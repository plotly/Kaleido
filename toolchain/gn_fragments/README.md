1. We have to define a kaleido executable. To do that, we hijack chromium's headless app. That executable is defined at the bottom of `src/headless/BUILD.gn`. We copy and adapt that definition to kaleido (what you see in this `BUILD.gn`) and append it to the bottom of the former.
2. Arguments are specified in an args.gn in our desired output directory, which is passed as an argument to the `ninja` command in the ??-build_kaleido.sh script.

As well as these files and their includes, reading `src/headless/BUILD.gn` and `src/headless/headless.gni` will help to understand possible arguments in `args.gn`.

If its not already, its very likely these will have to be adapted per chromium version.

`enable_printing` and `proprietary_codecs` are particularly interesting, and deserve investigation.
