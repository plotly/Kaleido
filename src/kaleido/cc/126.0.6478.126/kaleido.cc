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

void Kaleido::OnBrowserStart(headless::HeadlessBrowser* browser) {
  browser_ = browser; // Global by another name

  // Actual constructor duties, init stuff
  output_sequence = base::ThreadPool::CreateSequencedTaskRunner(
      {base::TaskPriority::USER_VISIBLE}
    ); // Can't do this before OnBrowserStart!

  dispatch = std::make_unique<Dispatch>(); // Tab manager

  // Create browser context and set it as the default. The default browser
  // context is used by the Target.createTarget() DevTools command when no other
  // context is given.
  headless::HeadlessBrowserContext::Builder context_builder =
      browser_->CreateBrowserContextBuilder();
  headless::HeadlessBrowserContext* browser_context = context_builder.Build();
  browser_->SetDefaultBrowserContext(browser_context);

  // Run
  dispatch->CreateTab();
  PostListen();
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
    LOG(WARNING) << "Recieved invalid JSON from client connected to Kaleido:";
    LOG(WARNING) << json.DumpString();
    Api_ErrorInvalidJSON();
    return;
  }
  base::Value::Dict &jsonDict = json->GetDict();
  std::string *id = jsonDict.FindInt("id");
  std::string *operation = jsonDict.FindString("operation");
  if !(operation && id) {
    Api_ErrorMissingBasicFields();
    return;
  }
  if  (!messageIds.insert(*id).second) {
    Api_ErrorDuplicateId();
    return;
  }
}

void Kaleido::Api_ErrorInvalidJSON() {
  Kaleido::PostEcho(R"({"error":"malformed JSON string"})");
}

void Kaleido::Api_ErrorMissingBasicFields() {
  Kaleido::PostEcho(R"({"error":"all messages must contain an 'id' integer and an 'operation' string"})");
}

void Kaleido::Api_ErrorDepulicateId() {
  Kaleido::PostEcho(R"({"error":"all messages must contain a unique 'id' integer for the entire session."})");
}

} // namespace kaleido

