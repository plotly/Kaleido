# Integrating your charting library with kaleido:

## Scope (Plugin) architecture
While motivated by the needs of plotly.py, we made the decision early on to design Kaleido to make it fairly straightforward to add support for additional libraries.  Plugins in Kaleido are called "scopes". For more information, see https://github.com/plotly/Kaleido/wiki/Scope-(Plugin)-Architecture.

## Language wrapper architecture
While Python is the initial target language for Kaleido, it has been designed to make it fairly straightforward to add support for additional languages. For more information, see https://github.com/plotly/Kaleido/wiki/Language-wrapper-architecture.

# Building and Releasing

Kaleido depends on chromium, so building and releasing Kaleido means building chromium. This is a ~18GB download and ultimately ~25GB after build. The compile can take nearly half a day. If the compile throws an error, you can *just find the `ninja` command in the `build_kaleido.[ps1/sh]` script for that platform and resume the compile by running it manually.* This is also a good way to propagate the error that caused the build to fail if the script outputs too much junk after the failure.

**The best strategy is to use a) the last known good build (see below) and if no b) the most updated stable version of chromium.** Old versions of chromium usually need work to build because its own 3rd party dependencies change. That work will have been done for successful builds, but may have become out-of-date. 

However, today (4/20/2024) that is not possible as Kaleido depends on [an API that Chromium deleted after version 108](https://source.chromium.org/chromium/chromium/src/+/69dde6480cf45b1ee6cee9d2a091546bba1022cf). Today's compile is that version 108, from 2023.

## How to build

The directories `repos/win_scripts` `repos/mac_scripts` and `repos/linux_scripts` each contain README.md with specific instructions for preparing a build for that platform. The readme also contains historical notes about a particular build was achieved for a particular chromium version on a particular date.

Here is a summary (since 2024):

| Date      | Chromium Tag   | depot_tools | linux | mac | win | Kaleido Ref |
| --------  | -----------    | ----------- | ----- | --- | --- | ----------- |
| 4/20/2024 | 108.0.5359.125 | f9f61a9d7   |   ❓  |  ❓ |  ✅ |             |

### Preparing a Build

#### Picking a specific chromium version

> Find a stable chromium version tag from https://chromereleases.googleblog.com/search/label/Desktop%20Update. Look up date of associated tag in GitHub at https://github.com/chromium/chromium/
E.g. Stable chrome version tag on 05/19/2020: 83.0.4103.61, set `CHROMIUM_TAG="83.0.4103.61"`
>
> Search through depot_tools commitlog (https://chromium.googlesource.com/chromium/tools/depot_tools/+log) for commit hash of commit from the same day.
E.g. depot_tools commit hash from 05/19/2020: e67e41a, set `DEPOT_TOOLS_COMMIT=e67e41a`

#### What changes to make
Also refer to the README for the specific platform.

In `repos/patches` there are folders by chromium tags and patches for that version of chromium. You might want to look at the README.md for the closest version you're trying to install, and if you see the indicated errors, copy the relevant patch 

## Releasing

Based on how you repaired the build, you may need to make certain modifications to circle-ci.

## CMakeLists.txt
The CMakeLists.txt file in `repos/` is only there to help IDE's like `CLion`/`KDevelop` figure out how to index the chromium source tree. It can't be used to actually build chromium. Using this approach, it's possible to get full completion and code navigation from `repos/kaleido/cc/kaleido.cc` in CLion.
