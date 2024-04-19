# Change to cloned src/ directory
cd repos\src
gclient sync -D --force --reset --no-history --jobs=3 --with-tags
gclient runhooks
cd ..\..
