@echo off
echo ============================================
echo   Stock Correlation Explorer
echo   Starting server...
echo ============================================
echo.

REM Check if venv exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate venv
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt -q

echo.
echo Starting server at http://localhost:5500
echo Press Ctrl+C to stop
echo.
python app.py
