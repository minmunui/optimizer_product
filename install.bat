@echo off
setlocal enabledelayedexpansion

:: change directory to the location of this script
cd /D "%~dp0"

echo =========================================================================
echo.
echo   Python venv Launcher
echo   This version does NOT use conda
echo.
echo =========================================================================
echo.

:: deactivate conda environment if it exists
(call conda deactivate && call conda deactivate && call conda deactivate) 2>nul

:: set directory for virtual environment
set VENV_DIR=%cd%\venv

:: check if Python is installed
where python >nul 2>&1
if errorlevel 1 (
    echo Python does not exist.
    goto end
)

:: check if virtual environment already exists
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%" || (
        echo Could not create virtual environment.
        goto end
    )
    echo Virtual environment created at %VENV_DIR%
)

:: activate virtual environment
call "%VENV_DIR%\Scripts\activate.bat"

:: install required packages
echo Installing required packages...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt || (
    echo Could not install required packages.
    goto end
)

:end
pause
