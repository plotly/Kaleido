// kaleido.cc:
//  goals:
//    * start up the browser
//    * start up the tab manager
//    * start up the IO thread

#include <signal.h>
#include <cstdio>
#include <string>


#include <stdlib.h>

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

#include "headless/app/scopes/Factory.h"
// For copy 1
#include "base/command_line.h"

/// COPY 2
#include "base/files/file_util.h"
#include "base/strings/stringprintf.h"
#include <iostream>
#include <fstream>

#define FILE_URI_PREFIX "file://"
#if BUILDFLAG(IS_WIN)
#define HTML L"html"
#else
#define HTML "html"
#endif


// COPY
//
// OMG
//

// Copyright 2016 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.
#include "headless/public/headless_shell.h"
#include <memory>
#include "base/base_switches.h"
#include "base/command_line.h"
#include "base/files/file_util.h"
#include "base/functional/bind.h"
#include "base/logging.h"
#include "base/task/thread_pool.h"
#include "base/version_info/version_info.h"
#include "build/branding_buildflags.h"
#include "build/build_config.h"
#include "content/public/app/content_main.h"
#include "content/public/common/content_switches.h"
#include "headless/lib/browser/headless_browser_impl.h"
#include "headless/lib/browser/headless_web_contents_impl.h"
#include "headless/lib/headless_content_main_delegate.h"
#include "headless/public/headless_browser.h"
#include "headless/public/headless_browser_context.h"
#include "headless/public/headless_web_contents.h"
#include "headless/public/switches.h"
#include "net/base/filename_util.h"
#include "url/gurl.h"
#if BUILDFLAG(IS_MAC)
#include "components/os_crypt/sync/os_crypt_switches.h"  // nogncheck
#endif
#if BUILDFLAG(IS_WIN)
#include "base/strings/utf_string_conversions.h"
#include "components/crash/core/app/crash_switches.h"  // nogncheck
#include "components/crash/core/app/run_as_crashpad_handler_win.h"
#include "sandbox/win/src/sandbox_types.h"
#endif
#if defined(HEADLESS_USE_POLICY)
#include "components/headless/policy/headless_mode_policy.h"  // nogncheck
#endif
#if defined(HEADLESS_ENABLE_COMMANDS)
#include "components/headless/command_handler/headless_command_handler.h"  // nogncheck
#endif
namespace headless {
namespace {
GURL ConvertArgumentToURL(const base::CommandLine::StringType& arg) {
#if BUILDFLAG(IS_WIN)
  GURL url(base::WideToUTF8(arg));
#else
  GURL url(arg);
#endif
  if (url.is_valid() && url.has_scheme())
    return url;
  return net::FilePathToFileURL(
      base::MakeAbsoluteFilePath(base::FilePath(arg)));
} // useful but bring it in later
// An application which implements a simple headless browser.
class HeadlessShell {
 public:
  HeadlessShell() = default;
  HeadlessShell(const HeadlessShell&) = delete;
  HeadlessShell& operator=(const HeadlessShell&) = delete;
  ~HeadlessShell() = default;
  void OnBrowserStart(HeadlessBrowser* browser);
 private:
  void ShutdownSoon();
  void Shutdown();
  raw_ptr<HeadlessBrowser> browser_ = nullptr;
};
void HeadlessShell::OnBrowserStart(HeadlessBrowser* browser) {
  //std::cout << "We cool" << std::endl;
  browser_ = browser;
  base::raw_ptr<kaleido::Kaleido> kaleido = new kaleido::Kaleido();
  kaleido->OnBrowserStart(browser);
  // seg fault
  return;
  // Otherwise instantiate headless shell command handler that will
  // execute the commands against the target page.
}
void HeadlessShell::ShutdownSoon() {
  browser_->BrowserMainThread()->PostTask(
      FROM_HERE,
      base::BindOnce(&HeadlessShell::Shutdown, base::Unretained(this)));
}
void HeadlessShell::Shutdown() {
  browser_.ExtractAsDangling()->Shutdown();
}
void HeadlessChildMain(content::ContentMainParams params) {
  HeadlessContentMainDelegate delegate(nullptr);
  params.delegate = &delegate;
  int rc = content::ContentMain(std::move(params));
  // Note that exiting from here means that base::AtExitManager objects will not
  // have a chance to be destroyed (typically in main/WinMain).
  // Use TerminateCurrentProcessImmediately instead of exit to avoid shutdown
  // crashes and slowdowns on shutdown.
  base::Process::TerminateCurrentProcessImmediately(rc);
}
int HeadlessBrowserMain(content::ContentMainParams params) {
#if DCHECK_IS_ON()
  // The browser can only be initialized once.
  static bool browser_was_initialized;
  DCHECK(!browser_was_initialized);
  browser_was_initialized = true;
  // Child processes should not end up here.
  DCHECK(!base::CommandLine::ForCurrentProcess()->HasSwitch(
      ::switches::kProcessType));
#endif
  HeadlessShell shell;
  auto browser = std::make_unique<HeadlessBrowserImpl>(
      base::BindOnce(&HeadlessShell::OnBrowserStart, base::Unretained(&shell)));
  HeadlessContentMainDelegate delegate(std::move(browser));
  params.delegate = &delegate;
  return content::ContentMain(std::move(params));
}
}  // namespace
int HeadlessShellMain(content::ContentMainParams params) {
#if BUILDFLAG(IS_WIN)
  base::CommandLine::Init(0, nullptr);
#else
  base::CommandLine::Init(params.argc, params.argv);
#endif  // BUILDFLAG(IS_WIN)
  base::CommandLine& command_line(*base::CommandLine::ForCurrentProcess());
  std::string process_type =
      command_line.GetSwitchValueASCII(::switches::kProcessType);
#if defined(HEADLESS_USE_CRASHPAD)
  if (process_type == crash_reporter::switches::kCrashpadHandler) {
    return crash_reporter::RunAsCrashpadHandler(
        *base::CommandLine::ForCurrentProcess(), base::FilePath(),
        ::switches::kProcessType, switches::kUserDataDir);
  }
#endif  // defined(HEADLESS_USE_CRASHPAD)
  if (!process_type.empty()) {
    HeadlessChildMain(std::move(params));
    NOTREACHED_IN_MIGRATION();
  }
#if BUILDFLAG(IS_MAC)
  command_line.AppendSwitch(os_crypt::switches::kUseMockKeychain);
#endif
#if BUILDFLAG(IS_FUCHSIA)
  // TODO(fuchsia): Remove this when GPU accelerated compositing is ready.
  command_line.AppendSwitch(::switches::kDisableGpu);
#endif
  if (command_line.GetArgs().size() > 1) {
    LOG(ERROR) << "Multiple targets are not supported.";
    return EXIT_FAILURE;
  }
  return HeadlessBrowserMain(std::move(params));
}
}  // namespace headless

