// kaleido.cc:
//  goals:
//    * start up the browser
//    * start up the tab manager
//    * start up the IO thread

#include "headless/app/kaleido.h"

#include "headless/lib/browser/headless_browser_impl.h"
#include "headless/public/headless_browser.h"
#include "base/functional/bind.h"

#include "base/logging.h"
#include "base/task/thread_pool.h"

#include "third_party/abseil-cpp/absl/types/optional.h"
#include <iostream>
#include "base/json/json_reader.h"

namespace kaleido {

void Kaleido::Kaleido() {
  output_sequence = base::ThreadPool::CreateSequencedTaskRunner(); 
}
void Kaleido::OnBrowserStart(headless::HeadlessBrowser* browser) {
  browser_ = browser;
  // now we have a browser, lets start a sequence of echoing!#
  PostListen();
  //ShutdownSoon();
}


void Kaleido::Listen() {
  std::string in;
  if (!std::getline(std::cin, in).good()) {
    std::string eof = std::cin.eof() ? "EOF" : "";
    std::string bad = std::cin.eof() ? "BAD" : "GOOD";
    std::string fail = std::cin.eof() ? "FAIL" : "SUCCESS";
    LOG(INFO) << eof << "|" << bad << "|" << fail << "|" << in;
    // TODO: post end to controller, we're shutting down, just let it go....
    return;
  }
  ReadJSON(in);
  PostListen();
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
		PostEcho("No operation");
	}
}

void Kaleido::PostEcho(const std::string &msg) {
  auto echo = [](const std::string &msg){ std::cout << msg << std::endl; }
  output_sequence->PostTask(FROM_HERE, base::BindOnce(echo, msg))
}
void Kaleido::PostListen() { 
  base::ThreadPool::PostTask(
                      FROM_HERE, {base::TaskPriority::BEST_EFFORT, base::MayBlock()},
                          base::BindOnce(&Kaleido::Listen, base::Unretained(this)));
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

