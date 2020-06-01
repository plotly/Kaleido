## Docker container
The docker container contains an Ubuntu 16.04 environment with the dependencies needed to checkout and build the chromium source code

Build container with:

```
$ docker build -t jonmmease/chromium-builder:0.5 -f Dockerfile .
```

## Fetch chromium source code
This will download the full chromium source tree (may take up to 40GB after build steps below) 
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
This will build the `orca_next` application to `repos/src/out/Headless/orca_next`, and bundle shared libraries and fonts.
```
$ docker run -it -v `pwd`/repos/:/repos  jonmmease/chromium-builder:0.5 /repos/build_orca_next
```

## Update chromium version
To update the version of chromium, the docker image will need to be updated. Follow the instructions
for the `DEPOT_TOOLS_COMMIT` and `CHROMIUM_TAG` environment variables. The `CHROMIUM_TAG` environemnt
variable must also be updated in the `repos/checkout_revision` script.

## WIP commands
Test run from vanilla ubuntu 16.04 container
```
docker run -it --env LD_LIBRARY_PATH="/repos/build/orca_next/lib:/repos/build/orca_next/lib/nss" --env FONTCONFIG_PATH=/repos/build/orca_next/etc/fonts  --env XDG_DATA_HOME=/repos/build/orca_next/xdg -v `pwd`/repos/:/repos ubuntu:16.04 /repos/build/orca_next/orca_next --no-sandbox --disable-gpu http://www.plotly.com
```

```
docker run -it -v `pwd`/repos/:/repos ubuntu:16.04 /repos/build/orca_next/orca_next.sh http://www.plotly.com
```

libsqlite3.so.0
