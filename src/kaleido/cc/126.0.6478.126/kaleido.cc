// kaleido.cc:
//  goals:
//    * start up the browser
//    * start up the tab manager
//    * start up the IO thread

#include "headless/app/kaleido.h"

// fundamental chromium includes
#include "content/public/app/content_main.h"
#include "base/logging.h"

#include "build/build_config.h" // IS_WIN and stuff like that
#if BUILDFLAG(IS_WIN)
#include "content/public/app/sandbox_helper_win.h"
#include "sandbox/win/src/sandbox_types.h"  // nogncheck
#elif BUILDFLAG(IS_MAC)
#include "base/check.h"
#include "sandbox/mac/seatbelt_exec.h"
#endif

// CLI includes, not sure if using all
#include "base/command_line.h"
#include "base/base_switches.h"
#include "content/public/common/content_switches.h"
#include "headless/public/switches.h"
#if BUILDFLAG(IS_MAC)
#include "components/os_crypt/sync/os_crypt_switches.h"  // nogncheck
#endif

namespace kaleido {

//  Much of KaleidoMain is boilerplate taking from headless/app/ example:
//  - it starts sandboxes, which may be pointless, but our flags are chaos
//      - init_tools flags no sandbox
//      - here we initialize it
//      - python then turns it off again
//      - it is not really necessary
//  - it, depending on platform, moves argc and argv towards a HeadlessBrowser instance
//
//  It is better not to pass whatever chromium flag into kaleido,
//  unless there was a flag specifically for that "--chromium_flags="--whatever=23,-f," etc
int KaleidoMain(int argc, const char** argv) {
  content::ContentMainParams params(nullptr); // TODO  WHAT IS THIS REALLY FOR

// LETS CONSTRUCT SANDBOX THAT WE THEN DISABLE
#if BUILDFLAG(IS_WIN)
  sandbox::SandboxInterfaceInfo sandbox_info = {nullptr};
  content::InitializeSandboxInfo(&sandbox_info);
  // Sandbox info has to be set and initialized.
  params.sandbox_info = &sandbox_info;
#else
  params.argc = argc;
  params.argv = argv;
#if BUILDFLAG(IS_MAC)
  sandbox::SeatbeltExecServer::CreateFromArgumentsResult seatbelt =
      sandbox::SeatbeltExecServer::CreateFromArguments(
          argv[0], argc, const_cast<char**>(argv));
  if (seatbelt.sandbox_required) {
    CHECK(seatbelt.server->InitializeSandbox());
  }
#endif  // BUILDFLAG(IS_MAC)
#endif  // BUILDFLAG(IS_WIN)

  base::CommandLine::Init(0, nullptr);

  base::CommandLine& command_line(*base::CommandLine::ForCurrentProcess());
  // command_line.AppendSwitch(::switches::kDisableGpu); // <-- possibility


// BELOW IS A TEMPORARY MUST-REMOVE TEST
#if BUILDFLAG(IS_WIN)
#if defined(HEADLESS_USE_CRASHPAD)
  LOG(FATAL) << "crashpad IS used on windows, reactivate comments. Need command_line boilerplate." << std::endl;
#else
  LOG(FATAL) << "we can get rid of all crashpad" << std::endl;
#endif
#endif

// EXAMPLE SAYS WE (MAC USERS) NEED THIS
#if BUILDFLAG(IS_MAC)
  command_line.AppendSwitch(os_crypt::switches::kUseMockKeychain);
#endif

  // Some Logging
  LOG(INFO) << "Original command: " << command_line.GetArgumentsString();
  LOG(INFO) << "Args size: " << command_line.GetArgs().size();
  for (const auto &piece : command_line.GetArgs()) {
    LOG(INFO) << piece << std::endl;
  }

  // Now we're going to start the browser
  HeadlessShell shell;
  auto browser = std::make_unique<HeadlessBrowserImpl>(
      base::BindOnce(&HeadlessShell::OnBrowserStart, base::Unretained(&shell)));
  HeadlessContentMainDelegate delegate(std::move(browser));
  params.delegate = &delegate;
  return content::ContentMain(std::move(params));
  // return EXIT_FAILURE; // save for future use, where does EXIT_FAILURE come from?
}

} // namespace kaleido

