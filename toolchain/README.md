# Developing the Toolchain

Bash is dangerous and hard to test, but portable across platforms and flexible, so keep modules as small as possible.

- shellcheck.net
- https://github.com/kward/shunit2

The files in  `toolchain/version_configuration/` are combinations of chromium/depot_tool versions that are known to work.

# Build Scripts

They are all numbered by supposed order and have a verbose --help.

- stages/00-set_version.sh
- stages/01-fetch_tools.sh

There are utility scripts:

- stages/xx-make_bin.sh (described below)
- stages/xx-all.sh (will run all stages)
- stages/xx-template (just a template for writing new stages)

As well as well commented `toolchain/stages/include/` folder.

## Adding Scripts to Path

If you want to be able to run build scripts as commands, like
```bash
set_version -c "108.123.01.2" -d "HEAD"
fetch_tools --verbose --delete-git
```
then you should run `source ./toolschain/stages/xx-make_bin.sh`.
