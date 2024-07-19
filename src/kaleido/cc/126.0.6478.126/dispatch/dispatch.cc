
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

  void Dispatch::createTab() {
    //
  }
}