/*
#include <memory>

#include "base/files/file_util.h"
#include "base/functional/bind.h"
#include "base/task/thread_pool.h"
#include "build/branding_buildflags.h"
#include "build/build_config.h"
#include "content/public/app/content_main.h"
#include "headless/lib/browser/headless_browser_impl.h"
#include "headless/lib/browser/headless_web_contents_impl.h"
#include "headless/lib/headless_content_main_delegate.h"
#include "headless/public/headless_browser.h"
#include "headless/public/headless_browser_context.h"
#include "headless/public/headless_web_contents.h"

#include "net/base/filename_util.h"
#include "url/gurl.h"


#if BUILDFLAG(IS_WIN)
#include "base/strings/utf_string_conversions.h"
#include "components/crash/core/app/crash_switches.h"  // nogncheck
#include "components/crash/core/app/run_as_crashpad_handler_win.h"
#include "sandbox/win/src/sandbox_types.h"
#endif

namespace kaleido {

namespace {

#if BUILDFLAG(IS_WIN)
const wchar_t kAboutBlank[] = L"about:blank";
#else
const char kAboutBlank[] = "about:blank";
#endif

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
}

// An application which implements a simple headless browser.
class HeadlessShell {
 public:
  HeadlessShell() = default;

  HeadlessShell(const HeadlessShell&) = delete;
  HeadlessShell& operator=(const HeadlessShell&) = delete;

  ~HeadlessShell() = default;

  void OnBrowserStart(HeadlessBrowser* browser);

 private:
#if defined(HEADLESS_ENABLE_COMMANDS)
  void OnProcessCommandsDone(HeadlessCommandHandler::Result result);
#endif
  void ShutdownSoon();
  void Shutdown();

  raw_ptr<HeadlessBrowser> browser_ = nullptr;
};

void HeadlessShell::OnBrowserStart(HeadlessBrowser* browser) {
  browser_ = browser;

#if defined(HEADLESS_USE_POLICY)
  if (HeadlessModePolicy::IsHeadlessModeDisabled(
          static_cast<HeadlessBrowserImpl*>(browser)->GetPrefs())) {
    LOG(ERROR) << "Headless mode is disallowed by the system admin.";
    ShutdownSoon();
    return;
  }
#endif

  HeadlessBrowserContext::Builder context_builder =
      browser_->CreateBrowserContextBuilder();

  // Create browser  context and set it as the default. The default browser
  // context is used by the Target.createTarget() DevTools command when no other
  // context is given.
  HeadlessBrowserContext* browser_context = context_builder.Build();
  browser_->SetDefaultBrowserContext(browser_context);

  const bool devtools_enabled = static_cast<HeadlessBrowserImpl*>(browser)
                                    ->options()
                                    ->DevtoolsServerEnabled();

  // If no explicit URL is present navigate to about:blank unless we're being
  // driven by a debugger.
  base::CommandLine::StringVector args =
      base::CommandLine::ForCurrentProcess()->GetArgs();
  args.erase(
      std::remove(args.begin(), args.end(), base::CommandLine::StringType()),
      args.end());

  if (args.empty() && !devtools_enabled) {
    args.push_back(kAboutBlank);
  }

  if (args.empty()) {
    return;
  }

  GURL target_url = ConvertArgumentToURL(args.front());
  HeadlessWebContents::Builder builder(
      browser_context->CreateWebContentsBuilder());

  // If driven by a debugger just open the target page and
  // leave expecting the debugger will do what they need.
  if (devtools_enabled) {
    HeadlessWebContents* web_contents =
        builder.SetInitialURL(target_url).Build();
    if (!web_contents) {
      LOG(ERROR) << "Navigation to " << target_url << " failed.";
      ShutdownSoon();
    }
    return;
  }

  // Otherwise instantiate headless shell command handler that will
  // execute the commands against the target page.
#if defined(HEADLESS_ENABLE_COMMANDS)
  GURL handler_url = HeadlessCommandHandler::GetHandlerUrl();
  HeadlessWebContents* web_contents =
      builder.SetInitialURL(handler_url).Build();
  if (!web_contents) {
    LOG(ERROR) << "Navigation to " << handler_url << " failed.";
    ShutdownSoon();
    return;
  }

  HeadlessCommandHandler::ProcessCommands(
      HeadlessWebContentsImpl::From(web_contents)->web_contents(),
      std::move(target_url),
      base::BindOnce(&HeadlessShell::OnProcessCommandsDone,
                     base::Unretained(this)));
#endif
}

#if defined(HEADLESS_ENABLE_COMMANDS)
void HeadlessShell::OnProcessCommandsDone(
    HeadlessCommandHandler::Result result) {
  if (result != HeadlessCommandHandler::Result::kSuccess) {
    static_cast<HeadlessBrowserImpl*>(browser_)->ShutdownWithExitCode(
        static_cast<int>(result));
    return;
  }
  Shutdown();
}
#endif

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
}

}  // namespace

}  // namespace headless
*/
