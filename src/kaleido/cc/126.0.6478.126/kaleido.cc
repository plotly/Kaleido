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

Kaleido::~Kaleido() {} // style guide wont let me do it in .h

void Kaleido::OnBrowserStart(headless::HeadlessBrowser* browser) {
  browser_ = browser;
  dispatch = std::make_unique<Dispatch>();
  headless::HeadlessBrowserContext::Builder context_builder =
      browser_->CreateBrowserContextBuilder();

  // Create browser context and set it as the default. The default browser
  // context is used by the Target.createTarget() DevTools command when no other
  // context is given. -- from original example
  headless::HeadlessBrowserContext* browser_context = context_builder.Build();
  browser_->SetDefaultBrowserContext(browser_context);

  PostListen();
  //ShutdownSoon();
}

// this is the task, we'd like it to be lambda
// chromium's bind only supports non-capture lambdas
// which wouldn't have access to `this`
void Kaleido::listen() {
  std::string in;
  if (!std::getline(std::cin, in).good()) {
    LOG(INFO) << in << ": "
      << (std::cin.eof() ? "EOF | " : "")
      << (std::cin.eof() ? "BAD | " : "GOOD | ")
      << (std::cin.eof() ? "FAIL" : "SUCCESS");
    // TODO: post end to controller, we're shutting down, just let it go....
    return;
  };
  ReadJSON(in);
  PostListen();
}

void Kaleido::PostListen() {
  if(listening.test_and_set(std::memory_order_relaxed)) return;
  base::ThreadPool::PostTask(
    FROM_HERE,
    {base::TaskPriority::BEST_EFFORT, base::MayBlock()},
    base::BindOnce(&Kaleido::listen, base::Unretained(this)));
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
  // Really no arbitrary strings to PostEcho TODO

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

