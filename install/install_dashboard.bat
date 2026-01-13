@echo off
REM Behavior Box Controller - Dashboard Installation Script
REM Supports: Windows 10, Windows 11
REM License: CC BY-NC-SA 4.0

setlocal enabledelayedexpansion

REM Constants
set SCRIPT_DIR=%~dp0
set REPO_ROOT=%SCRIPT_DIR%..
set MIN_PYTHON_VERSION=3.11
set APP_NAME=Behavior Box Dashboard
set VENV_PATH=%REPO_ROOT%\venvs\dashboard
set REQUIREMENTS=%REPO_ROOT%\apps\dashboard\requirements.txt

echo.
echo ======================================
echo   Behavior Box Dashboard Installer
echo ======================================
echo.

REM Check for Python
echo [1/7] Checking Python installation...
py -3.11 --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.11+ not found
    echo Please install from https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('py -3.11 --version') do set PYTHON_VERSION=%%i
echo [OK] Found !PYTHON_VERSION!

REM Create virtual environment
echo.
echo [2/7] Creating virtual environment...
if exist "%VENV_PATH%" (
    echo [WARN] Virtual environment already exists
    set /p RECREATE="Remove and recreate? [y/N]: "
    if /i "!RECREATE!"=="y" (
        echo Removing existing virtual environment...
        rmdir /s /q "%VENV_PATH%"
    ) else (
        echo Using existing virtual environment
        goto :skip_venv_creation
    )
)

echo Creating virtual environment at %VENV_PATH%
py -3.11 -m venv "%VENV_PATH%"
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)

:skip_venv_creation
echo [OK] Virtual environment ready

REM Activate and install
echo.
echo [3/7] Installing dependencies...
call "%VENV_PATH%\Scripts\activate.bat"
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

echo Upgrading pip...
python -m pip install --upgrade pip --quiet
if errorlevel 1 (
    echo [ERROR] Failed to upgrade pip
    pause
    exit /b 1
)

echo Installing Python packages (this may take a few minutes)...
pip install -r "%REQUIREMENTS%"
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed

REM Convert icon
echo.
echo [4/7] Converting icon for Windows...
python -c "from PIL import Image; img = Image.open('%REPO_ROOT%/apps/dashboard/assets/icon.png'); img.save('%REPO_ROOT%/apps/dashboard/assets/icon.ico', format='ICO')" 2>nul
if errorlevel 1 (
    echo [WARN] Icon conversion failed, but continuing...
) else (
    echo [OK] Icon converted
)

REM Verify installation
echo.
echo [5/7] Verifying installation...
python -c "import PyQt6; import websocket; import PIL"
if errorlevel 1 (
    echo [ERROR] Verification failed
    echo One or more packages could not be imported
    pause
    exit /b 1
)
echo [OK] Verification complete

REM Create launcher
echo.
echo [6/7] Creating launcher...
(
echo @echo off
echo REM Auto-generated launcher for Behavior Box Dashboard
echo.
echo set SCRIPT_DIR=%%~dp0
echo set VENV_PATH=%%SCRIPT_DIR%%venvs\dashboard
echo.
echo if not exist "%%VENV_PATH%%" ^(
echo     echo Error: Virtual environment not found at %%VENV_PATH%%
echo     echo Please run install\install_dashboard.bat first
echo     pause
echo     exit /b 1
echo ^)
echo.
echo call "%%VENV_PATH%%\Scripts\activate.bat"
echo cd "%%SCRIPT_DIR%%apps\dashboard"
echo bash start.sh
echo if errorlevel 1 ^(
echo     echo.
echo     echo Error: Failed to start dashboard
echo     echo Check the log file at apps\dashboard\logs\dashboard.log
echo     pause
echo ^)
) > "%REPO_ROOT%\launch_dashboard.bat"
echo [OK] Launcher created at %REPO_ROOT%\launch_dashboard.bat

REM Create shortcut
echo.
echo [7/7] Creating desktop shortcut...
set /p CREATE_SHORTCUT="Create desktop shortcut? [y/N]: "
if /i "!CREATE_SHORTCUT!"=="y" (
    REM Use PowerShell to create shortcut
    powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\Behavior Box Dashboard.lnk'); $Shortcut.TargetPath = '%REPO_ROOT%\launch_dashboard.bat'; $Shortcut.IconLocation = '%REPO_ROOT%\apps\dashboard\assets\icon.ico'; $Shortcut.WorkingDirectory = '%REPO_ROOT%'; $Shortcut.Save()" 2>nul
    if errorlevel 1 (
        echo [WARN] Desktop shortcut creation failed
    ) else (
        echo [OK] Desktop shortcut created
    )
)

echo.
echo ======================================
echo   Installation Complete!
echo ======================================
echo.
echo To start the dashboard:
echo   1. Double-click: launch_dashboard.bat
echo   2. Or use desktop shortcut (if created)
echo.
echo For help, see: install\README.md
echo.
pause