///
/// END OMG
///
///

/// END COPY 2
namespace kaleido {

Kaleido::Kaleido() = default;

// Control Flow, declare here
void Kaleido::ShutdownSoon() {
  scope_ptr = nullptr;
  browser_->BrowserMainThread()->PostTask(
      FROM_HERE,
      base::BindOnce(&Kaleido::ShutdownTask, base::Unretained(this)));
}
void Kaleido::ShutdownTask() {
  LOG(INFO) << "Calling shutdown on browser";
  if (tmpFileName.value().size()) base::DeleteFile(tmpFileName);
  dispatch->Release(); // Fine to destruct what we have here.
  dispatch = nullptr;
  browser_.ExtractAsDangling()->Shutdown();
}

void Kaleido::OnBrowserStart(headless::HeadlessBrowser* browser) {
  //std::cout << "OnBrowserStart" << std::endl;
  browser_ = browser; // global by another name

  // Actual constructor duties, init stuff
  output_sequence = base::ThreadPool::CreateSequencedTaskRunner(
      {base::TaskPriority::BEST_EFFORT, base::TaskShutdownBehavior::SKIP_ON_SHUTDOWN}
    ); // Can't do this before OnBrowserStart!

  dispatch = new Dispatch(this); // Tab manager

  // Create browser context and set it as the default. The default browser
  // context is used by the Target.createTarget() DevTools command when no other
  // context is given.
  // This stuff has weird side effects and I'm not sure its necessary.
  headless::HeadlessBrowserContext::Builder context_builder = browser_->CreateBrowserContextBuilder();
  context_builder.SetIncognitoMode(true);
  headless::HeadlessBrowserContext* browser_context = context_builder.Build();
  browser_->SetDefaultBrowserContext(browser_context);

  // BEGIN COPY 1
  // Get the scope from the command line.
  base::CommandLine::StringVector args =
          base::CommandLine::ForCurrentProcess()->GetArgs();
  if (args.empty()) {
      Api_OldMsg(1, "No Scope Specified");
      browser->Shutdown();
      exit(EXIT_FAILURE);
  }
  // Get first command line argument as a std::string using a string stream.
  // This handles the case where args[0] is a wchar_t on Windows
  std::stringstream scope_stringstream;
  scope_stringstream << args[0];
  scope_name = scope_stringstream.str();

  // Instantiate renderer scope
  scope_ptr = LoadScope(scope_name);
  scope_args = scope_ptr->BuildCallArguments();

  if (!scope_ptr) {
      // Invalid scope name
      Api_OldMsg(1,  base::StringPrintf("Invalid scope: %s", scope_name.c_str()));
      browser->Shutdown();
      exit(EXIT_FAILURE);
  } else if (!scope_ptr->errorMessage.empty()) {
      Api_OldMsg(1,  scope_ptr->errorMessage);
      browser->Shutdown();
      exit(EXIT_FAILURE);
  }

  // Add javascript bundle
  scope_ptr->localScriptFiles.emplace_back("./js/kaleido_scopes.js");

  // Build initial HTML file
  std::list<std::string> scriptTags = scope_ptr->ScriptTags();
  std::stringstream htmlStringStream;
  htmlStringStream << "<html><head><meta charset=\"UTF-8\"><style id=\"head-style\"></style>";

  // Add script tags
  while (!scriptTags.empty()) {
      std::string tagValue = scriptTags.front();
      GURL tagUrl(tagValue);
      if (tagUrl.is_valid()) {
          // Value is a url, use a src of script tag
          htmlStringStream << "<script type=\"text/javascript\" src=\"" << tagValue << "\"></script>";
      } else {
          // Value is not a url, use a inline JavaScript code
          htmlStringStream << "<script>" << tagValue << "</script>\n";
      }
      scriptTags.pop_front();
  }
  // Close head and add body with img tag place holder for PDF export
  htmlStringStream << "</head><body style=\"{margin: 0; padding: 0;}\"><img id=\"kaleido-image\"><img></body></html>";

  // Write html to temp file
  tmpFileName = base::FormatTemporaryFileName(HTML);
  std::ofstream htmlFile;
  htmlFile.open(tmpFileName.value(), std::ios::out);
  htmlFile << htmlStringStream.str();
  LOG(INFO) << "Dumping HTML from memory";
  LOG(INFO) << htmlStringStream.str().c_str();
  LOG(INFO) << "Log file name:";
  LOG(INFO) << tmpFileName;
  htmlFile.close();

  // Create file:// url to temp file
  LOG(INFO) << "Log file name narrowed:";
  GURL url = headless::ConvertArgumentToURL(tmpFileName.value());
  LOG(INFO) << url.spec();

  // Initialization succeeded
  Api_OldMsg(0, "Initilization Success");

  // END COPY 1
  // Run
  dispatch->CreateTab(-1, url);
  // PART OF copy 1
  for (std::string const &s: scope_ptr->LocalScriptFiles()) {
    localScriptFiles.push_back(s);
  }
  base::GetCurrentDirectory(&cwd);
  // END THAT

  StartListen();
  // TODO Destructor, temp files not destroyed

}

// Wish this were a lambda (as in PostEcho) but would have no access to private vars
void Kaleido::listenTask() {
  std::string in;
  if (!std::getline(std::cin, in).good()) {
    LOG(WARNING) << in << ": "
      << (std::cin.eof() ? "EOF | " : "")
      << (std::cin.eof() ? "BAD | " : "GOOD | ")
      << (std::cin.eof() ? "FAIL" : "SUCCESS");
    ShutdownSoon();
    return;
  };
  if (in == "\n") postListenTask();
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
  if (old) {
    LOG(INFO) << msg;
    return;
  }
  auto echo = [](const std::string &msg){ std::cout << msg << std::endl; };
  output_sequence->PostTask(FROM_HERE, base::BindOnce(echo, msg));
}

void Kaleido::PostEchoTaskOld(const std::string &msg) {
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
  absl::optional<int> id = jsonDict.FindInt("id");
  std::string *operation = jsonDict.FindString("operation");
  std::string *maybe_format = jsonDict.FindString("format");
  // The only operation we handle here. We're shutting down.
  // Trust chromium to handle it all when the browser exits
  // Doesn't need id, no return
  if (operation && *operation == "shutdown") {
    LOG(INFO) << "Shutdown clean";
    ShutdownSoon();
    return false; // breaks stdin loop
  }
  if (!operation || !id) {
    // we are likely using the old protocol, which for now is all we accept
    if (maybe_format) {
      LOG(INFO) << "It seems like we're using the old protocol.";
      old=true;
      std::unique_ptr<Job> job = std::make_unique<Job>();
      job->version = 0;
      job->id = -2;
      job->format = *maybe_format;
      job->scope = scope_ptr->ScopeName().c_str();
      job->spec_parsed = std::move(jsonDict);
      dispatch->PostJob(std::move(job));
      return true;
    } else {
      Api_ErrorMissingBasicFields(id);
      return true;
    }
  }
  if (!old) {
    if (*id < 0) {
      Api_ErrorNegativeId(*id);
      return true;
    }
    if (messageIds.find(*id) != messageIds.end()) {
      Api_ErrorDuplicateId(*id);
      return true;
    }
  }
  if (operation && *operation == "create_tab") {
    std::string urlCopy(tmpFileName.value().begin(), tmpFileName.value().end());
    dispatch->CreateTab(*id, GURL(FILE_URI_PREFIX + urlCopy));
  } else if (operation && *operation == "reload") {
    dispatch->ReloadAll();
  } else if (operation && *operation == "noop") {} else {
    Api_ErrorUnknownOperation(*id, *operation);
    return true;
  }


  if (!old) messageIds.emplace(*id, *operation);
  return true;
}

void Kaleido::ReportOperation(int id, bool success, const base::Value::Dict &msg) {
  if (!success && id < 0) {
    LOG(ERROR) << "Failure of internal dev tools operation id "
      << std::to_string(id)
      << " and msg: "
      << msg;
    return;
  } else if (success && id < 0) {
    LOG(INFO) << "Success of internal dev tools operation id "
      << std::to_string(id)
      << " and msg: "
      << msg;
    return;
  }
  PostEchoTask(R"({"id":)"+std::to_string(id)+R"(,"success":)"+std::to_string(success)+R"(, "msg":)"+msg.DebugString()+R"(})");
}
void Kaleido::ReportFailure(int id, const std::string& msg) {
  if (id < 0) {
    LOG(ERROR) << "Failure of internal dev tools operation id "
      << std::to_string(id)
      << " and msg: "
      << msg;
    return;
  }
  PostEchoTask(R"({"id":)"+std::to_string(id)+R"(,"success":false, "msg":")"+msg+R"("})");
}

void Kaleido::ReportSuccess(int id) {
  if (id < 0) {
    LOG(INFO) << "Success of message with id " << std::to_string(id);
    return;
  }
  PostEchoTask(R"({"id":)"+std::to_string(id)+R"(,"success":true})");
}

void Kaleido::Api_ErrorInvalidJSON() {
  PostEchoTask(R"({"error":"malformed JSON string"})");
}

void Kaleido::Api_ErrorMissingBasicFields(absl::optional<int> id) {
  if (id) {
    PostEchoTask(R"({"id":)"+std::to_string(*id)+R"(,"error":"all messages must contain an 'id' integer and an 'operation' string"})");
  } else {
    PostEchoTask(R"({"error":"all messages must contain an 'id' integer and an 'operation' string"})");
  }
}

void Kaleido::Api_ErrorDuplicateId(int id) {
  PostEchoTask(R"({"id":)"+std::to_string(id)+R"(,"error":"message using already-used 'id' integer"})");
}

void Kaleido::Api_ErrorNegativeId(int id) {
  PostEchoTask(R"({"id":)"+std::to_string(id)+R"(,"error":"must use 'id' integer >=0"})");
}

void Kaleido::Api_ErrorUnknownOperation(int id, const std::string& op) {
  PostEchoTask(R"({"id":)"+std::to_string(id)+R"(,"error":"Unknown operation:)"+op+R"("})");
}

void Kaleido::Api_OldMsg(int code, std::string message) {
    static std::string *version = nullptr;
    if (!version) {
        std::ifstream verStream("version");
        version = new std::string((
                    std::istreambuf_iterator<char>(verStream)),std::istreambuf_iterator<char>());
    }
    std::string error = base::StringPrintf(
            "{\"code\": %d, \"message\": \"%s\", \"result\": null, \"version\": \"%s\"}",
            code, message.c_str(), version->c_str());
    PostEchoTaskOld(error);
}

} // namespace kaleido
