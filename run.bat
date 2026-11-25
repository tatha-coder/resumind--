@echo off
echo ========================================================
echo        RESUMIND AI - RESUME ANALYSIS STUDIO
echo ========================================================
echo.

:: Check for Python
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not in your system PATH.
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Create virtual environment if it does not exist
if not exist "venv" (
    echo [INFO] Creating Python virtual environment (venv)...
    python -m venv venv
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Install / verify requirements
echo [INFO] Installing / verifying required libraries...
pip install -r requirements.txt

:: Start Streamlit
echo.
echo ========================================================
echo  Launching Resumind AI at http://localhost:8501
echo ========================================================
echo.
streamlit run app.py

pause
