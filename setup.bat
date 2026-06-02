@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo  PetMe-Moji First-Time Setup
echo  (Requires Python 3.11+ and Node.js 18+)
echo ============================================
echo.

echo [1/2] Backend venv + pip install (2-5 min)...
cd backend
if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create venv. Check Python 3.11+ is installed.
        pause
        exit /b 1
    )
)
call .venv\Scripts\python.exe -m pip install --upgrade pip >nul
call .venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] pip install failed.
    pause
    exit /b 1
)

if not exist ".env" copy ".env.example" ".env" >nul
cd ..

echo.
echo [2/2] Frontend npm install (1-3 min)...
cd frontend
if not exist "node_modules" (
    call npm install
    if errorlevel 1 (
        echo [ERROR] npm install failed. Check Node.js 18+ is installed.
        pause
        exit /b 1
    )
) else (
    echo node_modules exists, skipping.
)
cd ..

echo.
echo ============================================
echo  Setup complete!
echo.
echo  Next:
echo   1) Double-click start.bat (browser opens automatically)
echo   2) Enter Gemini API key on the first screen
echo      Get one at https://aistudio.google.com/apikey
echo   3) Upload 2 photos, choose style, generate 32 stickers
echo ============================================
echo.
pause
