// kaleido_main.cc runs main() and includes a lot of google boilerplate.
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
namespace {
  void buildSandbox(content::ContentMainParams);
  void processCommandLine(content::ContentMainParams, int argc, const char** argv);
}


int main(int argc, const char** argv) {
  content::ContentMainParams params(nullptr);

  buildSandbox(std::move(params));

  processCommandLine(std::move(params), argc, argv);

  // Now we're going to start the browser
  // Would love to do this inside the constructor but
  // ... chromium just hates it.
  auto browser = std::make_unique<headless::HeadlessBrowserImpl>(
      base::BindOnce(&kaleido::Kaleido::OnBrowserStart, base::Unretained(new kaleido::Kaleido())));
      // Should be a lambda that starts a Kaleido, not a function in Kaleido
  headless::HeadlessContentMainDelegate delegate(std::move(browser));
  params.delegate = &delegate;
  return content::ContentMain(std::move(params));
}


namespace {

void buildSandbox(content::ContentMainParams) {
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
}

void processCommandLine(content::ContentMainParams params, int argc, const char** argv) {

  #if BUILDFLAG(IS_WIN)
    base::CommandLine::Init(0, nullptr);
  #else
    base::CommandLine::Init(argc, argv);
  #endif  // BUILDFLAG(IS_WIN)

  base::CommandLine& command_line(*base::CommandLine::ForCurrentProcess());
  // command_line.AppendSwitch(::switches::kDisableGpu); // <-- possibility
  // could be used to always put on essential switches

  LOG(INFO) << "Original command: " << command_line.GetArgumentsString();
  LOG(INFO) << "Args size: " << command_line.GetArgs().size();
  for (const auto &piece : command_line.GetArgs()) {
    LOG(INFO) << piece << std::endl;
  }


  std::string process_type = command_line.GetSwitchValueASCII(::switches::kProcessType);
  LOG(INFO) << "Process type: " << process_type;

  #if defined(HEADLESS_USE_CRASHPAD)
    if (process_type == crash_reporter::switches::kCrashpadHandler) {
      return crash_reporter::RunAsCrashpadHandler(
          *base::CommandLine::ForCurrentProcess(), base::FilePath(),
          ::switches::kProcessType, switches::kUserDataDir);
    }
  #endif  // defined(HEADLESS_USE_CRASHPAD)

  // Chromium starts child processes, and we need this to catch them and their flags
  if (!process_type.empty()) {
    headless::HeadlessContentMainDelegate delegate(nullptr);
    params.delegate = &delegate;
    int rc = content::ContentMain(std::move(params));
    base::Process::TerminateCurrentProcessImmediately(rc);
    NOTREACHED_IN_MIGRATION();
  }
  // So we must be the main process...

  #if BUILDFLAG(IS_MAC)
    command_line.AppendSwitch(os_crypt::switches::kUseMockKeychain);
  #endif
}

} // namespace


#if defined(OS_WIN)
namespace base {
    // Chromium doens't provide and implementation of ExecutableExistsInPath on Windows, so we add one here
    bool ExecutableExistsInPath(Environment* env,
        const std::string& executable) {
        std::string path;
        if (!env->GetVar("PATH", &path)) {
            LOG(ERROR) << "No $PATH variable. Assuming no " << executable << ".";
            return false;
        }

        for (const StringPiece& cur_path:
            SplitStringPiece(path, ";", KEEP_WHITESPACE, SPLIT_WANT_NONEMPTY)) {

            // Build wide strings using wstringstreams
            std::wstringstream wpath_ss;
            wpath_ss << std::string(cur_path).c_str();

            std::wstringstream wexecutable_ss;
            wexecutable_ss << executable.c_str() << ".exe";

            std::wstring wpath_ss_as_string = wpath_ss.str();
            FilePath::StringPieceType w_cur_path(wpath_ss_as_string);
            FilePath file(w_cur_path);

            if (PathExists(file.Append(wexecutable_ss.str()))) {
                return true;
            }
        }
        return false;
    }
}
#endif
