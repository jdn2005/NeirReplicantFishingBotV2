@echo off
setlocal

set CONDA_ENV=replicant_fishing_bot
set VENV_DIR=venv
set SCRIPT=Calibration.py

:: Check if Conda is installed
where conda >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    :: Check if Conda env exists
    conda info --envs | findstr /C:"%CONDA_ENV%" >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo Found Conda environment: %CONDA_ENV%
        call conda activate %CONDA_ENV%
        goto :run_script
    ) else (
        echo Conda installed but environment "%CONDA_ENV%" not found.
    )
) else (
    echo Conda not installed or not in PATH.
)

:: Check for Python venv
if exist %VENV_DIR%\Scripts\activate.bat (
    echo Found Python virtual environment: %VENV_DIR%
    call %VENV_DIR%\Scripts\activate.bat
    goto :run_script
)

:: Nothing found
echo No valid environment found.
echo Please run install.bat or install_with_python.bat first.
pause
exit /b 1

:run_script
echo Running %SCRIPT%...
python %SCRIPT%
pause
