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
pyinstaller --noconfirm --onedir --console --name docs --clean --add-data "docs_cli;docs_cli" build_entry.py

if not exist "dist\docs\docs.exe" (
    echo [ERROR] Build failed. Check errors above.
    pause
    exit /b
)

set "INSTALL_DIR=%LOCALAPPDATA%\DocsCLI"
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

echo [INFO] Installing to %INSTALL_DIR%...

REM Remove old installation if exists
if exist "%INSTALL_DIR%\docs" (
    echo [INFO] Removing old installation...
    rmdir /S /Q "%INSTALL_DIR%\docs"
)

REM Copy the entire docs folder
xcopy /E /I /Y "dist\docs" "%INSTALL_DIR%\docs" >nul

if %errorlevel% neq 0 (
    echo [ERROR] Failed to copy files.
    pause
    exit /b
)

REM Create launcher batch file
echo [INFO] Creating launcher script...
(
    echo @echo off
    echo "%INSTALL_DIR%\docs\docs.exe" %%*
) > "%INSTALL_DIR%\docs.bat"

echo [INFO] Updating PATH variable...
set "PS_INSTALL_DIR=%INSTALL_DIR%"
powershell -Command "$installDir=$env:PS_INSTALL_DIR; $p=[Environment]::GetEnvironmentVariable('Path','User'); if($null -eq $p){$p=''}; if($p -notlike '*DocsCLI*'){$new=$p+';'+$installDir; $new=$new -replace '^;',''; [Environment]::SetEnvironmentVariable('Path',$new,'User'); Write-Host '[SUCCESS] Added to PATH'} else {Write-Host '[INFO] Already in PATH'}"

echo.
echo ========================================================
echo [SUCCESS] Docs CLI has been built and installed!
echo.
echo Please RESTART your terminal to use 'docs' command.
echo.
echo Installation folder: %INSTALL_DIR%\docs\
echo Launcher script: %INSTALL_DIR%\docs.bat
echo ========================================================
pause