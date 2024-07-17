
#include "headless/app/kaleido.h"

// Fundamental chromium includes
#include "content/public/app/content_main.h"
#include "headless/lib/headless_content_main_delegate.h"

// Fundamental utilities
#include "base/logging.h"
#include "base/files/file_util.h"
#include "base/functional/bind.h"

#include "build/build_config.h" // IS_WIN and stuff like that

// Sandbox Includes
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

#if BUILDFLAG(IS_WIN)
#include "base/strings/utf_string_conversions.h"
#include "components/crash/core/app/crash_switches.h"  // nogncheck
#include "components/crash/core/app/run_as_crashpad_handler_win.h"
#include "sandbox/win/src/sandbox_types.h"
#endif

// Can you clear up deps in build?
//
namespace kaleido {

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

#if BUILDFLAG(IS_WIN)
  base::CommandLine::Init(0, nullptr);
  // It's a good way to process CommandLine, but is windows really not capable of using it?
#else
  base::CommandLine::Init(argc, argv);
#endif  // BUILDFLAG(IS_WIN)

  base::CommandLine& command_line(*base::CommandLine::ForCurrentProcess());
  std::string process_type = command_line.GetSwitchValueASCII(::switches::kProcessType);
  LOG(INFO) << "Process type: " << process_type;
  // command_line.AppendSwitch(::switches::kDisableGpu); // <-- possibility

#if defined(HEADLESS_USE_CRASHPAD)
  if (process_type == crash_reporter::switches::kCrashpadHandler) {
    return crash_reporter::RunAsCrashpadHandler(
        *base::CommandLine::ForCurrentProcess(), base::FilePath(),
        ::switches::kProcessType, switches::kUserDataDir);
  }
#endif  // defined(HEADLESS_USE_CRASHPAD)

// BELOW IS A TEMPORARY MUST-REMOVE TEST
#if BUILDFLAG(IS_WIN)
#if defined(HEADLESS_USE_CRASHPAD)
  LOG(FATAL) << "crashpad IS used on windows, reactivate comments. Need command_line boilerplate." << std::endl;
#else
  LOG(FATAL) << "we can get rid of all crashpad" << std::endl;
#endif
#endif
  // Some Logging
  LOG(INFO) << "Original command: " << command_line.GetArgumentsString();
  LOG(INFO) << "Args size: " << command_line.GetArgs().size();
  for (const auto &piece : command_line.GetArgs()) {
    LOG(INFO) << piece << std::endl;
  }
  if (!process_type.empty()) {
    headless::HeadlessContentMainDelegate delegate(nullptr);
    params.delegate = &delegate;
    int rc = content::ContentMain(std::move(params));
    base::Process::TerminateCurrentProcessImmediately(rc);
    NOTREACHED_IN_MIGRATION();
  }
  // So we must be the main process...

// EXAMPLE SAYS WE (MAC USERS) NEED THIS
#if BUILDFLAG(IS_MAC)
  command_line.AppendSwitch(os_crypt::switches::kUseMockKeychain);
#endif


  // Now we're going to start the browser
  Kaleido kmanager;
  auto browser = std::make_unique<headless::HeadlessBrowserImpl>(
      base::BindOnce(&Kaleido::OnBrowserStart, base::Unretained(&kmanager)));
  headless::HeadlessContentMainDelegate delegate(std::move(browser));
  params.delegate = &delegate;
  return content::ContentMain(std::move(params));
  // return EXIT_FAILURE; // save for future use, where does EXIT_FAILURE come from?
}

} // namespace kaleido
