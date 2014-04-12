@echo off
setLocal EnableDelayedExpansion

del gifs.html
echo ^<html^> >>gifs.html

set /a count=1
for /f "tokens=* delims= " %%a in (list.txt) do (
echo !count!^<img src^="%%a"^>^<br^> >>gifs.html
set /a count+=1
)

echo ^<^/html^> >>gifs.html
