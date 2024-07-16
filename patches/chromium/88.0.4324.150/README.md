# build/compute_build_timestamp.py

Google has a complex way to embed a timestamp into all of their source files and libraries. It has to do with cache optimization and symbol lookup for proprietary servers they have. It didn't work in 2024 and their most recent build (which we can't use yet) doesn't even have this file. But I just replace the file with a simple timestamp since that's suitable for Kaleido's purposes.


# build/toolchain/win/setup_toolchain.py

This version was released before the Spectre vulnerability was patched. The spectre-mitigation libraries are in a folder that the build system doesn't include in the `-libpath` set for the linkers. I've added that folder to the build flags manually. Google's linker-command generation system is insanely complicated. My patch is in the correct area but it hardcodes the directory (Google somehow determines it through 10000 lines of obtuse python) which corresponds to the version of the Windows SDK you had to install. Not the best but not bad. If this is copied to other versions, and you still get can't find `atls.lib`, use this patch but change the x.y.z version number on the `lib = [path] + lib` line.
