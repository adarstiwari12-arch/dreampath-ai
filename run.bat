@echo off
REM run.bat - one-click start for Windows.
REM Creates the virtual environment, installs Flask, creates .env, then starts the app.
setlocal
cd /d "%~dp0"

where py >nul 2>nul && (set PY=py -3) || (set PY=python)

if not exist .venv (
  echo Creating virtual environment ^(.venv^)...
  %PY% -m venv .venv
  if errorlevel 1 goto :error
)
call .venv\Scripts\activate.bat

python -c "import flask" 2>nul
if errorlevel 1 (
  echo Installing dependencies...
  pip install -r requirements.txt
  if errorlevel 1 goto :error
)

if not exist .env copy .env.example .env >nul

echo.
echo DreamPath AI is starting at http://127.0.0.1:5000   ^(press Ctrl+C to stop^)
echo.
flask --app app run --debug
goto :eof

:error
echo.
echo Something went wrong. Open HOW_TO_RUN.md and see the Troubleshooting section.
pause
