@echo off
echo ===================================================
echo 1. Fetching Fresh Data from Braze API...
echo ===================================================

:: Ensure we are in the script's directory
cd /d "%~dp0"

:: Check if uv is installed
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: 'uv' is not found in your PATH. Please install uv first.
    pause
    exit /b 1
)

:: Ensure virtual environment exists (keeps installs local)
if not exist ".venv\Scripts\python.exe" (
    echo Creating .venv...
    uv venv
    if %errorlevel% neq 0 (
        echo Error: Failed to create .venv.
        pause
        exit /b 1
    )
)

:: Ensure dependencies are installed
echo Checking dependencies...
uv pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error: Failed to install dependencies.
    echo.
    echo Try running: uv pip install -r requirements.txt
    pause
    exit /b 1
)

:: Run the Extraction Script
set "ENV_FILE=C:\Toast\.env"
if exist "%ENV_FILE%" (
    echo Loading configuration from %ENV_FILE% ...
    uv run etl/extract_braze.py --env-file "%ENV_FILE%"
) else (
    echo No %ENV_FILE% found. Using local .env or process environment...
    uv run etl/extract_braze.py
)

if %errorlevel% neq 0 (
    echo.
    echo Extraction failed. Check your API key or connection.
    echo Falling back to existing local files...
) else (
    echo.
    echo Extraction complete.
)

:PARSE
echo.
echo ===================================================
echo 2. Parsing Data into CSV Tables...
echo ===================================================

:: Run the Parsing Script
uv run etl/parse_liquid.py

if %errorlevel% equ 0 (
    echo.
    echo Success! Dashboard data updated in data/tables/
) else (
    echo.
    echo Parsing Failed. Please check the error messages above.
)

:: Show git status for easy commit
where git >nul 2>nul
if %errorlevel% equ 0 (
    echo.
    echo ===================================================
    echo Next: Review and commit updated CSV tables
    echo ===================================================
    git status
)

pause
