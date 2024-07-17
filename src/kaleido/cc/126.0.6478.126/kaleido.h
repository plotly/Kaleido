#ifndef KALEIDO_H_
#define KALEIDO_H_

// Fundamental chromium includes
#include "content/public/app/content_main.h"
#include "headless/public/headless_browser.h"

namespace kaleido {
  class Kaleido {
	  public:
      Kaleido(content::ContentMainParams);
	    Kaleido(const Kaleido&) = delete;
	    Kaleido& operator=(const Kaleido&) = delete;
	    ~Kaleido() = default;

      void OnBrowserStart(headless::HeadlessBrowser* browser);
    private:
      void ShutdownSoon();
      void Shutdown();
      raw_ptr<headless::HeadlessBrowser> browser_ = nullptr;
  };
  void ChildProcess(content::ContentMainParams);
}


#endif  // KALEIDO_H_
