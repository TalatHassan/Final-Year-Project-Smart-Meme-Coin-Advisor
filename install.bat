@echo off
COLOR 0A
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║     🚀 SMART MEME COIN ANALYZER - INSTALLATION 🚀         ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo [Step 1/4] Checking Python installation...
python --version
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.11
    pause
    exit /b 1
)
echo ✓ Python found
echo.

echo [Step 2/4] Activating virtual environment...
if not exist ".venv" (
    echo ❌ Virtual environment not found!
    echo Creating virtual environment...
    python -m venv .venv
    echo ✓ Virtual environment created
)
call .venv\Scripts\activate.bat
echo ✓ Virtual environment activated
echo.

echo [Step 3/4] Installing dependencies...
echo This may take a few minutes...
echo.
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Installation failed!
    pause
    exit /b 1
)
echo.
echo ✓ All dependencies installed successfully
echo.

echo [Step 4/4] Verifying installation...
python -c "import flask, pandas, numpy, xgboost, sklearn; print('✓ All packages verified')"
if errorlevel 1 (
    echo ❌ Some packages are missing!
    pause
    exit /b 1
)
echo.

echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║              ✅ INSTALLATION COMPLETED! ✅                 ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo 🚀 Ready to run! Use start_server.bat to launch the app
echo.
echo 📋 Installed packages:
pip list | findstr "Flask pandas numpy xgboost scikit-learn requests beautifulsoup4"
echo.
echo ════════════════════════════════════════════════════════════
pause
