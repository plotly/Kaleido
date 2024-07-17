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
    Kaleido() = default;

    Kaleido(const Kaleido&) = delete;
    Kaleido& operator=(const Kaleido&) = delete;

    ~Kaleido() = default;

    void OnBrowserStart(headless::HeadlessBrowser* browser);

   private:
    void ShutdownSoon();
    void Shutdown();
    raw_ptr<headless::HeadlessBrowser> browser_ = nullptr;
  };
}
#endif  // KALEIDO_H_
