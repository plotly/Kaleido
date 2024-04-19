# Note: we'd like to set a depot tools commit close to the chromium version
# And we'd like to set DEPOT_TOOLS_UPDATE to 0 so it doesn't update
# But windows now seems to depend on something else that gets pulled in during the update

# Commits
$env:DEPOT_TOOLS_COMMIT="" # See Note: above
$env:CHROMIUM_VERSION_TAG="124.0.6367.60"

# Tell gclient to use local Vistual Studio install
$env:DEPOT_TOOLS_WIN_TOOLCHAIN=0

# cd to repos directory
cd repos

# Get depot_tools
git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git
cd depot_tools

# Add cloned depot_tools directory to PATH
$env:path = "$pwd;$pwd\bootstrap;$env:path"
echo $env:path

# GCLIENT_PY3 was experimental when this was configured
$env:GCLIENT_PY3=0

# See Note: above
#$env:DEPOT_TOOLS_UPDATE=1

# Reset to proper commit
# Note: You can clone individual branches/tags but not commits
git reset --hard ${Env:DEPOT_TOOLS_COMMIT}
git clean -ffd
git --no-pager log -2

cd ..

cmd.exe /c gclient sync -D --force --reset --no-history --jobs=3 --revision=%CHROMIUM_VERSION_TAG% # google wants gclient run from cmd, no ps

cd src
# Append kaleido section to headless build file (src\headless\BUILD.gn)
cat ..\win_scripts\build_target.py | Add-Content -Path .\headless\BUILD.gn

## Write out credits
python3 ..\src\tools\licenses\licenses.py credits *> ..\CREDITS.html

## Go back to root directory
cd ..\..




