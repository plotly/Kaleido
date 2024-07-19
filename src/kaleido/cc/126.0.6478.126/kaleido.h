#ifndef KALEIDO_H_
#define KALEIDO_H_

#include <unordered_set>
#include <atomic>

// Browser Includes
#include "headless/lib/browser/headless_browser_impl.h"
#include "headless/public/headless_browser.h"

#include "base/task/sequenced_task_runner.h"
#include "headless/app/dispatch/dispatch.h"

#include "base/task/thread_pool.h"

namespace kaleido {

  // Kaleido is our app, basically.
  // Should be singleton, but non-trivial work
  // SIGINT and SIGTERM would be nice
  // TODO: For now, they can catch and write a message to shutdown to its own stdin
  class Kaleido {
    public:
      Kaleido();
      ~Kaleido();

      Kaleido(const Kaleido&) = delete;
      Kaleido& operator=(const Kaleido&) = delete;

      // This is basically a singleton. Could we pass the constructor instead of on browser start?
      void OnBrowserStart(headless::HeadlessBrowser* browser);


  private:

    // a browser, global basically
    raw_ptr<headless::HeadlessBrowser> browser_;

    // User IO stuff for main
    void StartListen(); // continually reads stdin on parallel task
    void listenTask();
    void postListenTask();
    std::atomic_flag listening = ATOMIC_FLAG_INIT; // to only call postListenTask() once
    void PostEchoTask(const std::string&); // echo something out

    std::unordered_set<int> messageIds; // every message must have a unique id
    bool ReadJSON(std::string&); // try to turn message into json object

    // a thread, for making sure output is orderer and messages aren't mixed
    scoped_refptr<base::SequencedTaskRunner> output_sequence;

    // our tab dispatch, our actual browser controller
    std::unique_ptr<Dispatch> dispatch = nullptr;

    // JSON Helper functions for creating common messages to user
    void Api_ErrorInvalidJSON();
    void Api_ErrorMissingBasicFields();
    void Api_ErrorDuplicateId();


    // Control Flow, declare here
    void ShutdownSoon() {
      browser_->BrowserMainThread()->PostTask(
          FROM_HERE,
          base::BindOnce(&Kaleido::ShutdownTask, base::Unretained(this)));
    }
    void ShutdownTask() {
      LOG(INFO) << "Calling shutdown on browser";
      dispatch.reset(); // Fine to destruct what we have here.
      browser_.ExtractAsDangling()->Shutdown();
    }
  };
}
#endif  // KALEIDO_H_
