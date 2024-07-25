#include <fstream>

#include "base/logging.h"
#include "base/functional/bind.h"
#include "headless/app/dispatch/dispatch.h"

#include "headless/lib/browser/headless_browser_impl.h"
#include "headless/lib/browser/headless_web_contents_impl.h"

// Callbacks and threads
#include "base/functional/bind.h"
#include "base/task/thread_pool.h"
#include "base/task/bind_post_task.h"
// We can do the same thing with a WebContentsBuilder to create a tab, but maybe we can do it directly with dev tools?
namespace kaleido {
  Tab::Tab() {}
  Tab::~Tab() {
    // TODO calling this destructor on shutdown would be V good, otherwise we complain
    client_->DetachClient();
    web_contents_.ExtractAsDangling()->Close();
  }
  Job::Job() {}
  Job::~Job() {
    if (currentTab) currentTab.reset();
  }


  Dispatch::Dispatch(raw_ptr<Kaleido> parent_): parent_(parent_) {
    browser_devtools_client_.AttachToBrowser();
    job_line = base::ThreadPool::CreateSequencedTaskRunner({
        base::TaskPriority::BEST_EFFORT,
        base::TaskShutdownBehavior::SKIP_ON_SHUTDOWN});
    env = base::Environment::Create();
    popplerAvailable = base::ExecutableExistsInPath(env.get(), "pdftops");
    inkscapeAvailable = base::ExecutableExistsInPath(env.get(), "inkscape");
  }

  void Dispatch::CreateTab(int id, const GURL &url) {
    auto tab = std::make_unique<Tab>();
    headless::HeadlessWebContents::Builder builder(
      parent_->browser_->GetDefaultBrowserContext()->CreateWebContentsBuilder());
    tab->web_contents_ = builder.SetInitialURL(url).Build();

    tab->client_ = std::make_unique<SimpleDevToolsProtocolClient>();
    // DevToolsTargetReady TODO
    tab->client_->AttachToWebContents(headless::HeadlessWebContentsImpl::From(tab->web_contents_)->web_contents());

    job_line->PostTask(
        FROM_HERE,
        base::BindOnce(&Dispatch::sortTab, base::Unretained(this), id, std::move(tab)));

  }

  void Dispatch::ReloadAll() {
    parent_->browser_->BrowserMainThread()->PostTask(
      FROM_HERE,
      base::BindOnce(&Dispatch::reloadAll, base::Unretained(this)));
  }
  void Dispatch::reloadAll() {
    for (auto& it: activeJobs) {
      activeJobs[it.first]->currentTab->client_->SendCommand("Page.reload");
    }
  }

  // jobLine modifying tabs and jobs
  void Dispatch::sortTab(int id, std::unique_ptr<Tab> tab) {
    if (jobs.size() == 0) {
      tabs.push(std::move(tab));
    } else {
      dispatchJob(std::move(jobs.front()), std::move(tab));
      jobs.pop();
    }
  }

  // jobLine modifying tabs and jobs
  void Dispatch::sortJob(std::unique_ptr<Job> job) {
    if (tabs.size() == 0) {
      jobs.push(std::move(job));
    } else {
      dispatchJob(std::move(job), std::move(tabs.front()));
      tabs.pop();
    }
  }

  // jobline modying tabs and jobs and aciveJobs
  void Dispatch::dispatchJob(std::unique_ptr<Job> job, std::unique_ptr<Tab> tab) {
    int job_id = job_number++;

    job->currentTab = std::move(tab);
    activeJobs[job_id] = std::move(job);
    parent_->browser_->BrowserMainThread()->PostTask(
      FROM_HERE,
      base::BindOnce(&Dispatch::runJob1_resetTab, base::Unretained(this), job_id)); // jobline gives browser control of tab/job
    return;
  }

  inline bool Dispatch::checkError(const base::Value::Dict &msg, const std::string &context, const int& job_id) {
    if (msg.FindString("error")) {
        std::string error = base::StringPrintf(
                "%s: Response: %s", context.c_str(), msg.DebugString().c_str());
        if (parent_->old) parent_->Api_OldMsg(1, error);
        else parent_->ReportFailure(activeJobs[job_id]->id, error);
        job_line->PostTask(
            FROM_HERE,
            base::BindOnce(&Dispatch::closeJob, base::Unretained(this), job_id)); // we're done with this job_id
        return true;
    }
    return false;
  }

  void Dispatch::runJob1_resetTab(const int &job_id) {
    if (activeJobs.find(job_id) == activeJobs.end()) return;

    activeJobs[job_id]->currentTab->client_->SendCommand("Page.enable");
    activeJobs[job_id]->currentTab->client_->SendCommand("Runtime.enable", base::BindOnce(&Dispatch::runJob2_reloadTab, base::Unretained(this), job_id));
  }

  void Dispatch::runJob2_reloadTab(const int &job_id, base::Value::Dict msg) {
    if (activeJobs.find(job_id) == activeJobs.end() || checkError(msg, "runJob2_reloadTab", job_id)) return;
    auto cb = base::BindRepeating(&Dispatch::runJob3_loadScripts, base::Unretained(this), job_id);
    activeJobs[job_id]->runtimeEnableCb = cb;
    activeJobs[job_id]->currentTab->client_->AddEventHandler("Runtime.executionContextCreated", cb);
    activeJobs[job_id]->currentTab->client_->SendCommand("Page.reload");
  }

