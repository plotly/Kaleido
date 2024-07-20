This directory is used by `10-extract.sh` and it's subscript, `10-extract_subscript.py`.


Chromium documents the files necessary for building installers in `src/infra/archive_config/*.json`.

When releasing a new version of Kaleido, we

a) See if their configuration has changed at all (if it has 10-extract wil fail and you will have to do this process).
b) Modify the new config if we don't need all the same files or need to change names.
-- What should you modify? That's a tougher question... trial and error.
c) Save the original config and the modification as a patch.

Even if a new version of chromium can use the older version's, it is recommended you create a new version folder identical
to the old so as to be explicit about that fact.

Furthermore, the `10-extract.sh `script should be dry run before any build so as not to fail a continuous integration run at
this late, trivial stage.
