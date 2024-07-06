# Building Locally

Whats your OS?

### Windows

Isolation seems difficult, probably need to install visual studio + windows SDK to your system. Specific versions depend on which version of Chromium you want to install.

TODO: Add specific instructions for version.

### Linux

Chromium expects to be built in Ubuntu (maybe anything with `apt`?). Recommended to use LXC or docker.

#### Building in Docker

You can use the same docker image we use in circle-ci, which is their convenience image `cimg/python:X.X` on [dockerhub](https://hub.docker.com/r/cimg/python).

Use our convenience script to pull and boot it:

```bash
./toolchain/src/xx-kdocker.sh
## see --help for more advanced usage.
```

### Mac

TODO

# Developing the Toolchain

Bash is dangerous and hard to test, but portable across platforms and flexible, so keep modules as small as possible.

- shellcheck.net
- https://github.com/kward/shunit2

The files in  `toolchain/version_configuration/` are combinations of chromium/depot_tool versions that are known to work.

# Build Scripts

They are all numbered by supposed order and have a verbose --help. These must be cross platform!

- src/00-set_version.sh
- src/01-fetch_tools.sh

There are utility scripts, only guarenteed to work on linux:

- src/xx-make_bin.sh (described below)
- src/xx-all.sh (will run all stages)
- src/xx-template (just a template for writing new stages)
- src/xx-kdocker.sh (see [above](#linux))

These may or may not work on your OS of choice, they will all work on linux.

As well as well commented `toolchain/src/include/` folder.

## Adding Scripts to Path

If you want to be able to run build scripts as commands, like
```bash
set_version -c "108.123.01.2" -d "HEAD"
fetch_tools --verbose --delete-git
```
then you should run `source ./toolschain/src/xx-make_bin.sh`.
