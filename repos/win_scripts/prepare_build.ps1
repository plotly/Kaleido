cd repos\src
# 2) Append kaleido section to headless build file (src\headless\BUILD.gn)
cat ..\win_scripts\build_target.py | Add-Content -Path .\headless\BUILD.gn

## Write out credits
python3 --version
python3 ..\src\tools\licenses\licenses.py credits > ..\CREDITS.html

## Go back to where we started
cd ..\..

