# Commits
$env:DEPOT_TOOLS_COMMIT="36a0bee"
$env:CHROMIUM_VERSION_TAG="88.0.4324.150"

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

# Reset to proper commit
git reset --hard ${Env:DEPOT_TOOLS_COMMIT}
git --no-pager log -2

# Move back to repos directory + download tarball
echo "Downloading..."
cd ..
$ProgressPreference = 'SilentlyContinue'
Invoke-WebRequest -Uri ${Env:TAR_URL} -OutFile "${Env:CHROMIUM_VERSION_TAG}.tar.gz"
mkdir src
cd src
tar -xvzf ..\${Env:CHROMIUM_VERSION_TAG}.tar.gz

# Change to cloned src/ directory
gclient sync -D --force --reset
gclient runhooks

# 2) Append kaleido section to headless build file (src\headless\BUILD.gn)
cat ..\win_scripts\build_target.py | Add-Content -Path .\headless\BUILD.gn

## Write out credits
python ..\src\tools\licenses.py credits > ..\CREDITS.html

# Delete .git directory to save some space
# TODO: also delete third-part .git directories
Remove-Item -Recurse -Force .git
