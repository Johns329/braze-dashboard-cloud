@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem Master refresh script for Streamlit dashboard.
rem - Runs Braze snapshot extract + parse (writes data\tables\*.csv/json)
rem - Uses cached Primary_Locations_Catalog when available (data\latest_catalog)
rem   otherwise runs Primary_Locations_Catalog exporter (external repo)
rem - Builds catalog composition artifacts (writes data\tables\catalog_composition_*)
rem - Commits + pushes ONLY data\tables\ outputs (leaves other changes untouched)

for /f "delims=" %%a in ('echo prompt $E^| cmd') do set "ESC=%%a"
set "C_RESET=!ESC![0m"
set "C_DIM=!ESC![2m"
set "C_BOLD=!ESC![1m"
set "C_RED=!ESC![31m"
set "C_GREEN=!ESC![32m"
set "C_YELLOW=!ESC![33m"
set "C_BLUE=!ESC![34m"
set "C_MAGENTA=!ESC![35m"
set "C_CYAN=!ESC![36m"

set "DO_COMMIT=1"
set "DO_PUSH=1"
set "ENV_FILE="
set "SHOW_HELP=0"
set "DID_PUSHD=0"
set "EXITCODE=0"

rem Allow override via env var; default matches your local layout.
set "EXPORTER_DIR=C:\Toast\braze_catalog_exporter"
if not "%BRAZE_CATALOG_EXPORTER_DIR%"=="" set "EXPORTER_DIR=%BRAZE_CATALOG_EXPORTER_DIR%"

rem Resolve dashboard dir from this script.
set "DASHBOARD_DIR=%~dp0"
for %%I in ("%DASHBOARD_DIR%.") do set "DASHBOARD_DIR=%%~fI"

call :parse_args %*
if errorlevel 1 exit /b %errorlevel%
if "!SHOW_HELP!"=="1" exit /b 0

call :banner

pushd "%DASHBOARD_DIR%" >nul
set "DID_PUSHD=1"

call :step 1 6 "Validate environment"
call :need_cmd git
call :need_cmd python
if not exist "etl\extract_braze.py" call :die "Missing etl\extract_braze.py (wrong folder?)"
if not exist "etl\parse_liquid.py" call :die "Missing etl\parse_liquid.py (wrong folder?)"
if not exist "scripts\build_catalog_composition.py" call :die "Missing scripts\build_catalog_composition.py (wrong folder?)"
if not exist "data\tables" mkdir "data\tables" >nul 2>nul
if not exist "data\latest_catalog" mkdir "data\latest_catalog" >nul 2>nul
call :ok "Ready"

call :step 2 6 "Extract latest Braze snapshots"
if "!ENV_FILE!"=="" (
  call :info "Running: python etl\\extract_braze.py"
  python etl\extract_braze.py
) else (
  call :info "Running: python etl\\extract_braze.py --env-file !ENV_FILE!"
  python etl\extract_braze.py --env-file "!ENV_FILE!"
)
if errorlevel 1 call :die "Extract failed (no new data pulled). Fix credentials/network and re-run."
call :ok "Extract complete"

call :step 3 6 "Parse snapshots into Streamlit tables"
call :info "Writes: data\\tables\\(catalog_schema, asset_inventory, content_blocks, field_references, dependencies, refresh_meta)"
python etl\parse_liquid.py
if errorlevel 1 call :die "Parse failed. See output above."
call :ok "Parse complete"

call :step 4 6 "Export Primary_Locations_Catalog (cached when PST-today exists)"

set "CACHED_EXPORT="
call :find_cached_today_export

