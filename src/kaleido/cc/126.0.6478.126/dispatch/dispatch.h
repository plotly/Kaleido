#ifndef DISPATCH_H_
#define DISPATCH_H_

#include <queue>

#include "components/devtools/simple_devtools_protocol_client/simple_devtools_protocol_client.h"

#include "base/task/sequenced_task_runner.h"
#include "headless/app/kaleido.h"

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
      ~Dispatch() = delete;

      Dispatch(const Dispatch&) = delete;
      Dispatch& operator=(const Dispatch&) = delete;
      void CreateTab(int id, const GURL &url);

      void Release() { browser_devtools_client_.DetachClient(); } // subclients go with it


    private:
      raw_ptr<Kaleido> parent_;
      // a devtools client for the _whole_ browser process (not a tab)
      SimpleDevToolsProtocolClient browser_devtools_client_;

      base::raw_ptr<headless::HeadlessWebContents> web_contents;
      // Represent connections to a tab
      std::queue<std::unique_ptr<SimpleDevToolsProtocolClient>> tabs;
      std::queue<std::string> jobs;

      // All queue operations happen on a SequencedTaskRunner for memory safety
      // Note: no callbacks allowed from within the SequencedTaskRunner
      scoped_refptr<base::SequencedTaskRunner> job_line;

      void sortTab(int id, std::unique_ptr<SimpleDevToolsProtocolClient> tab);
      void dumpEvent(const base::Value::Dict& msg);
      void dumpResponse(base::Value::Dict msg);
  };
}

#endif  // DISPATCH_H_
