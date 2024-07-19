
#include "base/logging.h"
#include "base/functional/bind.h"
#include "headless/app/dispatch/dispatch.h"

// Callbacks and threads
#include "base/functional/bind.h"
#include "base/task/thread_pool.h"
// We can do the same thing with a WebContentsBuilder to create a tab, but maybe we can do it directly with dev tools?

namespace kaleido {

  Dispatch::Dispatch() {
    browser_devtools_client_.AttachToBrowser();
    job_line = base::ThreadPool::CreateSequencedTaskRunner({base::TaskPriority::USER_VISIBLE});
  }
  Dispatch::~Dispatch() = default;

  void Dispatch::createTab1(const std::string &url) {
      base::Value::Dict params;
      params.Set("url", url);
      browser_devtools_client_.SendCommand("Target.createTarget",
          std::move(params),
          base::BindOnce(&Dispatch::createTab2, base::Unretained(this)));
      // Note: You may think "good place for BindRepeating, we can reuse that instead of calling BindOnce everytime!"
      // Yes, but the time saved at runtime is trivial and negative^2 impact on readability.

      //new unique_ptr to simpleDevtoolsClient  browser_devtools_client_.CreateSession(sId);
  }
  void Dispatch::createTab2(base::Value::Dict result) {

  }
}
