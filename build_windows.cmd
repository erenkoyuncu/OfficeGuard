@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo OFFICEGUARD 1.0.0 - WINDOWS PRODUCT BUILD
echo ============================================================
echo.

set "OFFICEGUARD_ICON=assets\branding\officeguard.ico"

if not exist "%OFFICEGUARD_ICON%" (
  echo ERROR: OfficeGuard icon not found: %OFFICEGUARD_ICON%
  goto :error
)

python --version
if errorlevel 1 goto :error

echo [1/7] Build dependencies...
python -m pip install --upgrade pip
if errorlevel 1 goto :error

python -m pip install --upgrade psutil pywin32 pyinstaller
if errorlevel 1 goto :error

echo.
echo [2/7] Clean build folders...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist payload rmdir /s /q payload
mkdir payload

echo.
echo [3/7] Build OfficeGuardService (onedir)...
python -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onedir ^
  --console ^
  --icon "%OFFICEGUARD_ICON%" ^
  --name OfficeGuardService ^
  --hidden-import win32timezone ^
  service.py
if errorlevel 1 goto :error

echo.
echo [4/7] Build UI / Admin / Uninstall...
python -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --windowed ^
  --icon "%OFFICEGUARD_ICON%" ^
  --name OfficeGuardUI ^
  ui_agent.py
if errorlevel 1 goto :error

python -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --windowed ^
  --icon "%OFFICEGUARD_ICON%" ^
  --name OfficeGuardAdmin ^
  admin.py
if errorlevel 1 goto :error

python -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --console ^
  --uac-admin ^
  --icon "%OFFICEGUARD_ICON%" ^
  --name OfficeGuardUninstall ^
  uninstall.py
if errorlevel 1 goto :error

echo.
echo [5/7] Stage setup payload...
mkdir payload\Service
xcopy /e /i /y "dist\OfficeGuardService\*" "payload\Service\" > nul
copy /y "dist\OfficeGuardUI.exe" "payload\OfficeGuardUI.exe" > nul
copy /y "dist\OfficeGuardAdmin.exe" "payload\OfficeGuardAdmin.exe" > nul
copy /y "dist\OfficeGuardUninstall.exe" "payload\OfficeGuardUninstall.exe" > nul

if exist alert.wav copy /y "alert.wav" "payload\alert.wav" > nul

echo.
echo [6/7] Build OfficeGuardSetup.exe...
python -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --console ^
  --uac-admin ^
  --icon "%OFFICEGUARD_ICON%" ^
  --name OfficeGuardSetup ^
  --add-data "payload:payload" ^
  setup.py
if errorlevel 1 goto :error

echo.
echo [7/7] DONE
echo.
echo ============================================================
echo Build output:
echo   %CD%\dist\OfficeGuardSetup.exe
echo ============================================================
echo.
echo Bu EXE hedef PC'de Python olmadan kurulabilir.
echo.
pause
exit /b 0

:error
echo.
echo ============================================================
echo BUILD FAILED
echo ============================================================
echo.
pause
exit /b 1
