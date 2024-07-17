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

#include "headless/app/kaleido.h"


int main(int argc, const char** argv) {

  // These switches likely to processed at some point
  // Browser probably needs to be started to use Chromium's builtins
  return kaleido::KaleidoMain(argc, argv);
}
