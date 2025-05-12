@echo off
setlocal enabledelayedexpansion

:: 현재 스크립트 경로로 이동
cd /D "%~dp0"

echo =========================================================================
echo.
echo   Python venv Launcher
echo   This version does NOT use conda
echo.
echo =========================================================================
echo.

:: conda 환경 비활성화
(call conda deactivate && call conda deactivate && call conda deactivate) 2>nul

:: 가상환경 디렉토리 지정
set VENV_DIR=%cd%\venv

:: Python 설치 여부 확인
where python >nul 2>&1
if errorlevel 1 (
    echo Python does not exist.
    goto end
)

:: 가상환경이 없는 경우 생성
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%" || (
        echo Could not create virtual environment.
        goto end
    )
    echo Virtual environment created at %VENV_DIR%
)

:: 가상환경 활성화
call "%VENV_DIR%\Scripts\activate.bat"

:: 필요한 패키지 설치
echo Installing required packages...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt || (
    echo Could not install required packages.
    goto end
)

:: 스크립트 실행

:end
pause
