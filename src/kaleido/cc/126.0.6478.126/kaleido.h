#ifndef KALEIDO_H_
#define KALEIDO_H_

#include <unordered_map>
#include <atomic>
#include "third_party/abseil-cpp/absl/types/optional.h"

// Browser Includes
#include "headless/lib/browser/headless_browser_impl.h"
#include "headless/public/headless_browser.h"

#include "base/task/sequenced_task_runner.h"
#include "headless/app/dispatch/dispatch.h"

#include "base/task/thread_pool.h"

namespace kaleido {
    namespace scopes {
        class BaseScope;
    }
  class Dispatch;
  // Kaleido is our app, basically.
  // Should be singleton, but non-trivial work
  // SIGINT and SIGTERM would be nice
  // TODO: For now, they can catch and write a message to shutdown to its own stdin
  class Kaleido {
    public:
      Kaleido();
      ~Kaleido() = delete;

      Kaleido(const Kaleido&) = delete;
      Kaleido& operator=(const Kaleido&) = delete;

      // make more private?
      std::vector<std::string> localScriptFiles;
      base::FilePath cwd;
      base::raw_ptr<scopes::BaseScope> scope_ptr;

      // This is basically a singleton. Could we pass the constructor instead of on browser start?
      void OnBrowserStart(headless::HeadlessBrowser* browser);

      // Dispatch uses this to let us know how things went
      void PostEchoTaskOld(const std::string&);
      void ReportOperation(int id, bool success, const base::Value::Dict &msg);
      void ReportSuccess(int id);
      void ReportFailure(int id, const std::string& msg);
      void Api_OldMsg(int code, std::string message);
      // JSON Helper functions for creating common messages to user
      void Api_ErrorInvalidJSON();
      void Api_ErrorMissingBasicFields(absl::optional<int>);
      void Api_ErrorDuplicateId(int);
      void Api_ErrorNegativeId(int);
      void Api_ErrorUnknownOperation(int id, const std::string& op);

      // a browser, global basically,
      // this is needed for anything that does anything on thread control
      raw_ptr<headless::HeadlessBrowser> browser_;
      std::string scope_name;
      base::Value::List scope_args;
      void ShutdownSoon();
      bool old = false;

  private:

    // User IO stuff for main
    void StartListen(); // continually reads stdin on parallel task
    void listenTask();
    void postListenTask();
    std::atomic_flag listening = ATOMIC_FLAG_INIT; // to only call postListenTask() once
    void PostEchoTask(const std::string&); // echo something out

    std::unordered_map<int, const std::string&> messageIds; // every message must have a unique id
    bool ReadJSON(std::string&); // try to turn message into json object

    // a thread, for making sure output is orderer and messages aren't mixed
    scoped_refptr<base::SequencedTaskRunner> output_sequence;

    // our tab dispatch, our actual browser controller
    raw_ptr<Dispatch> dispatch;


    void ShutdownTask();

    // FROM PREVIOUS STRUCTURE
    std::string tmpFileName;
  };
}


#endif  // KALEIDO_H_

