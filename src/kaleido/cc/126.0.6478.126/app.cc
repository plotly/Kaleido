// app.cc
//  goals:
//    Almost none. We just start up the main kaleido process, see kaleido.cc.

#include "headless/app/kaleido.h"


int main(int argc, const char** argv) {

  // These switches likely to processed at some point
  // Browser probably needs to be started to use Chromium's builtins
  return kaleido::KaleidoMain(argc, argv);
}
