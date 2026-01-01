@echo off
COLOR 0B
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║      🚀 SMART MEME COIN ANALYZER - STARTING... 🚀         ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

echo [1/2] Activating virtual environment...
call .venv\Scripts\activate.bat
echo ✓ Virtual environment activated
echo.

echo [2/2] Starting server...
echo.
echo ════════════════════════════════════════════════════════════
echo   🌐 Server starting on: http://localhost:5000
echo   📱 Open browser: http://localhost:5000
echo   ⏹️  Press Ctrl+C to stop
echo ════════════════════════════════════════════════════════════
echo.

REM Start with Python directly (no batch wrapper)
"%~dp0.venv\Scripts\python.exe" -u run_server.py

echo.
echo ════════════════════════════════════════════════════════════
echo   Server stopped
echo ════════════════════════════════════════════════════════════
pause
