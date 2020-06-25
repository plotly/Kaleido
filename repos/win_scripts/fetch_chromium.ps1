# Commits
$DEPOT_TOOLS_COMMIT="e67e41a"
$CHROMIUM_TAG="83.0.4103.61"

# Tell gclient not to update depot_tools
$env:DEPOT_TOOLS_UPDATE=0
# Tell gclient to use local Vistual Studio install
$env:DEPOT_TOOLS_WIN_TOOLCHAIN=0

# cd to repos directory
cd repos

# Get depot_tools
git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git
cd depot_tools

# Add cloned depot_tools directory to PATH
$env:path = "$pwd;$pwd\bootstrap-3_8_0_chromium_8_bin\python\bin;$env:path"
echo $env:path
$env:GCLIENT_PY3=0

# Reset to proper commit
git reset --hard $DEPOT_TOOLS_COMMIT
git log -2

# Move back to repos directory
cd ../
fetch --nohooks chromium

# Change to cloned src/ directory
cd src
git reset --hard
git checkout tags/$CHROMIUM_TAG
git log -2
gclient sync -D --force --reset
gclient runhooks

# 2) Append kaleido section to headless build file (src\headless\BUILD.gn)
cat ..\win_scripts\build_target.py | Add-Content -Path .\headless\BUILD.gn

# Delete .git directory to save some space
# TODO: also delete third-part .git directories
Remove-Item -Recurse -Force .git
