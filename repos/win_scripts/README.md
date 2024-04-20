Read the build notes for whatever version of Chromium you want to build with!

You should have at least 20GB free, compiling takes 6 hours on a 4 core 8GB RAM machine.

## Urgent Todo:

Unlike the rest of the world, windows scripts don't bubble up errors- it is often totally silent.
The windows `ps1` scripts should be improved by occasionally or at least ultimately checking expclitly for failure and manually throwing an error.
Furthermore, `make clean` and `--resume` style logic would be appreciated.

## Preparing a Build

The `/repos/win_scripts/fetch_chromium.ps1` has two environment variables to set the Chromium tag and depot version.

The same script also include a TODO note you need to read.

Head the advice about patches in the main [BUILD_AND_RELEASE.md](../../BUILD_AND_RELEASE.md).

Otherwise, best of luck.

## Building

### Dependencies:

* Visual Studio 2019+ (community edition is fine)
* nodejs 12
* Python 3

See https://chromium.googlesource.com/chromium/src/+/master/docs/windows_build_instructions.md for more possibly more update info about chromium dependencies specifically.


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

The build step will also create the Python wheel under `repos/kaleido/py/dist/`

## Build Notes

### Chromium 108.0.5359.125 on 4/20/2024

The chromium windows instructions asked for the following for x86 and x86_64 architectures.

```
$ PATH_TO_INSTALLER.EXE ^
--add Microsoft.VisualStudio.Workload.NativeDesktop ^
--add Microsoft.VisualStudio.Component.VC.ATLMFC ^
--includeRecommended
```
I found these in the GUI installer for Visual Studio 2022.

Also asked for was:

* Windows 11 SDK version 10.0.22621.2428. This can be installed separately or by checking the appropriate box in the Visual Studio Installer.
* (Windows 11) SDK Debugging Tools 10.0.22621.755 or higher 

> You may also have to set variable vs2022_install to your installation path of Visual Studio 2022, like set vs2022_install=C:\Program Files\Microsoft Visual Studio\2022\Professional.

However, since I was intending to install a verison a year older than the date of thos instructions, I had to install windows 10 sdk version 10.0.20348.0. [Microsoft SDK-Archive](https://developer.microsoft.com/en-us/windows/downloads/sdk-archive/).

I didn't want to install all the options, but I did have to install the debugging tools and the stuff marked as Desktop Apps. Visual Studio has the option to install it as well but it misses the debugging tools and therefore doesn't work.
