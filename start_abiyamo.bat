@echo off
title ABIYAMO - ANC Risk Scoring
echo.
echo  Starting ABIYAMO...
echo  Open your browser at: http://localhost:5000
echo  Press Ctrl+C to stop the server.
echo.
cd /d "%~dp0"
python app.py
pause
