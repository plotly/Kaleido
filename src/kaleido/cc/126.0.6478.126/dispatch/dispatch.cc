
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
    headless::HeadlessWebContents::Builder builder(
      parent_->browser_->GetDefaultBrowserContext()->CreateWebContentsBuilder());
    web_contents = builder.SetInitialURL(url).Build();

    auto tab = std::make_unique<SimpleDevToolsProtocolClient>();
    tab->AttachToWebContents(headless::HeadlessWebContentsImpl::From(web_contents)->web_contents());

    job_line->PostTask(
        FROM_HERE,
        base::BindOnce(&Dispatch::sortTab, base::Unretained(this), id, std::move(tab)));

  }

  void Dispatch::sortTab(int id, std::unique_ptr<SimpleDevToolsProtocolClient> tab) {
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

  void Dispatch::dispatchJob(std::unique_ptr<Job> job, tab_t tab) {
    int job_id = job_number++;
    parent_->browser_->BrowserMainThread()->PostTask(
      FROM_HERE,
      base::BindOnce(&Dispatch::runJob1_resetTab, base::Unretained(this), std::move(job), std::move(tab), job_id));
    return;
  }

  // Pure call back structure --> central manager structure TODO
  // Memory TODO
  // WebContents TODO
  // Reunify output

  void Dispatch::runJob1_resetTab(std::unique_ptr<Job> job, tab_t tab, const int &job_id) {
    tab->SendCommand("Page.enable", base::BindOnce(&Dispatch::runJob2_reloadTab, base::Unretained(this), std::move(job), std::move(tab), job_id));
  }

  void Dispatch::runJob2_reloadTab(std::unique_ptr<Job> job, tab_t tab, const int &job_id, base::Value::Dict msg) {
    LOG(INFO) << "CAUGHT ENABLE";
    LOG(INFO) << msg.DebugString();
    /*auto cb = base::BindRepeating(&Dispatch::runJob3_configureTab, base::Unretained(this), std::move(job), std::move(tab), job_id);
    job_events[job_id] = cb.get();
    tab->AddEventHandler("Page.loadEventFired", std::move(cb));
    tab->SendCommand("Page.reload");*/
  }

  void Dispatch::runJob3_configureTab(std::unique_ptr<Job> job, tab_t tab, const int &job_id, const base::Value::Dict& msg) {
    LOG(INFO) << "CAUGHT PAGE RELOAD";/*
    tab->RemoveEventHandler("Page.loadEventFired", *job_events[job_id]);
    job_events.erase(job_id);*/
    // Theoretically, we've reloaded the page, and we're good to go. Theoretically.
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
