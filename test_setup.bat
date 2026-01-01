@echo off
COLOR 0E
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║          📋 SMART MEME COIN ANALYZER - TEST 📋            ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

echo [Step 1/5] Checking files...
echo.

set "missing_files=0"

if not exist "app.py" (
    echo ❌ app.py missing
    set "missing_files=1"
) else (
    echo ✓ app.py
)

if not exist "scraper.py" (
    echo ❌ scraper.py missing
    set "missing_files=1"
) else (
    echo ✓ scraper.py
)

if not exist "smart_meme_coin_model.pkl" (
    echo ❌ smart_meme_coin_model.pkl missing
    set "missing_files=1"
) else (
    echo ✓ smart_meme_coin_model.pkl
)

if not exist "templates\index.html" (
    echo ❌ templates\index.html missing
    set "missing_files=1"
) else (
    echo ✓ templates\index.html
)

if not exist "templates\analyze.html" (
    echo ❌ templates\analyze.html missing
    set "missing_files=1"
) else (
    echo ✓ templates\analyze.html
)

if not exist "requirements.txt" (
    echo ❌ requirements.txt missing
    set "missing_files=1"
) else (
    echo ✓ requirements.txt
)

echo.
if "%missing_files%"=="1" (
    echo ❌ Some files are missing!
    pause
    exit /b 1
)
echo ✅ All required files present
echo.

echo [Step 2/5] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found
    pause
    exit /b 1
) else (
    echo ✓ Python installed
)
echo.

echo [Step 3/5] Checking virtual environment...
if not exist ".venv" (
    echo ❌ Virtual environment not found
    echo Run install.bat first
    pause
    exit /b 1
) else (
    echo ✓ Virtual environment exists
)
echo.

echo [Step 4/5] Activating environment and checking packages...
call .venv\Scripts\activate.bat
python -c "import flask, pandas, numpy, xgboost, sklearn, requests, bs4" >nul 2>&1
if errorlevel 1 (
    echo ❌ Some packages missing
    echo Run install.bat to install dependencies
    pause
    exit /b 1
) else (
    echo ✓ All required packages installed
)
echo.

echo [Step 5/5] Testing model loading...
python -c "import pickle; f=open('smart_meme_coin_model.pkl','rb'); m=pickle.load(f); f.close(); print('✓ Model loads successfully')" 2>&1
if errorlevel 1 (
    echo ❌ Model loading failed
    pause
    exit /b 1
)
echo.

echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║              ✅ ALL TESTS PASSED! ✅                       ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo 🚀 Your project is ready to run!
echo.
echo Next steps:
echo   1. Run: start_server.bat
echo   2. Open: http://localhost:5000
echo   3. Analyze coins!
echo.
pause
