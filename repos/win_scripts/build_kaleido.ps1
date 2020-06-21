& {

# cd to repos directory
cd $PSScriptRoot\..

# Add depot_tools to path
$env:path += "$pwd\depot_tools"

# Tell gclient to use local Vistual Studio install
$env:DEPOT_TOOLS_WIN_TOOLCHAIN=0

# cd to repos/src
cd src

# Make output directory
if (-Not (Test-Path out\Kaleido_win)) {
    New-Item -Path out\Kaleido_win -ItemType "directory" -ErrorAction Ignore
}

# Write out/Kaleido_win/args.gn
Copy-Item ..\win_scripts\args.gn -Destination out\Kaleido_win

# 1) Reset headless/BUILD.gn
git checkout HEAD -- headless\BUILD.gn

# 2) Append kaleido section to headless build file (src\headless\BUILD.gn)
cat ..\win_scripts\build_target.py | Add-Content -Path .\headless\BUILD.gn

# 3) Copy kaleido/kaleido.cc to src/headless/app/kaleido.cc
if (Test-Path headless\app\scopes) {
    Remove-Item -Recurse -Force headless\app\scopes
}
Copy-Item ..\kaleido\cc\* -Destination headless\app\ -Recurse 

# 4) Perform build, result will be out/Kaleido_win/kaleido
gn gen out\Kaleido_win
ninja -C out\Kaleido_win -j 8 kaleido

# 5) Copy build files
if (-Not (Test-Path ..\build\kaleido)) {
    New-Item -Path ..\build\kaleido -ItemType "directory"
}
Remove-Item -Recurse -Force ..\build\kaleido\* -ErrorAction Ignore
New-Item -Path ..\build\kaleido\bin -ItemType "directory"

Copy-Item out\Kaleido_win\kaleido.exe -Destination ..\build\kaleido\bin -Recurse
Copy-Item out\Kaleido_win\swiftshader -Destination ..\build\kaleido\bin -Recurse

# Copy icudtl.dat
Copy-Item .\out\Kaleido_win\icudtl.dat -Destination ..\build\kaleido\bin

# Copy javascript
cd ..\kaleido\js\
if (-Not (Test-Path build)) {
    New-Item -Path build -ItemType "directory"
}
npm install
npm run clean
npm run build

# Back to src
cd ..\..\src
if (-Not (Test-Path ..\build\kaleido\js\)) {
    New-Item -Path ..\build\kaleido\js\ -ItemType "directory"
}
Copy-Item ..\kaleido\js\build\*.js -Destination ..\build\kaleido\js\ -Recurse

# Copy kaleido.cmd launch script
Copy-Item ..\win_scripts\kaleido.cmd -Destination ..\build\kaleido\

# Build python wheel
cd ../kaleido/py
python setup.py package
}