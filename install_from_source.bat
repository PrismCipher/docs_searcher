@echo off

title Docs CLI Installer (Source)
echo ========================================================
echo      DOCS CLI - BUILD ^& INSTALL FROM SOURCE
echo ========================================================

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b
)

echo [INFO] Installing requirements...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install requirements.
    pause
    exit /b
)

pip install pyinstaller
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install PyInstaller.
    pause
    exit /b
)

echo [INFO] Building executable...
pyinstaller --noconfirm --onefile --console --name docs --clean --add-data "docs_cli;docs_cli" build_entry.py

if not exist "dist\docs.exe" (
    echo [ERROR] Build failed. Check errors above.
    pause
    exit /b
)

set "INSTALL_DIR=%LOCALAPPDATA%\DocsCLI"
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

echo [INFO] Installing to %INSTALL_DIR%...
copy /Y "dist\docs.exe" "%INSTALL_DIR%\docs.exe" >nul

if %errorlevel% neq 0 (
    echo [ERROR] Failed to copy files.
    pause
    exit /b
)

echo [INFO] Updating PATH variable...
set "PS_INSTALL_DIR=%INSTALL_DIR%"
powershell -Command "$installDir=$env:PS_INSTALL_DIR; $p=[Environment]::GetEnvironmentVariable('Path','User'); if($null -eq $p){$p=''}; if($p -notlike '*DocsCLI*'){$new=$p+';'+$installDir; $new=$new -replace '^;',''; [Environment]::SetEnvironmentVariable('Path',$new,'User'); Write-Host '[SUCCESS] Added to PATH'} else {Write-Host '[INFO] Already in PATH'}"

echo.
echo ========================================================
echo [SUCCESS] Docs CLI has been built and installed!
echo.
echo Please RESTART your terminal to use 'docs' command.
echo.
echo Location: %INSTALL_DIR%\docs.exe
echo ========================================================
pause