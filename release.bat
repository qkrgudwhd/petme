@echo off
setlocal
cd /d "%~dp0"

REM ============================================
REM  Build distributable ZIP for GitHub / Drive
REM ============================================

set RELEASE_NAME=PetMe-Moji-source
set RELEASE_DIR=%TEMP%\%RELEASE_NAME%
set OUTPUT_ZIP=%~dp0%RELEASE_NAME%.zip

echo Building distributable package...
echo Output: %OUTPUT_ZIP%
echo.

if exist "%RELEASE_DIR%" rmdir /s /q "%RELEASE_DIR%"
if exist "%OUTPUT_ZIP%" del /f "%OUTPUT_ZIP%"

mkdir "%RELEASE_DIR%"

REM /XD takes directory NAMES — excludes ANY dir with these names at any depth
robocopy "%~dp0" "%RELEASE_DIR%" /E /XD .venv venv node_modules .next __pycache__ .git uploads outputs /XF *.pyc .env secrets.bin "%RELEASE_NAME%.zip" /NFL /NDL /NJH /NJS >nul

REM Recreate empty storage placeholders so users have the structure
if exist "%RELEASE_DIR%\backend\app\storage" rmdir /s /q "%RELEASE_DIR%\backend\app\storage"
mkdir "%RELEASE_DIR%\backend\app\storage\uploads"
mkdir "%RELEASE_DIR%\backend\app\storage\outputs"
type nul > "%RELEASE_DIR%\backend\app\storage\uploads\.gitkeep"
type nul > "%RELEASE_DIR%\backend\app\storage\outputs\.gitkeep"

REM Defensive: re-delete any leftover sensitive files
del /f /q "%RELEASE_DIR%\backend\.env" >nul 2>&1
del /f /q "%RELEASE_DIR%\backend\app\storage\secrets.bin" >nul 2>&1

powershell -nologo -command ^
  "Compress-Archive -Path '%RELEASE_DIR%\*' -DestinationPath '%OUTPUT_ZIP%' -Force"

rmdir /s /q "%RELEASE_DIR%"

if exist "%OUTPUT_ZIP%" (
    for %%I in ("%OUTPUT_ZIP%") do (
        set /a SIZE_KB=%%~zI / 1024
    )
    echo.
    echo ============================================
    echo  Done! Package ready:
    echo    %OUTPUT_ZIP%
    echo    Size: about %SIZE_KB% KB
    echo.
    echo  Upload this ZIP to:
    echo    - GitHub Releases  (recommended)
    echo    - Google Drive     (set sharing: anyone with link)
    echo ============================================
) else (
    echo [ERROR] ZIP creation failed.
)

pause
