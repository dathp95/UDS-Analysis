@echo off

call .venv\Scripts\activate

pyinstaller UDS-Analysis.spec --clean

if errorlevel 1 (
    echo Build failed!
    pause
    exit /b
)

python build_release.py

echo.
echo Release completed.
pause