@echo off
REM ============================================================
REM  Builds MarathiCalendarMaker.exe  (run this ONCE on Windows)
REM  Needs: Python 3.10 - 3.12 (64-bit) from python.org, with "Add to PATH"
REM  Result: dist\MarathiCalendarMaker.exe  (double-click to use)
REM ============================================================
setlocal
cd /d "%~dp0"

set PY=py -3.12
%PY% --version >nul 2>nul || set PY=py -3.11
%PY% --version >nul 2>nul || set PY=py -3
%PY% --version >nul 2>nul || set PY=python
%PY% --version || (echo Python not found. Install Python 3.12 from python.org and re-run. & pause & exit /b 1)

%PY% -m venv .venv || (echo Could not create virtual environment & pause & exit /b 1)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt pyinstaller || (echo Package install failed & pause & exit /b 1)

REM quick self-test of the calculation engine before building
python tests\verify.py || (echo Self-test failed & pause & exit /b 1)

pyinstaller --noconfirm --clean --onefile --windowed --name MarathiCalendarMaker ^
  --add-data "marathi_calendar\fonts;marathi_calendar\fonts" ^
  --hidden-import swisseph --hidden-import uharfbuzz --collect-submodules fpdf ^
  run.py || (echo Build failed & pause & exit /b 1)

echo.
echo ===== DONE =====  dist\MarathiCalendarMaker.exe
pause
