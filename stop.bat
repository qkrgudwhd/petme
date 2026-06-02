@echo off
echo Stopping PetMe-Moji servers...

REM Kill processes on port 8000 (backend)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000 " ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

REM Kill processes on port 3000 (frontend)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000 " ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

REM Close labeled windows
taskkill /F /FI "WINDOWTITLE eq PetMe Backend*"  >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq PetMe Frontend*" >nul 2>&1

echo Done.
timeout /t 2 >nul
