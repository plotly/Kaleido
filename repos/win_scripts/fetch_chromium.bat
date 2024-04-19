cd repos\

gclient
fetch --nohooks --no-history chromium

cd src
git reset --hard
git fetch origin 'refs/tags/%1:refs/tags/%1'
git checkout ${Env:CHROMIUM_VERSION_TAG}
git clean -ffd

cd ..\..
