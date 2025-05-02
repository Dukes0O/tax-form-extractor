@echo off
REM One-click starter for Tax Form Extractor app

REM Activate virtual environment if it exists
IF EXIST venv (
    call venv\Scripts\activate
)

REM Install dependencies only if not already installed
pip show flask >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Installing dependencies...
    pip install -r requirements.txt
) ELSE (
    echo Dependencies already installed.
)

REM Start the Flask app
cd app
start "" http://localhost:5000
python main.py
