#ifndef KALEIDO_H_
#define KALEIDO_H_

// Browser Includes
#include "headless/lib/browser/headless_browser_impl.h"
#include "headless/public/headless_browser.h"

namespace kaleido {
  int KaleidoMain(int argc, const char** argv);
  // Kaleido manages a browser and its tabs
  class Kaleido {
   public:
    Kaleido();

    Kaleido(const Kaleido&) = delete;
    Kaleido& operator=(const Kaleido&) = delete;

    ~Kaleido() = default;

    void OnBrowserStart(headless::HeadlessBrowser* browser);

   private:
    void ShutdownSoon(); // shut down browser (it will post it as a task)
    void Shutdown(); // shut down
    void Listen(); // read stdin
    void PostListen(); // post Listen as a task
    void PostEcho(const std::string&); // echo something out
    void ReadJSON(std::string&); // try to turn message into json object

    raw_ptr<headless::HeadlessBrowser> browser_ = nullptr;
    scoped_refptr<SequencedTaskRunner> output_sequence();
  };
}
#endif  // KALEIDO_H_
