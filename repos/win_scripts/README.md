Read the build notes for whatever version of Chromium you want to build with!

You should have at least 20GB free, compiling takes 6 hours on a 4 core 8GB RAM machine.

## Preparing a Build

The `/repos/win_scripts/fetch_chromium.ps1` has two environment variables to set the Chromium tag and depot version.

The same script also include a TODO note you need to read.

Heed the advice about patches in the main [BUILD_AND_RELEASE.md](../../BUILD_AND_RELEASE.md).

Otherwise, best of luck.

## Building

### Dependencies:

* Visual Studio 2019+ (community edition is fine) 
* nodejs 12
* Python 3

_NB: Go to the chromium repo online, the correct tag, the docs/ folder, and look for windows build instructions for specific version information_

### Run Scripts:
```
$ /repos/win_scripts/fetch_chromium.ps1
```

Then build Kaleido to `repos/build/kaleido`. 
```
# For a 64-bit build
$ /repos/win_scripts/build_kaleido.ps1 x64
# Or, for a 32-but build
$ /repos/win_scripts/build_kaleido.ps1 x86
```

You can add `--from-ninja` to resume from a compile error.

The build step will also create the Python wheel under `repos/kaleido/py/dist/`

## Build Notes

### Chromium 108.0.5359.125 on 4/20/2024

Docs ask for:

* Windows 11 SDK version 10.0.22621.2428. This can be installed separately or by checking the appropriate box in the Visual Studio Installer.
* (Windows 11) SDK Debugging Tools 10.0.22621.755 or higher 

You can do that through Visual Studio Installer + Windows control panel to activate the debugger, but I find it easier to just install from here using checkboxes: [Microsoft SDK-Archive](https://developer.microsoft.com/en-us/windows/downloads/sdk-archive/).

I didn't want to install all the options, but I did have to install the debugging tools and the stuff marked as Desktop Apps. Visual Studio has the option to install it as well but it misses the debugging tools and therefore doesn't work (unless control panel modifications).

### Chromium 88.0.4324.150 on 4/21/2024

In addition to the normal stuff, I had to go to Visual Studio Installer, Build Tools-->Modify, search and install ATL.