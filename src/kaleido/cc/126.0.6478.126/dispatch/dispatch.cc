
#include "base/logging.h"
#include "base/functional/bind.h"
#include "headless/app/dispatch/dispatch.h"

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

  void Dispatch::createTab1_createTarget(int id, const std::string &url) {
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
    base::Value::Dict *result = msg.FindDict("result");
    if (result) {
      std::string *tId = result->FindString("targetId");
      if (tId) {
        base::Value::Dict params;
        params.Set("flatten", true);
        params.Set("targetId", *tId);
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
    base::Value::Dict *result = msg.FindDict("result");
    if (result) {
      std::string *sId = result->FindString("sessionId");
      if (sId) {
        LOG(INFO) << "Target created.";
        job_line->PostTask(
          FROM_HERE,
          base::BindOnce(
            &Dispatch::createTab4_storeSession,
            base::Unretained(this),
            id,
            browser_devtools_client_.CreateSession(*sId)
          )
        );
        return;
      }
    }
    LOG(ERROR) << "Failure to create target.";
  }

  void Dispatch::createTab4_storeSession(int id, std::unique_ptr<SimpleDevToolsProtocolClient> newTab) {
    // We could run one command here to see if it is valid, it should be valid!
    // At some point we need to concern ourselves with failure paths.
    tabs.push(std::move(newTab));
    parent_->ReportSuccess(id);
  }


}
