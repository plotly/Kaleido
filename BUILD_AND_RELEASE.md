# Integrating your charting library with kaleido:

## Scope (Plugin) architecture
While motivated by the needs of plotly.py, we made the decision early on to design Kaleido to make it fairly straightforward to add support for additional libraries.  Plugins in Kaleido are called "scopes". For more information, see https://github.com/plotly/Kaleido/wiki/Scope-(Plugin)-Architecture.

## Language wrapper architecture
While Python is the initial target language for Kaleido, it has been designed to make it fairly straightforward to add support for additional languages. For more information, see https://github.com/plotly/Kaleido/wiki/Language-wrapper-architecture.

# Building and Releasing

Kaleido depends on building chromium: an ~18GB download, ~25GB after the half-day compile.

**Good strategies:**

1. the latest known good build (see below) OR
2. the most updated stable version of chromium

Third party dependencies are always in flux and no build is guarenteed to succeed at any point without work.

However, today (4/20/2024) Kaleido uses an [API that Chromium deleted after version 108](https://source.chromium.org/chromium/chromium/src/+/69dde6480cf45b1ee6cee9d2a091546bba1022cf). Furthermore, it appears that the API degraded to be unusable before it was removed.

## How to build

Tip! Set environmental variable cpus! It defaults at 4.

```
# Powershell
$env:cpus = 8
# Bash
export cpus = 8
```

After reading this, refer to:

* [win README.md](repos/win_scripts/README.md)
* [mac README.md](repos/mac_scripts/README.md)
* [linux README.md](repos/linux_scripts/README.md)

Bottom line, the operating systems and chromium change over time, and no formerly successful build is guarenteed. You can try running the scripts, but you may end up reading these notes in detail, especially "Preparing a Build". :-).

Here is a summary (since 2024) of successes:

| Date      | Chromium Tag                                                                                                                                                                                           | depot_tools | linux | mac | win | K. CC  | Kaleido | Notes                          |
| --------  | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------- | ----- | --- | --  |------- | ------ |  ----------------------------- |
| 4/20/2024 | [108.0.5359.125](https://chromium.googlesource.com/chromium/src/+/refs/tags/108.0.5359.125) [(docs)](https://chromium.googlesource.com/chromium/src/+/refs/tags/108.0.5359.125/docs/)                  | f9f61a9d7   |   ❓  |  ❓ |  ❓ | cc-1.5 |        |  Runtime errors likely due to old API degredation |
| 4/21/2024 | [88.0.4324.150](https://chromium.googlesource.com/chromium/src/+/refs/tags/88.0.4324.150) [(docs)](https://chromium.googlesource.com/chromium/src/+/refs/tags/88.0.4324.150/docs/)                     | f9f61a9d7   |   ❓  |  ❓ | ✅* | cc     | 19d0ee00 | |


_* builds but locally, no circle ci integration_

### Preparing a Build

OS-specific README's tell you to specify a chromium version (and depot tools version).

#### Picking a specific chromium version
From old README.md/Google:
> Find a stable chromium version tag from https://chromereleases.googleblog.com/search/label/Desktop%20Update. Look up date of associated tag in GitHub at https://github.com/chromium/chromium/
E.g. Stable chrome version tag on 05/19/2020: 83.0.4103.61, set `CHROMIUM_TAG="83.0.4103.61"`
>
> Search through depot_tools commitlog (https://chromium.googlesource.com/chromium/tools/depot_tools/+log) for commit hash of commit from the same day.
E.g. depot_tools commit hash from 05/19/2020: e67e41a, set `DEPOT_TOOLS_COMMIT=e67e41a`
#### Picking a cc version

The c++ for Kaleido has to be updated sometimes based on the chromium version. The platform README.md will tell you what variables to change for that. The [repos/kaleido/REAMDE-CC.md](repos/kaleido/README-CC.md) contains some information about the difference between the versions, so you can cross reference errors and that, maybe. Otherwise you need serious git-fu + code note research to get a handle on Google's unstable API.

#### Patching

In `repos/patches` there are folders by chromium tags and patches for that version of chromium. You might want to look at the README.md for the closest version you're trying to install, and if you see the indicated errors, copy the relevant patch into a folder named after whatever chromium tag you're trying to run.

#### Copying Run-Time Dependencies

Hopefully your executable doesn't need any `.dll` or `.so` that weren't compiled in as `.lib` or `.a` respectively. Linux and git bash can use `ldd` to resolve dependencies of an `elf` or `exe`, mac has the less powerful `otool -L`. That should let you know if you need to bring any deps with you into the wheel, but theoretically it could be fooled by a dynamic load... (and it currently is). This is because headless chromium is dependent on `swiftshader` since for whatever reason it doesn't support GPU rendering.

## Releasing

Based on how you prepaired the build, you may need to make certain modifications to circle-ci.

## CMakeLists.txt
The CMakeLists.txt file in `repos/` is only there to help IDE's like `CLion`/`KDevelop` figure out how to index the chromium source tree. It can't be used to actually build chromium. Using this approach, it's possible to get full completion and code navigation from `repos/kaleido/cc/kaleido.cc` in CLion.
