## WIP kaleido prototype
This is a WIP towards the goal of being able to perform static image export of web-based plotting libraries (starting with Plotly), from any relatively modern Linux distribution ((Ubuntu 16.04+, Centos 7+, etc.) without any external dependencies.

Rather than buiding on Electron, this idea here is to create a custom, stripped down, build of Chromium headless and then
bundle the necessary shared objects files, fonts, config, etc.

The Chromium source tree includes a minimal [`headless_example`](https://chromium.googlesource.com/chromium/src/+/lkgr/headless/README.md#usage-as-a-c_library) that was used as the starting point for this project.

## Docker container
First, create a docker container that is configured to download and build the chromium source tree.  This mostly follows the instructions at https://chromium.googlesource.com/chromium/src/+/master/docs/linux/build_instructions.md to install `depot_tools` and run `install-build-deps.sh` to install the required build dependencies the appropriate stable version of Chromium. The image is based on ubuntu 16.04, which is the recommended OS for building Chromium on Linux.

Build container with:

```
$ docker build -t jonmmease/chromium-builder:0.6 -f Dockerfile .
```


## Fetch chromium source code
This will download the full chromium source tree. **Caution**: This may take up to 40GB after build steps below
```
$ docker run -it -v `pwd`/repos/:/repos  jonmmease/chromium-builder:0.6 /repos/linux_scripts/fetch_chromium
```

## Checkout tag
This will checkout a specific stable tag of chromium, and then sync all dependencies
```
$ docker run -it --privileged --cap-add SYS_ADMIN --cap-add MKNOD --device /dev/fuse -v `pwd`/repos/:/repos  jonmmease/chromium-builder:0.6 /repos/linux_scripts/checkout_revision
```

## Build chromium headless
This will build the `headless_example` application to `repos/src/out/Headless/headless_example`
```
$ docker run -it -v `pwd`/repos/:/repos  jonmmease/chromium-builder:0.6 /repos/linux_scripts/build_headless
```

## Build kaleido
This will build the `kaleido` application to `repos/build/kaleido`, and bundle shared libraries and fonts. The input source for this application is in `repos/kaleido/kaleido.cc`.

```
$ docker run -it -v `pwd`/repos/:/repos  jonmmease/chromium-builder:0.6 /repos/linux_scripts/build_kaleido
```

To run the kaleido application, use the `/repos/build/kaleido/kaleido` bash script. This passes argumnets through to the `repos/build/kaleido/bin/kaleido` executable, but it also sets up the environment needed to use the bundled shared libraries, fonts, etc.

If you're running Linux locally, try it out on your local linux install with:

```
echo '{"figure":{"data":[{"y":[1,3,2], "name":"asdf another"}]},"format":"png"}' | repos/build/kaleido/kaleido plotly
```

You can try it out on in a raw ubuntu:16.04 docker image with:

```
echo '{"figure":{"data":[{"y":[1,3,2], "name":"asdf another"}]},"format":"png"}' | docker run -i -v `pwd`/repos/:/repos ubuntu:16.04 /repos/build/kaleido/kaleido plotly
```

This shows that we were able to invoke chromium on the most minimal ubuntu 16.04 image without installing any additional dependencies using `apt`, and without using `Xvfb` to simulate X11.

## Cross compile kaleido for Windows
This will build the `kaleido` application to `repos/build/kaleido_win`, for windows

```
$ docker run -it --privileged --cap-add SYS_ADMIN --cap-add MKNOD --device /dev/fuse -v `pwd`/repos/:/repos  jonmmease/chromium-builder:0.6 /repos/linux_scripts/build_kaleido_win
```


## Update chromium version
To update the version of chromium in the future, the docker image will need to be updated. Follow the instructions for the `DEPOT_TOOLS_COMMIT` and `CHROMIUM_TAG` environment variables in `Dockerfile`.

> Find a stable chromium version tag from https://chromereleases.googleblog.com/search/label/Desktop%20Update. Look up date of tag in GitHub at https://github.com/chromium/chromium/.k
E.g. Stable chrome version tag on 05/19/2020: 83.0.4103.61, set `CHROMIUM_TAG="83.0.4103.61"`
>
> Search through depot_tools commitlog (https://chromium.googlesource.com/chromium/tools/depot_tools/+log) for commit hash of commit from the same day.
E.g. depot_tools commit hash from 05/19/2020: e67e41a, set `DEPOT_TOOLS_COMMIT=e67e41a`

The `CHROMIUM_TAG` environemnt variable must also be updated in the `repos/linux_scripts/checkout_revision` and `repos/mac_scripts/checkout_revision` scripts.

## CMakeLists.txt
The CMakeLists.txt file in `repos/` is only there to help IDE's like `CLion`/`KDevelop` figure out how to index the chromium source tree. It can't be used to actually build chromium. Using this approach, it's possible to get full completion and code navigation from `repos/kaleido/kaleido.cc`
