@echo off
setlocal

call .venv\Scripts\activate

if errorlevel 1 (
    echo Failed to activate virtual environment.
    pause
    exit /b 1
)

set NUITKA_BUILD_DIR=build\nuitka
set NUITKA_DIST=%NUITKA_BUILD_DIR%\main.dist
set FINAL_DIST=dist\EEIV Diagnostic

if exist "%NUITKA_BUILD_DIR%" (
    rmdir /s /q "%NUITKA_BUILD_DIR%"
)

if exist "%FINAL_DIST%" (
    rmdir /s /q "%FINAL_DIST%"
)

python -m nuitka ^
    --standalone ^
    --enable-plugin=pyside6 ^
    --windows-console-mode=disable ^
    --windows-icon-from-ico=gui\resources\icons\car-diagnostics.ico ^
    --output-dir=%NUITKA_BUILD_DIR% ^
    --output-filename=V-CODE.exe ^
    --include-data-dir=gui\resources=gui\resources ^
    --include-module=can.io.asc ^
    --include-module=can.io.blf ^
    --include-package=openpyxl ^
    --include-package=pandas ^
    --include-package=pyqtgraph ^
    --include-package=cryptography ^
    --company-name="AES EEIV" ^
    --product-name="V-CODE" ^
    --file-description="V-CODE EEIV Diagnostic Tool" ^
    --file-version=3.0.6.0 ^
    --product-version=3.0.6.0 ^
    main.py

if errorlevel 1 (
    echo Nuitka build failed!
    pause
    exit /b 1
)

if not exist "%NUITKA_DIST%\V-CODE.exe" (
    set NUITKA_DIST=%NUITKA_BUILD_DIR%\V-CODE.dist
)

if not exist "%NUITKA_DIST%\V-CODE.exe" (
    echo Nuitka standalone output was not found.
    pause
    exit /b 1
)

python build_release.py --runtime-source "%NUITKA_DIST%" --dist "%FINAL_DIST%" --validate-archives

if errorlevel 1 (
    echo Release preparation or security validation failed!
    pause
    exit /b 1
)

echo.
echo Release completed successfully.
pause

endlocal
