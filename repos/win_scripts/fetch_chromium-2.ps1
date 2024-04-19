cd repos\

fetch --nohooks --no-history chromium

cd src
git reset --hard
git fetch origin 'refs/tags/${Env:CHROMIUM_VERSION_TAG}:refs/tags/${Env:CHROMIUM_VERSION_TAG}'
git checkout ${Env:CHROMIUM_VERSION_TAG}
git clean -ffd

cd ..\..
