@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo  PetMe-Moji Start
echo ============================================
echo.

if not exist "backend\.venv\Scripts\python.exe" (
    echo [ERROR] Backend venv not found. Run setup.bat first.
    pause
    exit /b 1
)
if not exist "frontend\node_modules" (
    echo [ERROR] Frontend packages not installed. Run setup.bat first.
    pause
    exit /b 1
)

echo [1/3] Starting backend (port 8000)...
start "PetMe Backend" cmd /k "cd /d "%~dp0backend" && .venv\Scripts\activate.bat && uvicorn app.main:app --port 8000 --reload"

echo [2/3] Starting frontend (port 3000)...
start "PetMe Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo [3/3] Waiting 10 seconds for servers to boot...
timeout /t 10 /nobreak >nul

echo.
echo Opening browser: http://localhost:3000
start "" "http://localhost:3000"

echo.
echo ============================================
echo  Done! Browser should open shortly.
echo.
echo  - Enter your Gemini API key on the first screen
echo    (Get one at https://aistudio.google.com/apikey)
echo  - The key is encrypted and remembered next time
echo.
echo  To stop: run stop.bat, or close the two cmd windows
echo  Check "PetMe Backend" / "PetMe Frontend" windows for logs
echo ============================================
echo.
pause
