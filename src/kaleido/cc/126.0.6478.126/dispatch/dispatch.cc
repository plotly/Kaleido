
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
  }

  void Dispatch::CreateTab(int id, const GURL &url) {
  /*
      browser_->BrowserMainThread()->PostTask(
          FROM_HERE,
          base::BindOnce(&Dispatch::CreateTab, base::Unretained(dispatch), *id, GURL(std::string("file://") + tmpFileName)));
  */
    headless::HeadlessWebContents::Builder builder(
      parent_->browser_->GetDefaultBrowserContext()->CreateWebContentsBuilder());
    web_contents = builder.SetInitialURL(url).Build();

    auto tab = std::make_unique<SimpleDevToolsProtocolClient>();
    tab->AttachToWebContents(headless::HeadlessWebContentsImpl::From(web_contents)->web_contents());

    // Commands to the browser
    // Memory management to the job line
    /*
    LOG(INFO) << "Attached to web contents";
    tab->AddEventHandler("Page.loadEventFired", base::BindRepeating(&Dispatch::dumpEvent, base::Unretained(this)));
    tab->SendCommand("Page.enable", base::BindOnce(&Dispatch::dumpResponse, base::Unretained(this)));
    LOG(INFO) << "Enabled page";
    */
    job_line->PostTask(
        FROM_HERE,
        base::BindOnce(&Dispatch::sortTab, base::Unretained(this), id, std::move(tab)));

  }

  void Dispatch::sortTab(int id, std::unique_ptr<SimpleDevToolsProtocolClient> tab) {
    if (jobs.size() == 0) {
      tabs.push(std::move(tab));
    } else {
      // adjust the jobs queue and get it started
    }
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