if not "!CACHED_EXPORT!"=="" (
  set "LATEST_EXPORT=!CACHED_EXPORT!"
  call :warn "Cached catalog found for PST-today; skipping Braze catalog API fetch."
  call :ok "Using cached export: !LATEST_EXPORT!"
) else (
  if not exist "!EXPORTER_DIR!\export_primary_locations_catalog.bat" call :die "Exporter not found: !EXPORTER_DIR!\export_primary_locations_catalog.bat"
  call :info "Exporter dir: !EXPORTER_DIR!"
  call "!EXPORTER_DIR!\export_primary_locations_catalog.bat"
  if errorlevel 1 call :die "Catalog export failed. See exporter output above."

  set "LATEST_EXPORT="
  call :find_latest_export
  if "!LATEST_EXPORT!"=="" call :die "Could not find an exported catalog CSV in !EXPORTER_DIR!\exports"
  call :ok "Latest export: !LATEST_EXPORT!"

  rem Best-effort cache copy so subsequent runs can skip the fetch.
  copy /y "!LATEST_EXPORT!" "data\latest_catalog\" >nul 2>nul
  if errorlevel 1 (
    call :warn "Could not copy export to data\latest_catalog (continuing)."
  ) else (
    call :info "Cached to: data\latest_catalog\"
  )
)

call :step 5 6 "Build catalog composition artifacts"
call :info "Reads: !LATEST_EXPORT!"
call :info "Writes: data\\tables\\catalog_composition_*"
python scripts\build_catalog_composition.py --input "!LATEST_EXPORT!" --output-dir "data\tables"
if errorlevel 1 call :die "Catalog composition build failed."
call :ok "Catalog composition artifacts updated"

call :step 6 6 "Commit + push dashboard data (data\\tables only)"
call :info "Staging: data\\tables\\*.csv and data\\tables\\*.json"

git add -A "data\tables" >nul
if errorlevel 1 call :die "git add failed"

git diff --cached --quiet -- "data/tables"
if not errorlevel 1 (
  call :warn "No changes in data\\tables; skipping commit/push."
  goto done
)

set "HAS_OTHER_STAGED=0"
for /f "usebackq delims=" %%F in (`git diff --cached --name-only`) do (
  set "F=%%F"
  set "PFX=!F:~0,12!"
  if /i not "!PFX!"=="data/tables/" set "HAS_OTHER_STAGED=1"
)
if "!HAS_OTHER_STAGED!"=="1" call :warn "There are staged changes outside data\\tables; this script will not commit them, but they will remain staged."

if "%DO_COMMIT%"=="0" (
  call :warn "Commit disabled (--no-commit). Leaving changes staged."
  goto done
)

set "STAMP="
for /f "usebackq delims=" %%T in (`powershell -NoProfile -Command "(Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss ''UTC''')"`) do set "STAMP=%%T"
set "MSG=Refresh dashboard data (!STAMP!)"
call :info "Commit: !MSG!"
git commit -m "!MSG!" -- "data/tables"
if errorlevel 1 call :die "git commit failed"
set "COMMIT_SHA="
for /f "usebackq delims=" %%H in (`git rev-parse --short HEAD`) do set "COMMIT_SHA=%%H"
if not "!COMMIT_SHA!"=="" (
  call :ok "Committed (!COMMIT_SHA!)"
) else (
  call :ok "Committed"
)

if "%DO_PUSH%"=="0" (
  call :warn "Push disabled (--no-push). Commit created locally only."
  goto done
)

call :info "Pushing to remote (current branch upstream)"
git push
if errorlevel 1 call :die "git push failed"
call :ok "Pushed"

