#ifndef DISPATCH_H_
#define DISPATCH_H_

#include <queue>

#include "components/devtools/simple_devtools_protocol_client/simple_devtools_protocol_client.h"

#include "base/task/sequenced_task_runner.h"

namespace kaleido {
  // probably should be a singleton
  class Dispatch {
    public:
      Dispatch();
      ~Dispatch();

      Dispatch(const Dispatch&) = delete;
      Dispatch& operator=(const Dispatch&) = delete;
      inline void CreateTab() { job_line->PostTask(FROM_HERE, base::BindOnce(&Dispatch::createTab, base::Unretained(this))); }

    private:
      // a devtools client for the _whole_ browser process (not a tab)
      simple_devtools_protocol_client::SimpleDevToolsProtocolClient browser_devtools_client_;
      scoped_refptr<base::SequencedTaskRunner> job_line;

      std::queue<void *> tabs;
      void createTab();
  };
}
  // What do we need to initialize with the browser? (look at python)
  // What does it manage for us?

  // We need to create at least one tab right away. SessionId MessageId?
  // We need to put that tab on the not busy Q
  // We can, if we want, run CheckForWork which looks for jobs and free tabs.
  // We have no concept of jobs and free tabs yet tho.
  // We probably at this point need to finish the rest of the build

#endif  // DISPATCH_H_
  // We need to some manual devtools client stuff just to see how stuff is different
  // --> Create Tab
  // --> Queue Job
  // --> Get Status
  /*
  TabDispatch {
    freeTabs
    busyTabs
    QueuedJobs (jobs should also be an object)
    Sequence
    AddTab
    AddJob
    */




