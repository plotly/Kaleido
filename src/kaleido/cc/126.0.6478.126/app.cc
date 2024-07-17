// app.cc
//  goals:
// 

// the build system thinks these are deps of kaleido.cc and kaleido.h,
// it only works because they all have to be in the same namespace anyway
// since they're linked together
#include "headless/app/kaleido.h"

// Fundamental chromium includes
#include "content/public/app/content_main.h"

// Fundamental utilities
#include "base/logging.h"
#include "base/files/file_util.h"

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

#if BUILDFLAG(IS_WIN)
#include "base/strings/utf_string_conversions.h"
#include "components/crash/core/app/crash_switches.h"  // nogncheck
#include "components/crash/core/app/run_as_crashpad_handler_win.h"
#include "sandbox/win/src/sandbox_types.h"
#endif

void buildSandbox(content::ContentMainParams);
void processCommandline(content::ContentMainParams, int argc, const char** argv);

int main(int argc, const char** argv) {
  content::ContentMainParams params(nullptr); 

  LOG(INFO) << "Building sandbox";
  buildSandbox(std::move(params));
  
  // chromium restarts this process several times to create child processes
  // this boilerplate helps the process determine if its a // Can you clear up deps in build?child process or not
  // we cannot intercept chromium commandline flags easily due to this
  LOG(INFO) << "Processing commandlines";
  processCommandline(std::move(params), argc, argv);

  // Make a Kaleido browser
  LOG(INFO) << "Making a kaleido browser";
  kaleido::Kaleido kbrowser(std::move(params));

  // Run chromium'smmain loop
  LOG(INFO) << "Running main content loop";
  return content::ContentMain(std::move(params));
  // return EXIT_FAILURE; // save for future use, where does EXIT_FAILURE come from?
}

// Construct sandbox (even tho we will disable it)
void buildSandbox(content::ContentMainParams params) {
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

void processCommandline(content::ContentMainParams params, int argc, const char** argv) {
  #if BUILDFLAG(IS_WIN)
    base::CommandLine::Init(0, nullptr); // Windows takes no commands, I guess?
  #else
    base::CommandLine::Init(argc, argv);
  #endif  // BUILDFLAG(IS_WIN)


  base::CommandLine& command_line(*base::CommandLine::ForCurrentProcess());
  // command_line.AppendSwitch(::switches::kDisableGpu); // <-- possibility
  // It is possible, that if we see we're not a child process, we can add the switches needed
  
  // Some Logging
  LOG(INFO) << "Original command: " << command_line.GetArgumentsString();
  LOG(INFO) << "Args size: " << command_line.GetArgs().size();
  for (const auto &piece : command_line.GetArgs()) {
    LOG(INFO) << piece << std::endl;
  }

  // This is where Chromium determines if it is a child or the main process
  std::string process_type = command_line.GetSwitchValueASCII(::switches::kProcessType);
  LOG(INFO) << "Process type: " << process_type;

  #if defined(HEADLESS_USE_CRASHPAD)
    LOG(INFO) << "Defined: HEADLESS_USE_CRASHPAD";
    if (process_type == crash_reporter::switches::kCrashpadHandler) {
      return crash_reporter::RunAsCrashpadHandler(
          *base::CommandLine::ForCurrentProcess(), base::FilePath(),
          ::switches::kProcessType, switches::kUserDataDir);
    }
  #endif  // defined(HEADLESS_USE_CRASHPAD)

  if (!process_type.empty()) {
    LOG(INFO) << "Is child process.";
    kaleido::ChildProcess(std::move(params));
  } else {
    // So we must be the main process...
    LOG(INFO) << "Is not child process.";
  }


  #if BUILDFLAG(IS_MAC)
    LOG(INFO) << "IS_MAC appending kUseMockKeychain";
    command_line.AppendSwitch(os_crypt::switches::kUseMockKeychain);
  #endif
}
