# Commits
$env:DEPOT_TOOLS_COMMIT="1dae848"
$env:CHROMIUM_VERSION_TAG="124.0.6367.60"

$env:TAR_URL="https://chromium.googlesource.com/chromium/src.git/+archive/refs/tags/${Env:CHROMIUM_VERSION_TAG}.tar.gz"
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

# We're checking out a specific commit, don't autoupdate
$env:DEPOT_TOOLS_UPDATE=0

# Reset to proper commit
# Note: You can clone individual branches/tags but not commits
git reset --hard ${Env:DEPOT_TOOLS_COMMIT}
git clean -ffd
git --no-pager log -2

# Move back to repos directory + download tarball
echo "Downloading..."
cd ..
$ProgressPreference = 'SilentlyContinue'
Invoke-WebRequest -Uri ${Env:TAR_URL} -OutFile "${Env:CHROMIUM_VERSION_TAG}.tar.gz"
mkdir src
cd src
tar -xzf ..\${Env:CHROMIUM_VERSION_TAG}.tar.gz
cd ..\..


# gclient may not like it not having a .git
