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

// Browser Includes
#include "headless/lib/browser/headless_browser_impl.h"
#include "headless/public/headless_browser.h"


// Can you clear up deps in build?

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
  // It's a good way to process CommandLine, but is windows really not capable of using it?
  // Above was on windows only, below was all else
/*#else
  base::CommandLine::Init(argc, argv);
#endif  // BUILDFLAG(IS_WIN)*/
  // GetSwitches, RemoveSwitch, Nothing to do about arguments, they are there

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
  /*
  HeadlessShell shell;
  auto browser = std::make_unique<HeadlessBrowserImpl>(
      base::BindOnce(&HeadlessShell::OnBrowserStart, base::Unretained(&shell)));
  HeadlessContentMainDelegate delegate(std::move(browser));
  params.delegate = &delegate;
  return content::ContentMain(std::move(params));
  */
  return EXIT_FAILURE; // save for future use, where does EXIT_FAILURE come from?
}

// Kaleido manages a browser and its tabs
class Kaleido {
 public:
  Kaleido() = default;

  Kaleido(const Kaleido&) = delete;
  Kaleido& operator=(const Kaleido&) = delete;

  ~Kaleido() = default;

  void OnBrowserStart(HeadlessBrowser* browser);

 private:
  void ShutdownSoon();
  void Shutdown();
  raw_ptr<HeadlessBrowser> browser_ = nullptr;
};

} // namespace kaleido

/*
#include <memory>

#include "base/files/file_util.h"
#include "base/functional/bind.h"
#include "base/task/thread_pool.h"
#include "build/branding_buildflags.h"
#include "build/build_config.h"
#include "content/public/app/content_main.h"
#include "headless/lib/browser/headless_web_contents_impl.h"
#include "headless/lib/headless_content_main_delegate.h"
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


};

void HeadlessShell::OnBrowserStart(HeadlessBrowser* browser) {
  browser_ = browser;

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

void HeadlessShell::ShutdownSoon() {
  browser_->BrowserMainThread()->PostTask(
      FROM_HERE,
      base::BindOnce(&HeadlessShell::Shutdown, base::Unretained(this)));
}

void HeadlessShell::Shutdown() {
  browser_.ExtractAsDangling()->Shutdown();
}

}  // namespace

}  // namespace headless
*/
