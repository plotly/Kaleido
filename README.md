# Overview
Kaleido is a cross-platform library for generating static images (e.g. png, svg, pdf, etc.) for web-based visualization libraries, with a particular focus on eliminating external dependencies. The project's initial focus is on the export of plotly.js images from Python for use by plotly.py, but it is designed to be relatively straight-forward to extend to other web-based visualization libraries, and other programming languages.  The primary focus of Kaleido (at least initially) is to serve as a dependency of web-based visualization libraries like plotly.py. As such, the focus is on providing a programmatic-friendly, rather than user-friendly, API.


# Background
As simple as it sounds, programmatically generating static images from web-based visualization libraries is a difficult problem.  The core difficulty is that these libraries don't actually render plots (i.e. color the pixels) on their own, instead they delegate this work to web technologies like SVG, Canvas, WebGL, etc.  This means that they are entirely dependent on the presence of a complete web browser to operate.

When the figure is displayed in a browser window, it's relatively straight-forward for a visualization library to provide an export-image button because it has full access to the browser for rendering.  The difficulty arises when trying to export an image programmatically (e.g. from Python) without displaying it in a browser and without user interaction.  To accomplish this, the Python portion of the visualization library needs programmatic access to a full web browser.

There are three main approaches that are currently in use among the Python web-based visualization libraries.

  1. bokeh, altair, bqplot, and ipyvolume rely on the Selenium Python library to control a system web browser such as Firefox or Chrome/Chromium to perform image rendering.
  2. plotly.py relies on Orca, which is a custom headless Electron application that uses the Chromium browser engine built into Electron to perform image rendering. Orca runs as a local web server and plotly.py sends requests to it using a local port.
  3. When operating in the Jupyter notebook or JupyterLab, ipyvolume also supports programmatic image export by sending export requests to the browser using the ipywidgets protocol.
  
While options 1 and 2 can both be installed using `conda`, they still rely on the presence of some components that must be installed externally. For example, on Linux both require the installation of system libraries like `libXss` that are not typically included in headless Linux installations like you find in JupyterHub installations, Binder, Colab, Azure notebooks, SageMaker, etc.  Also, conda is not as universally available as the pip package manager and neither approach is installable using pip packages.

Additionally, both 1 and 2 communicate between the Python process and the web browser over a local network port. While not typically a problem, certain firewall and container configurations can interfere with this local network connection.

The advantage of options 3 is that it introduces no additional system dependencies. The disadvantage is that it only works when running in a notebook, not in standalone Python scripts.

The end result is that all of these libraries have in-depth documentation pages on how to get image export working, and how to troubleshoot the inevitable failures and edge cases. While this is a great improvement over the state of affairs just a couple of years ago, and a lot of excellent work has gone into making these approaches work as seamlessly as possible, the fundamental limitations detailed above still result in sub-optimal user experiences. This is especially true when comparing web-based plotting libraries to traditional plotting libraries like matplotlib and ggplot2 where there's never a question of whether image export will work

The goal of Kaleido is to make static image export of web-based visualization libraries as universally available and reliable as that of matplotlib and ggplot2.

# Approach
To accomplish this goal, Kaleido introduces a new approach.  The core of Kaleido is a standalone C++ application that embeds Chromium as a library. This architecture allows Kaleido to communicate with the browser engine using the C++ API rather than requiring a local network connection. A thin Python wrapper runs the Kaledo C++ application as a subprocess and communicates with it by writing image export JSON requests to standard-in and retrieving results by reading from standard-out.  Other language wrappers (e.g. R, Julia, Scala, Rust, etc.) can fairly easily be written in the future because the interface relies only on standard-in / standard-out communication using JSON requests.

