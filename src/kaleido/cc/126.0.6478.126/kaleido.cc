// kaleido.cc:
//  goals:
//    * start up the browser
//    * start up the tab manager
//    * start up the IO thread

#include <signal.h>

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

Kaleido::Kaleido() = default; // Redefine here or else chromium complains.
Kaleido::~Kaleido() = default;

void Kaleido::OnBrowserStart(headless::HeadlessBrowser* browser) {
  browser_ = browser; // global by another name

  // Actual constructor duties, init stuff
  output_sequence = base::ThreadPool::CreateSequencedTaskRunner(
      {base::TaskPriority::BEST_EFFORT, base::TaskShutdownBehavior::SKIP_ON_SHUTDOWN}
    ); // Can't do this before OnBrowserStart!

  dispatch = std::make_unique<Dispatch>(); // Tab manager

  // Create browser context and set it as the default. The default browser
  // context is used by the Target.createTarget() DevTools command when no other
  // context is given.
  // This stuff has weird side effects and I'm not sure its necessary.
  headless::HeadlessBrowserContext::Builder context_builder = browser_->CreateBrowserContextBuilder();
  headless::HeadlessBrowserContext* browser_context = context_builder.Build();
  browser_->SetDefaultBrowserContext(browser_context);

  // Run
  dispatch->CreateTab(-1); // Negative numbers indicate our orders, + user orders
  StartListen();
}

// Wish this were a lambda (as in PostEcho) but would have no access to private vars
void Kaleido::listenTask() {
  std::string in;
  if (!std::getline(std::cin, in).good()) {
    LOG(WARNING) << in << ": "
      << (std::cin.eof() ? "EOF | " : "")
      << (std::cin.eof() ? "BAD | " : "GOOD | ")
      << (std::cin.eof() ? "FAIL" : "SUCCESS");
    // TODO: post end to controller, we're shutting down, just let it go....
    return;
  };
  if (ReadJSON(in)) postListenTask();
}

void Kaleido::postListenTask() {
  base::ThreadPool::PostTask(
    FROM_HERE, {
      base::TaskPriority::BEST_EFFORT,
      base::MayBlock(),
      base::TaskShutdownBehavior::SKIP_ON_SHUTDOWN},
    base::BindOnce(&Kaleido::listenTask, base::Unretained(this))
    );
}
void Kaleido::StartListen() {
  if(listening.test_and_set(std::memory_order_relaxed)) return;
  postListenTask();
}

void Kaleido::PostEchoTask(const std::string &msg) {
  auto echo = [](const std::string &msg){ std::cout << msg << std::endl; };
  output_sequence->PostTask(FROM_HERE, base::BindOnce(echo, msg));
}


bool Kaleido::ReadJSON(std::string &msg) {
  absl::optional<base::Value> json = base::JSONReader::Read(msg);
  if (!json) {
    LOG(WARNING) << "Recieved invalid JSON from client connected to Kaleido:";
    LOG(WARNING) << msg;
    Api_ErrorInvalidJSON();
    return true;
  }
  base::Value::Dict &jsonDict = json->GetDict();
  absl::optional<unsigned int> id = jsonDict.FindInt("id");
  std::string *operation = jsonDict.FindString("operation");
  // The only operation we handle here. We're shutting down.
  // Trust chromium to handle it all when the browser exits
  // Doesn't need id, no return
  if (operation && *operation == "shutdown") {
    ShutdownSoon();
    return false;
  }
  if (!operation || !id) {
    Api_ErrorMissingBasicFields();
    return true;
  }
  if (messageIds.find(*id) != messageIds.end()) {
    Api_ErrorDuplicateId();
    return true;
  }
  messageIds.emplace(*id, *operation);
  return true;

}

void Kaleido::Api_ErrorInvalidJSON() {
  Kaleido::PostEchoTask(R"({"error":"malformed JSON string"})");
}

void Kaleido::Api_ErrorMissingBasicFields() {
  Kaleido::PostEchoTask(R"({"error":"all messages must contain an 'id' integer and an 'operation' string"})");
}

void Kaleido::Api_ErrorDuplicateId() {
  Kaleido::PostEchoTask(R"({"error":"message using already-used 'id' integer"})");
}

} // namespace kaleido

