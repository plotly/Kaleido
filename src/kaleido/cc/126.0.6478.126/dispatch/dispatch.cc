
#include "base/logging.h"
#include "base/functional/bind.h"
#include "headless/app/dispatch/dispatch.h"

// Callbacks and threads
#include "base/functional/bind.h"
#include "base/task/thread_pool.h"
#include "base/task/bind_post_task.h"
// We can do the same thing with a WebContentsBuilder to create a tab, but maybe we can do it directly with dev tools?

namespace kaleido {

  Dispatch::Dispatch() {
    browser_devtools_client_.AttachToBrowser();
    job_line = base::ThreadPool::CreateSequencedTaskRunner({base::TaskPriority::USER_VISIBLE});
  }
  Dispatch::~Dispatch() = default;

  void Dispatch::createTab1_createTarget(const std::string &url) {
    LOG(INFO) << "Creating target.";
    base::Value::Dict params;
    params.Set("url", url);
    auto cb = base::BindOnce(&Dispatch::createTab2_attachTarget, base::Unretained(this));
    browser_devtools_client_.SendCommand("Target.createTarget",
        std::move(params),
        std::move(cb));
    // Note: You may think "good place for BindRepeating, we can reuse that instead of calling BindOnce everytime!"
    // Yes, but the time saved at runtime is trivial and negative^2 impact on readability.

  }
  void Dispatch::createTab2_attachTarget(base::Value::Dict result) {
    LOG(INFO) << "Reading Target.createTarget response";
    std::string *targetId = result.FindString("targetId");
    if (targetId) {
      LOG(INFO) << "Created target.";
    } else {
      if (result.FindString("error")) {
        LOG(INFO) << "Found error";
      }
      LOG(INFO) << "Failed to create target.";
    }
  }

  void Dispatch::createTab3_storeSession(base::Value::Dict result) {
    // get targetid and attach
  }

  // createTarget
  // attachToTarget
}
