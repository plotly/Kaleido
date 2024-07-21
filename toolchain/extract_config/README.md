This directory is used by `10-extract.sh` and it's subscript, `10-extract_subscript.py`.


Chromium documents the files necessary for building installers in `src/infra/archive_config/*.json`.

We make copies of them and add -original

If this project were to survive, a diffing mechanism on more than just these files (like BUILD.gn and arg.gn) would make transitions nicer.
