## WIP orca_next prototype
This is a WIP towards the goal of being able to perform plotly image export from any relatively modern Linux distribution ((Ubuntu 16.04+, Centos 7+, etc.) without any external dependencies.

Rather than buiding on Electron, this idea here is to create a custom, stripped down, build of Chromium headless and then
bundle the necessary shared objects files, fonts, config, etc.

The Chromium source tree includes a minimal [`headless_example`](https://chromium.googlesource.com/chromium/src/+/lkgr/headless/README.md#usage-as-a-c_library) that we'll use as the starting point for `orca_next`. So far, this repo is focused on scripting a reproducible workflow for building a custom `orca_next.cc` file that has identical functionality to `headless_example`, and bundling dependencies.


## Docker container
First, create a docker container that is configured to download and build the chromium source tree.  This mostly follows the instructions at https://chromium.googlesource.com/chromium/src/+/master/docs/linux/build_instructions.md to install `depot_tools` and run `install-build-deps.sh` to install the required build dependencies the appropriate stable version of Chromium. The image is based on ubuntu 16.04, which is the recommended OS for building Chromium on Linux.

Build container with:

```
$ docker build -t jonmmease/chromium-builder:0.5 -f Dockerfile .
```

## Fetch chromium source code
This will download the full chromium source tre. **Caution**: This may take up to 40GB after build steps below
```
$ docker run -it -v `pwd`/repos/:/repos  jonmmease/chromium-builder:0.5 /repos/fetch_chromium
```

## Checkout tag
This will checkout a specific stable tag of chromium, and then sync all dependencies
```
$ docker run -it -v `pwd`/repos/:/repos  jonmmease/chromium-builder:0.5 /repos/checkout_revision
```

## Build chromium headless
This will build the `headless_example` application to `repos/src/out/Headless/headless_example`
```
$ docker run -it -v `pwd`/repos/:/repos  jonmmease/chromium-builder:0.5 /repos/build_headless
```

## Build orca_next
This will build the `orca_next` application to `repos/build/orca_next`, and bundle shared libraries and fonts. The input source for this application is in `repos/orca_next/orca_next.cc`.  Right now, this is identical to `headless_example`.

```
$ docker run -it -v `pwd`/repos/:/repos  jonmmease/chromium-builder:0.5 /repos/build_orca_next
```

To run the orca_next application, use the `/repos/build/orca_next/orca_next` bash script. This passes argumnets through to the `repos/build/orca_next/bin/orca_next` executable, but it also sets up the environment needed to use the bundled shared libraries, fonts, etc.

If you're running Linux locally, try it out on your local linux install with:

```
repos/build/orca_next/orca_next http://www.plotly.com
```

You can try it out on in a raw ubuntu:16.04 docker image with:

```
docker run -it -v `pwd`/repos/:/repos ubuntu:16.04 /repos/build/orca_next/orca_next http://www.plotly.com
```

This shows that we were able to invoke chromium on the most minimal ubuntu 16.04 image without installing any additional dependencies using `apt`, and without using `Xvfb` to simulate X11.

## Update chromium version
To update the version of chromium in the future, the docker image will need to be updated. Follow the instructions for the `DEPOT_TOOLS_COMMIT` and `CHROMIUM_TAG` environment variables in `Dockerfile`.

> Find a stable chromium version tag from https://chromereleases.googleblog.com/search/label/Desktop%20Update. Look up date of tag in GitHub at https://github.com/chromium/chromium/.k
E.g. Stable chrome version tag on 05/19/2020: 83.0.4103.61, set `CHROMIUM_TAG="83.0.4103.61"`
>
> Search through depot_tools commitlog (https://chromium.googlesource.com/chromium/tools/depot_tools/+log) for commit hash of commit from the same day.
E.g. depot_tools commit hash from 05/19/2020: e67e41a, set `DEPOT_TOOLS_COMMIT=e67e41a`

The `CHROMIUM_TAG` environemnt variable must also be updated in the `repos/checkout_revision` script.

## CMakeLists.txt
The CMakeLists.txt file in `repos/` is only there to help IDE's like `CLion`/`KDevelop` figure out how to index the chromium source tree. It can't be used to actually build chromium. Using this approach, it's possible to get full completion and code navigation from `repos/orca_next/orca_next.cc`
