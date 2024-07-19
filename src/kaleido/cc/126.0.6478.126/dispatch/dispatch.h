#ifndef DISPATCH_H_
#define DISPATCH_H_

#include "components/devtools/simple_devtools_protocol_client/simple_devtools_protocol_client.h"

#include "base/task/sequenced_task_runner.h"

namespace kaleido {
  // probably should be a singleton
  class Dispatch {
    public:
      Dispatch();
      ~Dispatch() = default;

      Dispatch(const Dispatch&) = delete;
      Dispatch& operator=(const Dispatch&) = delete;

    private:
      // a devtools client for the _whole_ browser process (not a tab)
      simple_devtools_protocol_client::SimpleDevToolsProtocolClient browser_devtools_client_;
  };
}

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




