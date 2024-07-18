// kaleido.cc:
//  goals:
//    * start up the browser
//    * start up the tab manager
//    * start up the IO thread

#include "headless/app/kaleido.h"

// Browser stuff
#include "headless/lib/browser/headless_browser_impl.h"
#include "headless/public/headless_browser.h"
#include "headless/public/headless_browser_context.h"

// Derp
#include "base/logging.h"

// Callbacks and threads
#include "base/functional/bind.h"
#include "base/task/thread_pool.h"

// For JS
#include "third_party/abseil-cpp/absl/types/optional.h"
#include <iostream>
#include "base/json/json_reader.h"


namespace kaleido {

// Constructor will initialize our threads
Kaleido::Kaleido() {
  output_sequence = base::ThreadPool::CreateSequencedTaskRunner({base::TaskPriority::USER_VISIBLE});
}
inline Kaleido::~Kaleido() = default; // style guide wont let me do it in .h

void Kaleido::OnBrowserStart(headless::HeadlessBrowser* browser) {
  browser_ = browser;

  headless::HeadlessBrowserContext::Builder context_builder =
      browser_->CreateBrowserContextBuilder();

  // Create browser context and set it as the default. The default browser
  // context is used by the Target.createTarget() DevTools command when no other
  // context is given. -- from original example
  headless::HeadlessBrowserContext* browser_context = context_builder.Build();
  browser_->SetDefaultBrowserContext(browser_context);

  // We can do the same thing with a WebContentsBuilder to create a tab, but maybe we can do it directly with dev tools?
  browser_devtools_client_.AttachToBrowser();
  // Okay, lets get the ID browser_devtools_client_.GetTargetId()
  // Target.createTarget
  // Target.getTargets
  // event Target.targetCreated
  // Target.closeTarget
  // Target.attachToTarget
  // Lets try to open a new tab

  PostListen();
  //ShutdownSoon();
}

void Kaleido::PostListen() {
  if(listening.test_and_set(std::memory_order_relaxed)) return;
  auto listen = [](){
    std::string in;
    if (!std::getline(std::cin, in).good()) {
      LOG(INFO) << in << ": "
        << std::cin.eof() ? "EOF | " : ""
        << std::cin.eof() ? "BAD | " : "GOOD | "
        << std::cin.eof() ? "FAIL" : "SUCCESS";
      // TODO: post end to controller, we're shutting down, just let it go....
      return;
    };
    ReadJSON(in);
    PostListen();
  }
  base::ThreadPool::PostTask(
    FROM_HERE,
    {base::TaskPriority::BEST_EFFORT, base::MayBlock()},
    base::BindOnce(&listen)
  );
}

void Kaleido::PostEcho(const std::string &msg) {
  auto echo = [](const std::string &msg){ std::cout << msg << std::endl; };
  output_sequence->PostTask(FROM_HERE, base::BindOnce(echo, msg));
}


void Kaleido::ReadJSON(std::string &msg) {
  absl::optional<base::Value> json = base::JSONReader::Read(msg);
  if (!json.has_value()) {
    PostEcho("This wasn't valid JSON:\n  " + msg);
    return;
  }
  PostEcho("Thanks for the JSON:\n  " + msg);
  base::Value::Dict &jsonDict = json->GetDict();

  std::string *operation = jsonDict.FindString("operation");
  if (operation) {
    PostEcho("Found operation: " + *operation); // Are all these concates copies?
  } else {
    PostEcho("No operation.");
  }
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

