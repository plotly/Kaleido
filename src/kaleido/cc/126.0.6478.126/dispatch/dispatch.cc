
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
    headless::HeadlessWebContents::Builder builder(
      parent_->browser_->GetDefaultBrowserContext()->CreateWebContentsBuilder());
    web_contents = builder.SetInitialURL(url).Build();
    tab.AttachToWebContents(headless::HeadlessWebContentsImpl::From(web_contents)->web_contents());
    LOG(INFO) << "Attached to web contents";
    tab.AddEventHandler("Page.loadEventFired", base::BindRepeating(&Dispatch::dumpEvent, base::Unretained(this)));
    tab.SendCommand("Page.enable", base::BindOnce(&Dispatch::dumpResponse, base::Unretained(this)));
    LOG(INFO) << "Enabled page";

  }
  void Dispatch::dumpEvent(const base::Value::Dict& msg) {
    //parent_->ReportOperation(-999, true, msg);
    LOG(INFO) << msg.DebugString();
    // This is where we can look for jobs
    return;
  }
  void Dispatch::dumpResponse(base::Value::Dict msg) {
    LOG(INFO) << msg.DebugString();
  }
/*
  void Dispatch::createTab1_createTarget(int id, const std::string &url) {
    LOG(INFO) << "Sending createTarget message to :" << browser_devtools_client_.GetTargetId();
    base::Value::Dict params;
    params.Set("url", url);
    auto cb = base::BindOnce(&Dispatch::createTab2_attachTarget, base::Unretained(this), id);
    browser_devtools_client_.SendCommand("Target.createTarget",
        std::move(params),
        std::move(cb));
    // Note: You may think "good place for BindRepeating, we can reuse that instead of calling BindOnce everytime!"
    // Yes, but the time saved at runtime is trivial and negative^2 impact on readability.

  }
  void Dispatch::createTab2_attachTarget(int id, base::Value::Dict msg) {
    LOG(INFO) << "createTarget reply:";
    LOG(INFO) << msg.DebugString();
    LOG(INFO) << "Sending attach target message to :" << browser_devtools_client_.GetTargetId();
    base::Value::Dict *result = msg.FindDict("result");
    if (result) {
      std::string *tId = result->FindString("targetId");
      if (tId) {
        base::Value::Dict params;
        params.Set("flatten", true);
        params.Set("targetId", *tId);
        LOG(INFO) << "Asking to attach to: " << *tId;
        auto cb = base::BindOnce(&Dispatch::createTab3_startSession, base::Unretained(this), id);
        browser_devtools_client_.SendCommand("Target.attachToTarget",
            std::move(params),
            std::move(cb));
        return;
      }
    }
    LOG(ERROR) << "Failure to create target.";
  }

  void Dispatch::createTab3_startSession(int id, base::Value::Dict msg) {
    LOG(INFO) << "Attach reply: ";
    LOG(INFO) << msg.DebugString();
    LOG(INFO) << "Going to send page.enable";
    base::Value::Dict *result = msg.FindDict("result");
    if (result) {
      std::string *sId = result->FindString("sessionId");
      if (sId) {
        LOG(INFO) << "Target created.";
        auto tab = browser_devtools_client_.CreateSession(*sId);
        //LOG(INFO) << "Sending message to :" << tab->GetTargetId();
        //tab->AddEventHandler("Page.loadEventFired", base::BindRepeating(&Dispatch::dumpEvent, base::Unretained(this)));
        //LOG(INFO) << "Event Attached";
        auto cb = base::BindOnce(&Dispatch::createTab4_primeTab,
            base::Unretained(this),
            id,
            std::move(tab));
        tab->SendCommand("Page.enable", std::move(cb));
        return;
      }
    }
    LOG(ERROR) << "Failure to create target.";
  }

  void Dispatch::createTab4_primeTab(int id, const std::unique_ptr<SimpleDevToolsProtocolClient> tab, base::Value::Dict msg) {
    LOG(INFO) << msg.DebugString();
    //LOG(INFO) << "Sending message to :" << tab->GetTargetId();
    //LOG(INFO) << "Trying to enable page";
    //tab->SendCommand("Page.enable");
    //LOG(INFO) << "Trying to reload page";
    //tab->SendCommand("Page.reload");
    return;
  }

  void Dispatch::createTab4_storeSession(int id, std::unique_ptr<SimpleDevToolsProtocolClient> newTab) {
        job_line->PostTask(
          FROM_HERE,
          base::BindOnce(
            &Dispatch::createTab4_storeSession,
            base::Unretained(this),
            id,
            
          )
        );
    // We could run one command here to see if it is valid, it should be valid!
    // At some point we need to concern ourselves with failure paths.
    parent_->ReportSuccess(id);
    tabs.push(std::move(newTab));
  }
*/

}
