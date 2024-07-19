#ifndef KALEIDO_H_
#define KALEIDO_H_

#include <atomic>
// Browser Includes
#include "headless/lib/browser/headless_browser_impl.h"
#include "headless/public/headless_browser.h"

#include "base/task/sequenced_task_runner.h"
#include "headless/app/dispatch/dispatch.h"

namespace kaleido {

  // Kaleido manages several threads, basically.
  // a) it starts a thread for standard out, so all calls are guarenteed to be ordered
  // probably should be a singleton, non-trivial work, would allows catching SIGINT and SIGTERM
  // could also do global browser..
  class Kaleido {
    public:
      Kaleido();
      ~Kaleido();

      Kaleido(const Kaleido&) = delete;
      Kaleido& operator=(const Kaleido&) = delete;

      void OnBrowserStart(headless::HeadlessBrowser* browser); // this is basically a "main" function
      // it's called when chromium is done with all its init stuff

  private:

    void PostListen(); // read stdin on a task
    void listen(); // see note in .cc, or ignore this
    std::atomic_flag listening = ATOMIC_FLAG_INIT;
    void PostEcho(const std::string&); // echo something out
    void ReadJSON(std::string&); // try to turn message into json object
    void ShutdownSoon(); // shut down browser (it will post it as a task)
    void Shutdown(); // shut down

    // a browser
    raw_ptr<headless::HeadlessBrowser> browser_;

    // a thread, essentially, for output
    scoped_refptr<base::SequencedTaskRunner> output_sequence;

    // our tab dispatch, our actual browser controller
    std::unique_ptr<Dispatch> dispatch = nullptr;

  };
}
#endif  // KALEIDO_H_
