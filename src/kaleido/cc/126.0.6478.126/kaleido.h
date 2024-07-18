#ifndef KALEIDO_H_
#define KALEIDO_H_

// Browser Includes
#include "headless/lib/browser/headless_browser_impl.h"
#include "headless/public/headless_browser.h"

#include <atomic>
namespace kaleido {

  // Kaleido manages several threads, basically.
  // a) it starts a thread for standard out, so all calls are guarenteed to be ordered
  class Kaleido {
    public:
      Kaleido();

      Kaleido(const Kaleido&) = delete;
      Kaleido& operator=(const Kaleido&) = delete;

      ~Kaleido() = default;

      void OnBrowserStart(headless::HeadlessBrowser* browser); // this is basically a "main" function
      // it's called when chromium is done with all its init stuff

  private:

    void PostListen(); // read stdin on a task
    std::atomic_flag listening = ATOMIC_FLAG_INIT;
    void PostEcho(const std::string&); // echo something out
    void ReadJSON(std::string&); // try to turn message into json object
    void ShutdownSoon(); // shut down browser (it will post it as a task)
    void Shutdown(); // shut down

    // a browser
    raw_ptr<headless::HeadlessBrowser> browser_ = nullptr;

    // a thread, essentially, for output
    scoped_refptr<base::SequencedTaskRunner> output_sequence();

    // a devtools client for the _whole_ browser process (not a tab)
    simple_dev_tools_protocol_client::SimpleDevToolsProtocolClient browser_devtools_client_;
  };
}
#endif  // KALEIDO_H_
