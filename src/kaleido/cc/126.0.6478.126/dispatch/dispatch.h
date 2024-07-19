#ifndef DISPATCH_H_
#define DISPATCH_H_

#include <queue>

#include "components/devtools/simple_devtools_protocol_client/simple_devtools_protocol_client.h"

#include "base/task/sequenced_task_runner.h"

namespace kaleido {
  using namespace simple_devtools_protocol_client;
  // probably should be a singleton, could use static, make_unique, etc

  // Sadly, callback hell persists in google's chromium. 
  // DevTools is an asynchronous IPC messaging platform, their internal API uses callbacks,
  // not blockable coroutines- just callbacks without async/await to linearize
  // the architecture. So how do we make it easier to read? I can't use lambda functions because 
  // lambda functions + class methods don't mix w/ google's callback utilities.
  // A full state machine that manages callbacks as subroutines would 
  // be absurdly out of scope.
  //
  // Ergo, patterns like createTab1_description, createTab2_description clarify the concepts.
  // 
  class Dispatch {
    public:
      Dispatch();
      ~Dispatch();

      Dispatch(const Dispatch&) = delete;
      Dispatch& operator=(const Dispatch&) = delete;
      inline void CreateTab(const std::string &url = "") { createTab1_createTarget(url); }


    private:
      // a devtools client for the _whole_ browser process (not a tab)
      SimpleDevToolsProtocolClient browser_devtools_client_;
      scoped_refptr<base::SequencedTaskRunner> job_line;

      std::queue<std::unique_ptr<SimpleDevToolsProtocolClient>> tabs;
      void createTab1_createTarget(const std::string &url);
      void createTab2_attachTarget(base::Value::Dict);
      void createTab3_storeSession(base::Value::Dict);
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