:done
if "!DID_PUSHD!"=="1" popd >nul
echo.
echo(!C_BOLD!!C_GREEN!All done.!C_RESET!
exit /b 0


:abort
if "!DID_PUSHD!"=="1" popd >nul
exit /b !EXITCODE!


:parse_args
if "%~1"=="" exit /b 0
if /i "%~1"=="--help" (
  set "SHOW_HELP=1"
  call :usage
  exit /b 0
)
if /i "%~1"=="--env-file" (
  if "%~2"=="" (
    echo Missing value for --env-file
    exit /b 2
  )
  set "ENV_FILE=%~2"
  shift
  shift
  goto parse_args
)
if /i "%~1"=="--no-push" (
  set "DO_PUSH=0"
  shift
  goto parse_args
)
if /i "%~1"=="--no-commit" (
  set "DO_COMMIT=0"
  set "DO_PUSH=0"
  shift
  goto parse_args
)
echo Unknown argument: %~1
echo Run: refresh_and_publish.bat --help
exit /b 2


:usage
echo.
echo Usage:
echo   refresh_and_publish.bat [--env-file PATH] [--no-push] [--no-commit]
echo.
echo Notes:
echo   - Commits/pushes ONLY data\tables\ outputs.
echo   - Leaves any other local changes uncommitted.
echo   - Exporter path defaults to C:\Toast\braze_catalog_exporter; override with BRAZE_CATALOG_EXPORTER_DIR.
echo.
exit /b 0


:banner
echo.
echo(!C_BOLD!!C_CYAN!============================================================!C_RESET!
echo(!C_BOLD!!C_CYAN!  Braze Dashboard: Refresh + Publish (data\tables only)       !C_RESET!
echo(!C_BOLD!!C_CYAN!============================================================!C_RESET!
echo(!C_DIM!Dashboard: !DASHBOARD_DIR!!C_RESET!
echo(!C_DIM!Exporter : !EXPORTER_DIR!!C_RESET!
if not "!ENV_FILE!"=="" echo(!C_DIM!Env file : !ENV_FILE!!C_RESET!
echo.
exit /b 0


:need_cmd
where %~1 >nul 2>nul
if errorlevel 1 call :die "Missing required command in PATH: %~1"
exit /b 0


:step
set "N=%~1"
set "TOTAL=%~2"
set "TITLE=%~3"
echo.
echo(!C_BOLD!!C_BLUE![Step !N!/!TOTAL!] !TITLE!!C_RESET!
echo(!C_DIM!Next: see command output; failures stop the run.!C_RESET!
exit /b 0


:info
echo(!C_CYAN![info]!C_RESET! %~1
exit /b 0


:ok
echo(!C_GREEN![ok]!C_RESET! %~1
exit /b 0


:warn
echo(!C_YELLOW![warn]!C_RESET! %~1
exit /b 0


:die
echo.
echo(!C_BOLD!!C_RED![error]!C_RESET! %~1
echo(!C_DIM!Stopped. No changes were pushed unless step 6 completed successfully.!C_RESET!
set "EXITCODE=1"
goto abort


:find_latest_export
set "EXP_DIR=!EXPORTER_DIR!\exports"
if not exist "!EXP_DIR!" exit /b 0
for /f "delims=" %%F in ('dir /b /a:-d /o:-d "!EXP_DIR!\Primary_Locations_Catalog_*.csv" 2^>nul') do (
  set "LATEST_EXPORT=!EXP_DIR!\%%F"
  goto :eof
)
exit /b 0


:find_cached_today_export
set "CACHED_EXPORT="
set "CACHE_DIR=!DASHBOARD_DIR!\data\latest_catalog"
if not exist "!CACHE_DIR!" exit /b 0

rem Find most-recent Primary_Locations_Catalog* CSV modified on today's PST date.
for /f "usebackq delims=" %%F in (`powershell -NoProfile -Command "$dir='!CACHE_DIR!'; $pattern='Primary_Locations_Catalog*.csv'; try { $tz=[TimeZoneInfo]::FindSystemTimeZoneById('Pacific Standard Time') } catch { $tz=[TimeZoneInfo]::Local }; $today=[TimeZoneInfo]::ConvertTimeFromUtc((Get-Date).ToUniversalTime(), $tz).Date; $f=Get-ChildItem -LiteralPath $dir -Filter $pattern -File -ErrorAction SilentlyContinue ^| Where-Object { [TimeZoneInfo]::ConvertTimeFromUtc($_.LastWriteTimeUtc, $tz).Date -eq $today } ^| Sort-Object LastWriteTimeUtc -Descending ^| Select-Object -First 1; if ($f) { $f.FullName }"`) do (
  set "CACHED_EXPORT=%%F"
)
exit /b 0