  void Dispatch::runJob3_loadScripts(const int &job_id, const base::Value::Dict& msg) {
    LOG(INFO) << "Runtime enable";
    activeJobs[job_id]->currentTab->client_->RemoveEventHandler(
        "Runtime.executionContextCreated", std::move(activeJobs[job_id]->runtimeEnableCb));
    if (activeJobs.find(job_id) == activeJobs.end() || checkError(msg, "runJob3_loadScripts", job_id)) return;
    activeJobs[job_id]->scriptItr = parent_->localScriptFiles.begin();
    activeJobs[job_id]->executionId = *msg.FindDict("params")->FindDict("context")->FindInt("id");
    base::Value::Dict empty;
    runJob4_loadNextScript(job_id, std::move(empty));
  }

  void Dispatch::runJob4_loadNextScript(const int &job_id, const base::Value::Dict msg) {
    if (activeJobs.find(job_id) == activeJobs.end() || checkError(msg, "runJob4_loadNextScript", job_id)) return;
    if (activeJobs[job_id]->scriptItr == parent_->localScriptFiles.end()) {
      std::string exportFunction = base::StringPrintf(
          "function(spec, ...args) { return kaleido_scopes.%s(spec, ...args).then(JSON.stringify); }",
          parent_->scope_name.c_str());

      base::Value::Dict spec;
      spec.Set("value", std::move(activeJobs[job_id]->spec_parsed));
      base::Value::List args = std::move(parent_->scope_args);
      args.Insert(args.begin(), base::Value(std::move(spec)));
      base::Value::Dict params;
      params.Set("functionDeclaration", exportFunction);
      params.Set("arguments", std::move(args));
      params.Set("returnByValue", false);
      params.Set("userGesture", true);
      params.Set("awaitPromise", true);
      params.Set("executionContextId", activeJobs[job_id]->executionId);
      activeJobs[job_id]->currentTab->client_->SendCommand("Runtime.callFunctionOn",
        std::move(params),
        base::BindOnce(&Dispatch::runJob6_processImage, base::Unretained(this), job_id));
      return;
    }
    std::string scriptPath(*activeJobs[job_id]->scriptItr);
    std::ifstream script(scriptPath);
    if (!script.is_open()) {
      std::string error = base::StringPrintf("Failed to find, or open, local file at %s with working directory %s",
          scriptPath.c_str(), parent_->cwd.value().c_str());
      LOG(ERROR) << error;
      parent_->Api_OldMsg(404, error);
      // TODO gotta kill job
      return;
    }
    std::string scriptString((std::istreambuf_iterator<char>(script)),
        std::istreambuf_iterator<char>());
    auto after_loaded = base::BindRepeating(
        &Dispatch::runJob5_runLoadedScript, base::Unretained(this), job_id);

    base::Value::Dict script_params;
    script_params.Set("expression", scriptString);
    script_params.Set("sourceURL", scriptPath);
    script_params.Set("persistScript", true);
    activeJobs[job_id]->currentTab->client_->SendCommand("Runtime.compileScript", std::move(script_params), after_loaded);
  }

  void Dispatch::runJob5_runLoadedScript(const int &job_id, const base::Value::Dict msg) {
    if (activeJobs.find(job_id) == activeJobs.end() || checkError(msg, "runJob5_runLoadedScript", job_id)) return;
    activeJobs[job_id]->scriptItr++;

    auto after_run = base::BindRepeating(
        &Dispatch::runJob4_loadNextScript, base::Unretained(this), job_id);

    base::Value::Dict script_params;
    std::string scriptId = *msg.FindDict("result")->FindString("scriptId");
    script_params.Set("scriptId", scriptId);
    activeJobs[job_id]->currentTab->client_->SendCommand("Runtime.runScript", std::move(script_params), after_run);
  }

  void Dispatch::runJob6_processImage(const int& job_id, base::Value::Dict msg) {
    if (activeJobs.find(job_id) == activeJobs.end() || checkError(msg, "runJob6_processImage", job_id)) return;
    std::string result = *msg.FindDict("result")->FindDict("result")->FindString("value");
    parent_->PostEchoTaskOld(result.c_str());
    job_line->PostTask(
        FROM_HERE,
        base::BindOnce(&Dispatch::closeJob, base::Unretained(this), job_id)); // we're done with this job_id
    return;
  }

  void Dispatch::closeJob(const int& job_id) { // browser is modifying activejobs/etc, it should be jobline
    int messageId = activeJobs[job_id]->id;
    if (activeJobs.find(job_id) == activeJobs.end()) return;
    auto oldTab = std::move(activeJobs[job_id]->currentTab);
    auto oldJob = std::move(activeJobs[job_id]);
    oldJob.reset();
    activeJobs.erase(job_id);
    sortTab(messageId, std::move(oldTab));
  }

  void Dispatch::PostJob(std::unique_ptr<Job> job) {
    if (job->format == "eps" && !popplerAvailable) {
        parent_->Api_OldMsg(
                530,
                "Exporting to EPS format requires the pdftops command "
                "which is provided by the poppler library. "
                "Please install poppler and make sure the pdftops command "
                "is available on the PATH");
        return;
    }

    // Validate inkscape installed if format is emf
    if (job->format == "emf" && !inkscapeAvailable) {
        parent_->Api_OldMsg(
                530,
                "Exporting to EMF format requires inkscape. "
                "Please install inkscape and make sure it is available on the PATH");
        return;
    }

    job_line->PostTask(
        FROM_HERE,
        base::BindOnce(&Dispatch::sortJob, base::Unretained(this), std::move(job)));
  }

  // event callback signature
  void Dispatch::dumpEvent(const base::Value::Dict& msg) {
    LOG(INFO) << msg.DebugString();
  }
  // command callback signature
  void Dispatch::dumpResponse(base::Value::Dict msg) {
    LOG(INFO) << msg.DebugString();
  }

}
