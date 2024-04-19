# Note: we'd like to set a depot tools commit close to the chromium version
# And we'd like to set DEPOT_TOOLS_UPDATE to 0 so it doesn't update
# But windows now seems to depend on something else that gets pulled in during the update

# Commits
$env:DEPOT_TOOLS_COMMIT=""
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
$env:GCLIENT_PY3=0

$env:DEPOT_TOOLS_UPDATE=1

# Reset to proper commit
# Note: You can clone individual branches/tags but not commits
git reset --hard ${Env:DEPOT_TOOLS_COMMIT}
git clean -ffd
git --no-pager log -2

cd ..\..


