#ifndef DISPATCH_H_
#define DISPATCH_H_

#include <queue>

#include "components/devtools/simple_devtools_protocol_client/simple_devtools_protocol_client.h"

#include "base/task/sequenced_task_runner.h"

namespace kaleido {
  class Kaleido;
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
  // Ergo, patterns like createTab1_desc(), createTab2_desc() clarify the concepts,
  // the process started by a CreateTab() public call.
  // 
  class Dispatch {
    public:
      Dispatch(raw_ptr<Kaleido> parent_);
      ~Dispatch();

      Dispatch(const Dispatch&) = delete;
      Dispatch& operator=(const Dispatch&) = delete;
      inline void CreateTab(int id, const std::string &url = "") { createTab1_createTarget(id, url); }


    private:
      raw_ptr<Kaleido> parent_;
      // a devtools client for the _whole_ browser process (not a tab)
      SimpleDevToolsProtocolClient browser_devtools_client_;

      // Represent connections to a tab
      std::queue<std::unique_ptr<SimpleDevToolsProtocolClient>> tabs;

      // All queue operations happen on a SequencedTaskRunner for memory safety
      // Note: no callbacks allowed from within the SequencedTaskRunner
      scoped_refptr<base::SequencedTaskRunner> job_line;

      void createTab1_createTarget(int id, const std::string &url);
      void createTab2_attachTarget(int id, base::Value::Dict);
      void createTab3_startSession(int id, base::Value::Dict);
      void createTab4_storeSession(int id, std::unique_ptr<SimpleDevToolsProtocolClient>); // This is a task
  };
}

#endif  // DISPATCH_H_

  // [x] Create Tab (needs to check for jobs)
  // [x] Link JSON to shutdown
  // [x] Link JSON to create tab
  // [ ] How to handles errors in callback chain to user
  // [ ] Get Status
  // [ ] Link JSON to Status
  // [ ] Queue Job (needs to check for jobs)
  // [ ] Check for jobs
  // [ ] Handle better the signals (besides don't use stdin)




