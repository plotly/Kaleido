
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
    web_contents_->Close();
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

  void Dispatch::sortTab(int id, std::unique_ptr<Tab> tab) {
    if (jobs.size() == 0) {
      tabs.push(std::move(tab));
    } else {
      dispatchJob(std::move(jobs.front()), std::move(tab));
      jobs.pop();
    }
  }
  void Dispatch::sortJob(std::unique_ptr<Job> job) {
    if (tabs.size() == 0) {
      jobs.push(std::move(job));
    } else {
      dispatchJob(std::move(job), std::move(tabs.front()));
      tabs.pop();
    }
  }

  // Memory TODO

  void Dispatch::dispatchJob(std::unique_ptr<Job> job, std::unique_ptr<Tab> tab) {
    int job_id = job_number++;
    job->currentTab = std::move(tab);
    activeJobs[job_id] = std::move(job);
    // it would be better to create them and destroy them on the browser task, who is accessing them
    // that way we can also destroy them on the browser task
    // before shut down
    // we can also check to see if the activeJobs queue is donefor
    // TODO
    parent_->browser_->BrowserMainThread()->PostTask(
      FROM_HERE,
      base::BindOnce(&Dispatch::runJob1_resetTab, base::Unretained(this), job_id));
    return;
  }

  void Dispatch::runJob1_resetTab(const int &job_id) {
    activeJobs[job_id]->currentTab->client_->SendCommand("Page.enable");
    activeJobs[job_id]->currentTab->client_->SendCommand("Runtime.enable", base::BindOnce(&Dispatch::runJob2_reloadTab, base::Unretained(this), job_id));
  }

  void Dispatch::runJob2_reloadTab(const int &job_id, base::Value::Dict msg) {
    auto cb = base::BindRepeating(&Dispatch::runJob3_loadScripts, base::Unretained(this), job_id);
    activeJobs[job_id]->runtimeEnableCb = cb;
    activeJobs[job_id]->currentTab->client_->AddEventHandler("Runtime.executionContextCreated", cb);
    activeJobs[job_id]->currentTab->client_->SendCommand("Page.reload");
  }

  void Dispatch::runJob3_loadScripts(const int &job_id, const base::Value::Dict& msg) {
    LOG(INFO) << "Runtime enable";
    activeJobs[job_id]->currentTab->client_->RemoveEventHandler(
        "Runtime.executionContextCreated", std::move(activeJobs[job_id]->runtimeEnableCb));
    activeJobs[job_id]->scriptItr = parent_->localScriptFiles.begin();

    base::Value::Dict empty;
    runJob4_loadNextScript(job_id, std::move(empty));

  }

  void Dispatch::runJob4_loadNextScript(const int &job_id, const base::Value::Dict msg) {

    if (activeJobs[job_id]->scriptItr == parent_->localScriptFiles.end()) {
      // now we export next?
      return;
    }
    std::string scriptPath(*activeJobs[job_id]->scriptItr);
    std::ifstream script(scriptPath);
    if (!script.is_open()) {
      LOG(ERROR) << "Failed to find, or open, local file at "
        << scriptPath << " with working directory " << parent_->cwd.value() << std::endl;
      parent_->ShutdownSoon();
      return;
    }
    std::string scriptString((std::istreambuf_iterator<char>(script)),
        std::istreambuf_iterator<char>(script));

    auto after_loaded = base::BindRepeating(
        &Dispatch::runJob5_runLoadedScript, base::Unretained(this), job_id);

    base::Value::Dict script_params;
    script_params.Set("expression", scriptString);
    script_params.Set("sourceURL", scriptPath);
    script_params.Set("persistScript", true);

    activeJobs[job_id]->currentTab->client_->SendCommand("Runtime.compileScript", std::move(script_params), after_loaded);
  }

  void Dispatch::runJob5_runLoadedScript(const int job_id, const base::Value::Dict msg) {
    activeJobs[job_id]->scriptItr++;

    auto after_run = base::BindRepeating(
        &Dispatch::runJob4_loadNextScript, base::Unretained(this), job_id);

    base::Value::Dict script_params;
    std::string scriptId = *msg.FindDict("result")->FindString("scriptId");
    script_params.Set("scriptId", scriptId);
    activeJobs[job_id]->currentTab->client_->SendCommand("Runtime.runScript", std::move(script_params), after_run);
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
