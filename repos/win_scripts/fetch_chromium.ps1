# Commits
$env:DEPOT_TOOLS_COMMIT="f9f61a9d7c0c76a71dc1db860d1994c53c8aa148"
$env:CHROMIUM_VERSION_TAG="88.0.4324.150"

$ErrorActionPreference = "Stop"

$original_path = $env:path
$original_pwd = $pwd | Select -ExpandProperty Path
function CleanUp {
    $env:path = "$original_path"
    cd $original_pwd
}

trap { CleanUp }
function CheckLastExitCode {
    param ([int[]]$SuccessCodes = @(0), [scriptblock]$CleanupScript=$null)

    if ($SuccessCodes -notcontains $LastExitCode) {
        $msg = @"
EXE RETURNED EXIT CODE $LastExitCode
CALLSTACK:$(Get-PSCallStack | Out-String)
"@
        throw $msg
    }
}

# Tell gclient to use local Vistual Studio install
$env:DEPOT_TOOLS_WIN_TOOLCHAIN=0

# cd to repos directory
cd repos

# Get depot_tools
git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git
cd depot_tools
CheckLastExitCode

git reset --hard ${env:DEPOT_TOOLS_COMMIT}
git clean -ffd
CheckLastExitCode
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

cmd.exe /c cipd_bin_setup.bat
CheckLastExitCode
cmd.exe /c bootstrap\win_tools.bat
CheckLastExitCode
# If you're updating the DEPOT_TOOLS_COMMIT, you should read the skipped bat file to make sure that
# init steps like this are included here, but don't include any steps to update git. /end TODO

cd ..

cmd.exe /c gclient sync -D --force --reset --no-history --jobs=3 --revision=%CHROMIUM_VERSION_TAG% 
CheckLastExitCode
# google wants cmd.exe not powershell
# cmd not strictly necessary as gclient is a .bat that invokes cmd intrinsically but better safe than sorry

cd src
# Append kaleido section to headless build file (src\headless\BUILD.gn)
cat ..\win_scripts\build_target.py | Add-Content -Path .\headless\BUILD.gn
CheckLastExitCode

## Write out credits

python3 $pwd\tools\licenses\licenses.py credits *> ..\CREDITS.html
if ($LASTEXITCODE -ne 0) {
    python $pwd\tools\licenses\licenses.py credits *> ..\CREDITS.html
    CheckLastExitCode
}

# Apply patches

cd ..

# Define the source and destination directories
$sourceDirectory = "$pwd\patches\$Env:CHROMIUM_VERSION_TAG"
$destinationDirectory = "$pwd\src"

# Check if the directory exists
if (Test-Path -Path $sourceDirectory -PathType Container) {
    $itemsToCopy = Get-ChildItem -Path $sourceDirectory -Recurse -File | Where-Object { $_.Name -ne "README.md" }
    # Copy each file from the source directory to the destination directory
    foreach ($item in $itemsToCopy) {
        Write-Output "LOOP!"
        $outPath = $destinationDirectory + $item.DirectoryName.Replace($sourceDirectory, "") + "\" + $item.Name
        Write-Output $relative_file
        # Ensure the destination directory exists
        $null = New-Item -Path (Split-Path $outPath) -ItemType Directory -Force
        
        # Copy the file to the destination directory
        Copy-Item -Path $item.FullName -Destination $outPath -Force
        Write-Output " "
    }
} else {
    Write-Host "No patch directory for $Env:CHROMIUM_VERSION_TAG"
}


# Copy files from the source directory to the destination directory recursively



## Go back to root directory
cd ..
