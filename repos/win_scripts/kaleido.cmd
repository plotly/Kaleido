@echo off
setlocal
chdir /d "%~dp0"
.\bin\kaleido.exe --no-sandbox --allow-file-access-from-files --disable-breakpad %*