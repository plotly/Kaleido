// app.cc
//  goals:
//    Almost none. We just start up the main kaleido process, see kaleido.cc.
//  Much of app.cc is boilerplate taking from headless/app/ example:
//  - it starts sandboxes, which may be pointless, but our flags are chaos
//      - init_tools flags no sandbox
//      - here we initialize it
//      - python then turns it off again
//      - it is not really necessary
//  - it, depending on platform, moves argc and argv towards a HeadlessBrowser instance
//
//  It is better not to pass whatever chromium flag into kaleido,
//  unless there was a flag specifically for that "--chromium_flags="--whatever=23,-f," etc

#include "build/build_config.h"
#include "headless/app/kaleido.h"

#if BUILDFLAG(IS_WIN)
#include "content/public/app/sandbox_helper_win.h"
#include "sandbox/win/src/sandbox_types.h"  // nogncheck
#elif BUILDFLAG(IS_MAC)
#include "base/check.h"
#include "sandbox/mac/seatbelt_exec.h"
#endif

int main(int argc, const char** argv) {
  content::ContentMainParams params(nullptr);
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
  return 0;
  //return headless::HeadlessShellMain(std::move(params));
}
