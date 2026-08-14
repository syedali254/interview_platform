@echo off
setlocal EnableExtensions EnableDelayedExpansion
call :strlen "%~dp0" PATHLEN
echo   this folder path is !PATHLEN! characters
if !PATHLEN! GTR 120 (echo   WARN: too deep) else (echo   OK: comfortably within the limit)
exit /b 0
:strlen
set "_S=%~1"
set "_N=0"
:strlen_next
if defined _S (
    set "_S=!_S:~1!"
    set /a _N+=1
    goto :strlen_next
)
set "%~2=!_N!"
exit /b 0
