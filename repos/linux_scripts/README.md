This is a stub with just some stuff copied and pasted from the legacy readme.

-------------------------

To update the version of Chromium in the future, the docker images will need to be updated. Follow the instructions for the `DEPOT_TOOLS_COMMIT` and `CHROMIUM_TAG` environment variables in `linux_scripts/Dockerfile`.

Update `checkout_revision_docker`.

## chromium-builder
The `chromium-builder` container mostly follows the instructions at https://chromium.googlesource.com/chromium/src/+/master/docs/linux/build_instructions.md to install `depot_tools` and run `install-build-deps.sh` to install the required build dependencies the appropriate stable version of Chromium. The image is based on ubuntu 16.04, which is the recommended OS for building Chromium on Linux.

Build container with:

```
$ docker build -t jonmmease/chromium-builder:0.9 -f repos/linux_scripts/Dockerfile .
```

## Linux
The Linux build relies on the `jonmmease/chromium-builder` docker image, and the scripts in `repos/linux_scripts`, to download the chromium source to a local folder and then build it.
Download docker image
```
$ docker pull jonmmease/chromium-builder:0.9
```

Fetch the Chromium codebase and checkout the specific tag, then sync all dependencies

```
$ /repos/linux_scripts/fetch_chromium
```

Then build the `kaleido` application to `repos/build/kaleido`, and bundle shared libraries and fonts. The input source for this application is stored under `repos/kaleido/cc/`. The build step will also
create the Python wheel under `repos/kaleido/py/dist/`

```
$ /repos/linux_scripts/build_kaleido x64
```

The above command will build Kaleido for the 64-bit Intel architecture. Kaleido can also be build for 64-bit ARM architecture with

```
$ /repos/linux_scripts/build_kaleido arm64
```


