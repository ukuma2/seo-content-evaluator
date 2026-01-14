@echo off
echo Starting SEO Content Evaluator...
echo.
cd /d "%~dp0"
python -m streamlit run app.py
pause
