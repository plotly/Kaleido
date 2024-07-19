#ifndef KALEIDO_H_
#define KALEIDO_H_

#include <unordered_set>
#include <atomic>

// Browser Includes
#include "headless/lib/browser/headless_browser_impl.h"
#include "headless/public/headless_browser.h"

#include "base/task/sequenced_task_runner.h"
#include "headless/app/dispatch/dispatch.h"

namespace kaleido {

  // Kaleido is our app, basically.
  // Should be singleton, but non-trivial work
  // SIGINT and SIGTERM would be nice
  // TODO: For now, they can catch and write a message to shutdown to its own stdin
  class Kaleido {
    public:
      Kaleido() = default; // OnBrowserStart is the real constructor
      ~Kaleido() = default;

      Kaleido(const Kaleido&) = delete;
      Kaleido& operator=(const Kaleido&) = delete;

      void OnBrowserStart(headless::HeadlessBrowser* browser); // this is basically a "main" function
      // it's called when chromium is done with all its init stuff

  private:

    // a browser, global basically
    raw_ptr<headless::HeadlessBrowser> browser_;

    // User IO stuff for main
    void PostListen(); // continually reads stdin on parallel task
    void listenTask(); // see note in .cc, or ignore this
    std::atomic_flag listening = ATOMIC_FLAG_INIT; // to only call PostListen() once
    void PostEcho(const std::string&); // echo something out

    std::unordered_set<int> messageIds; // every message must have a unique id
    void ReadJSON(std::string&); // try to turn message into json object

    // a thread, for making sure output is orderer and messages aren't mixed
    scoped_refptr<base::SequencedTaskRunner> output_sequence;

    // our tab dispatch, our actual browser controller
    std::unique_ptr<Dispatch> dispatch = nullptr;

    // JSON Helper functions for creating common messages to user
    void Api_ErrorInvalidJSON();
    void Api_ErrorMissingBasicFields();
    void Api_ErrorDepulicateId();


    // Control Flow, declare here
    void ShutdownSoon() {
      browser_->BrowserMainThread()->PostTask(
          FROM_HERE,
          base::BindOnce(&Kaleido::ShutdownTask, base::Unretained(this)));
    }
    void ShutdownTask() {
      browser_.ExtractAsDangling()->Shutdown();
    }
  };
}
#endif  // KALEIDO_H_
