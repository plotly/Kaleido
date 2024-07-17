// kaleido.cc:
//  goals:
//    * start up the browser
//    * start up the tab manager
//    * start up the IO thread

#include "headless/app/kaleido.h"

#include "headless/lib/browser/headless_browser_impl.h"
#include "headless/public/headless_browser.h"
#include "base/functional/bind.h"

namespace kaleido {

void Kaleido::OnBrowserStart(headless::HeadlessBrowser* browser) {
  browser_ = browser;
  ShutdownSoon();
}

void Kaleido::ShutdownSoon() {
  browser_->BrowserMainThread()->PostTask(
      FROM_HERE,
      base::BindOnce(&Kaleido::Shutdown, base::Unretained(this)));
}

void Kaleido::Shutdown() {
  browser_.ExtractAsDangling()->Shutdown();
}



} // namespace kaleido