By compiling Chromium as a library, we have a degree of control over what is included in the Chromium build. In particular, on Linux we can build Chromium in [headless](https://chromium.googlesource.com/chromium/src/+/lkgr/headless/README.md#usage-as-a-c_library) mode, which eliminates a large number of runtime dependencies (e.g. the `libXss` library mentioned above).  The remaining dependencies are small enough to bundle with the library, making it possible to run Kaleido in the most minimal Linux environments with not additional dependencies required. So for example, the c++ Kaleido executable can run inside an `ubuntu:16.04` docker container without anything be installed using `apt`.

The Python wrapper and the Kaleido executable can then be packaged as operating system dependent Python wheels that can be distributed on PyPI.

# Disadvantages
While this approach has many advantages, the main disadvantage is that building Chromium is not for the faint of heart.  Even on powerful workstations, downloading and building the Chromium code base takes 50+ GB and several hours.  Because of this, on Linux this work can be done once and distributed as a docker container, but we don't have a similar shortcut for Windows and MacOS. Because of this, we're still working on finding a CI solution for MacOS and Windows.

# Scope (Plugin) architecture
While motivated by the needs of plotly.py, we made the decision early on to design Kaleido to make it fairly straightforward to add support for additional libraries.  Plugins in Kaleido are called "scopes". We hope to collaborate with many other web-based visualization libraries to solve this problem once as for all by developing scopes for a wide range of libraries across the community.


# Building Kaledo
Instructions for building Kaleido differ slightly across operating systems.  All of these approaches assume that the Kaleido repository has been cloned and that the working directory is set to the repository root.

```
$ git clone git@github.com:plotly/Kaleido.git
$ cd Kaleido
```

## Linux
There are two approaches to building Kaleido on Linux, both of which rely on Docker.

## Method 1
This approach relies on the `jonmmease/kaleido-builder` docker image, and the scripts in `repos/linux_full_scripts`, to compile Kaleido.  This docker image is over 30GB, but in includes a precompiled instance of the Chromium source tree making it possible to compile Kaleido in just a few 10s of seconds. The downside of this approach is that the chromium source tree is not visible outside of the docker image so it may be difficult for development environments to index it. This is the approach used for Continuous integration on Linux 

Download docker image
```
$ docker pull jonmmease/kaleido-builder:0.6
```

Build Kaleido

```
$ docker run -it -v `pwd`/repos/:/repos  jonmmease/kaleido-builder:0.6 /repos/linux_full_scripts/build_kaleido
```

### Method 2
This approach relies on the `jonmmease/chromium-builder` docker image, and the scripts in `repos/linux_scripts`, to download the chromium source to a local folder and then build it.  This takes longer to get set up than method 2 because the Chromium source tree must be compiled from scratch, but it downloads a copy of the chromium source tree to `repos/src` which makes it possible for development environments like CLion to index the Chromium codebase to provide code completion.

Download docker image
```
$ docker pull jonmmease/chromium-builder:0.6
```

Fetch the Chromium codebase

```
$ docker run -it -v `pwd`/repos/:/repos  jonmmease/chromium-builder:0.6 /repos/linux_scripts/fetch_chromium
```

Checkout the specific stable tag of chromium, and then sync all dependencies
```
$ docker run -it -v `pwd`/repos/:/repos  jonmmease/chromium-builder:0.6 /repos/linux_scripts/checkout_revision
```

Then build the `kaleido` application to `repos/build/kaleido`, and bundle shared libraries and fonts. The input source for this application is stored under `repos/kaleido/cc/`. The build step will also
create the Python wheel under `repos/kaleido/py/dist/`

```
$ docker run -it -v `pwd`/repos/:/repos  jonmmease/chromium-builder:0.6 /repos/linux_scripts/build_kaleido
```

## MacOS
To build on MacOS, first install XCode version 11.0+ and nodejs 12.  See https://chromium.googlesource.com/chromium/src/+/master/docs/mac_build_instructions.md for more information on build requirements.

Then fetch the chromium codebase

```
$ /repos/mac_scripts/fetch_chromium
```

Then build Kaleido to `repos/build/kaleido`. The build step will also create the Python wheel under `repos/kaleido/py/dist/`

```
$ /repos/mac_scripts/build_kaleido
```

## Windows
To build on Windows, first install Visual Studio 2019 (community edition is fine). See https://chromium.googlesource.com/chromium/src/+/master/docs/windows_build_instructions.md for more information on build requirements.

Then fetch the chromium codebase from a Power Shell command prompt

```
$ /repos/win_scripts/fetch_chromium.ps1
``` 

Then build Kaleido to `repos/build/kaleido`. The build step will also create the Python wheel under `repos/kaleido/py/dist/`
```
$ /repos/mac_scripts/build_kaleido.ps1
```

# Scope architecture
This section describes the current requirements for adding a new scope for a new visualization library. This section will assume that the new library is named superviz.

## repos/kaleido/py/kaleido/scopes/superviz.py
First add a new Python class named `SupervizScope` to a new file at `repos/kaleido/py/kaleido/scopes/superviz.py`. This class should subclass `BaseScope`. It must implement the constructor and override the `scope_name` property to return the string `'superviz'`.  The constructor should accept and validate any global configuration values the library needs. In particular, this may include the path/URL of the `superviz.js` library.

See `repos/kaleido/py/kaleido/scopes/plotly.py` for a reference example.

## repos/kaleido/cc/scopes/Superviz.h
Next, add a new `SupervizScope` C++ class to a new file at `repos/kaleido/cc/scopes/Superviz.h`. This class should subclass the `BaseScope`. It must override the `ScopeName` method to return the string `"superviz"`. In the constructor, it should look for command-line switches that correspond to the global configuration values above. These switches will have identical names to the Python variables defined above, but with underscores replaced by hyphens. The `scriptTags` list property should be updated with the `<script>` tag URLs that should be included in the initial HTML document.  The `localScriptFiles` list property should be updated with the paths of local JavaScript files to load dynamically after the initial HTML document has been loaded.

It must also override the `BuildCallArguments` method. This method is responsible for returning a `std::vector` of chromium `CallArguments`. These should correspond to the same global configuration parameters, but here the order is significant, so choose an order here that matches the argument order of the JavaScript `render` method described below.

See `repos/kaleido/cc/scopes/Plotly.h` for a reference example.

## repos/kaleido/cc/scopes/Factory.h
Update the `LoadScope` function in `repos/kaleido/cc/scopes/Factory.h` so that an instance of the `SupervizScope` class is returned when the input string is `"superviz"`.

## repos/kaleido/js/src/superviz/render.js
Next, add a new `render` JavaScript function to a new file at `repos/kaleido/js/src/superviz/render.js`.  The first argument of this function will be a JavaScript object that corresponds to the arguments to the `BaseScope.to_image` Python method: `figure`, `format`, `width`, `height`, and `scale`. The second through last argument will match the arguments constructed in the `BuildCallArguments` C++ method above.

This function is responsible for return a `Promise` that resolves to an object that includes the result of the image export attempt. The object should have the following properties
 
  - `code`: If an error occurred, the code should be a non-zero integer and an associated `message` should be included that describes the error. If export was successful, `code` should be `null`
  - `message`: If an error occurred, this should be a string containing the error message. If export was successful, `message` should be `null`
  - `result`: The image export result. All formats except `svg` should be base64 encoded. If the input format is `pdf`, then the `render` function should choose the most appropriate image format that will be embedded in pdf (e.g. `svg`) and instead of returning a `result`, it should set this image as the `src` property of the `<img>` tag with id `kaleido-image`.
  - `format`, `width`, `height`, `scale`: The format, width, height, and scale factor that were used. Even though these values are inputs, the `render` function may supply its own defaults and whatever values were actually used to generate the image should be included here. If the input format was `pdf`, then this `format` returned here should be whatever image format was used to generate the image that will be embedded in the PDF. e.g. `svg`.
  - `pdfBgColor`: If the `format` is `pdf`, this property should contain the desired background color of the figure. It is recommended that, if possible, the background color the associated figure image be set to fully transparent so that the PDF background color will fully show through. If `format` was not PDF this property should be set to `null`.
  

Additional JavaScript helper functions can be added to the `repos/kaleido/js/src/superviz/` directory. The JavaScript files are bundled using [`browserify`](http://browserify.org/) on build. Additional NPM dependencies can be added to `repos/kaleido/js/package.json`. Note that the visualization library itself shouldn't be added as an NPM dependency, this is because we want to keep the resulting JavaScript bundle as small as possible, and we don't want to have to release a new version of Kaleido for each release of various visualization libraries.  Instead, the visualization libraries should be loaded from a CDN url by default and added to `scriptTags` above. It is also helpful to support loading the visualization library from a local JavaScript file, adding the path to `localScriptFiles` instead.


## repos/kaleido/js/src/index.js
Update the `module.exports` section of `repos/kaleido/js/src/index.js` to include `superviz: require("./superviz/render")`.


# Language wrapper architecture
This section provides a high-level overview of the interactions between the Python and C++ layers.

The first time an image export request is made in the Python library, the Kaleido C++ executable is launched as a subprocess of the Python interpreter. The first, and only, positional argument should be the scope name.  After that, a series of flags of the form `--flag` are passed to the executable. These flags would correspond to the constructor arguments of the `SupervizScope` python class.

When construction is complete, the Kaledo executable will write a single line to std-out. This is a JSON string with `code` and `message` properties. If initialization was successful, `code` is 0 and `message` is `null`.  If something went wrong (e.g. a validation failure), then the `code` will be a non-zero integer and an error `message` will be included.  In this case, the Python layer will raise a `ValueError` with the returned `message`.

Each time an image export request is made of the Python library, a request JSON string is formed and written to standard-in, followed by a newline. This JSON string should contain the figure specification in the `figure` property, as well as `format`, `width`, `height`, `scale` options.  In response, the Kaleido C++ executable will write a single JSON string to standard out.  This JSON string also has the `code` and `message` properties. Again, if something went wrong, `code` will be non-zero and the `message` will describe the problem. And again, the Python layer will raise a `ValueError` with the contents of the message.  If `code` is 0, then the `result` property will contain the image data, which is returned by the Python layer as a `bytes` object.


# Building Docker containers
## chromium-builder
The `chromium-builder` container mostly follows the instructions at https://chromium.googlesource.com/chromium/src/+/master/docs/linux/build_instructions.md to install `depot_tools` and run `install-build-deps.sh` to install the required build dependencies the appropriate stable version of Chromium. The image is based on ubuntu 16.04, which is the recommended OS for building Chromium on Linux.

Build container with:

```
$ docker build -t jonmmease/chromium-builder:0.6 -f repos/linux_scripts/Dockerfile .
```

## kaleido-builder
This container contains a pre-compiled version of chromium source tree. Takes several hours to build!

```
$ docker build -t jonmmease/kaleido-builder:0.6 -f repos/linux_full_scripts/Dockerfile .
```


# Updating chromium version
To update the version of Chromium in the future, the docker images will need to be updated. Follow the instructions for the `DEPOT_TOOLS_COMMIT` and `CHROMIUM_TAG` environment variables in `linux_scripts/Dockerfile`.

> Find a stable chromium version tag from https://chromereleases.googleblog.com/search/label/Desktop%20Update. Look up date of associated tag in GitHub at https://github.com/chromium/chromium/
E.g. Stable chrome version tag on 05/19/2020: 83.0.4103.61, set `CHROMIUM_TAG="83.0.4103.61"`
>
> Search through depot_tools commitlog (https://chromium.googlesource.com/chromium/tools/depot_tools/+log) for commit hash of commit from the same day.
E.g. depot_tools commit hash from 05/19/2020: e67e41a, set `DEPOT_TOOLS_COMMIT=e67e41a`

The environment variable must also be updated in the `repos/linux_scripts/checkout_revision`, `repos/mac_scripts/fetch_chromium`, and `repos/win_scripts/fetch_chromium.ps1` scripts.

# CMakeLists.txt
The CMakeLists.txt file in `repos/` is only there to help IDE's like `CLion`/`KDevelop` figure out how to index the chromium source tree. It can't be used to actually build chromium. Using this approach, it's possible to get full completion and code navigation from `repos/kaleido/kaleido.cc` in CLion.
