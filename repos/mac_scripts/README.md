This is a stub with just some stuff copied and pasted from the legacy readme.

-------------------------


## MacOS
To build on MacOS, first install XCode version 11.0+, nodejs 12, and Python 3.  See https://chromium.googlesource.com/chromium/src/+/master/docs/mac_build_instructions.md for more information on build requirements.

Then fetch the chromium codebase

```
$ /repos/mac_scripts/fetch_chromium
```

Then build Kaleido to `repos/build/kaleido`. The build step will also create the Python wheel under `repos/kaleido/py/dist/`

```
$ /repos/mac_scripts/build_kaleido
```
