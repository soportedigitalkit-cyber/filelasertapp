@echo off
echo ========================================
echo Laser File Converter V1.1 - Setup Windows
echo ========================================

if not exist .venv (
    python -m venv .venv
)

call .venv\Scripts\activate
python -m pip install --upgrade pip
pip uninstall cairosvg fonttools -y
pip install -r requirements.txt

echo.
echo Setup finalizado.
echo Para abrir la app ejecuta: run_app.bat
pause
