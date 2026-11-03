@echo off
echo ========================================================
echo   Stock Correlation Explorer — Streamlit Web App
echo ========================================================
echo.
cd /d "%~dp0"
echo Starting Streamlit app at http://localhost:8501 ...
streamlit run streamlit_app.py
pause
