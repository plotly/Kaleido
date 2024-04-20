# Commits
$env:DEPOT_TOOLS_COMMIT="f9f61a9d7c0c76a71dc1db860d1994c53c8aa148"
$env:CHROMIUM_VERSION_TAG="108.0.5359.125"
# requires windows 10 sdk version 10.0.20348.0 which,\
# durng vs community install, can be included by going to
# "visual studio community: 2023" --> "individual components"

# Tell gclient to use local Vistual Studio install
$env:DEPOT_TOOLS_WIN_TOOLCHAIN=0

# cd to repos directory
cd repos

# Get depot_tools
git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git
cd depot_tools


git reset --hard ${env:DEPOT_TOOLS_COMMIT}
git clean -ffd

# GCLIENT_PY3 was experimental when this was configured
$env:GCLIENT_PY3=0

# Add cloned depot_tools directory to PATH
$env:path = "$pwd;$pwd\bootstrap;$env:path"
echo $env:path

# Reset to proper commit
git --no-pager log -2


# TODO: READ IF UPDATING (not actually a TODO, just a highlight to attract your attention)
# This will turn off auto-update so we can stick with the version we picked
$env:DEPOT_TOOLS_UPDATE=0
# However, the .\update_dpot_tools.bat file which we don't want to run also has two calls at the end
# which we do need to run! Google design flaw.
cmd.exe /c call "%~dp0\cipd_bin_setup.bad"
cmd.exe /c call "%~dp0\bootstrap\win_tools.bad"
# If you're updating the DEPOT_TOOLS_COMMIT, you should read the skipped bat file to make sure you're doing
# the init steps like above and whatever else, but not updating git!

cd ..

cmd.exe /c gclient sync -D --force --reset --no-history --jobs=3 --revision=%CHROMIUM_VERSION_TAG% 
# google wants cmd.exe not powershell
# cmd not strictly necessary as gclient is a .bat that invokes cmd intrinsically but better safe than sorry

cd src
# Append kaleido section to headless build file (src\headless\BUILD.gn)
cat ..\win_scripts\build_target.py | Add-Content -Path .\headless\BUILD.gn

## Write out credits
python3 ..\src\tools\licenses\licenses.py credits *> ..\CREDITS.html

## Go back to root directory
cd ..\..




