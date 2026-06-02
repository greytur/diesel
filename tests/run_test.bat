CALL "C:\Users\Greyson\dev\projects\diesel\.venv\Scripts\activate.bat"
@echo off
setlocal

if "%~1"=="" (
  echo Usage: %~nx0 ^<module^> [args...]
  echo Example: %~nx0 basic_app_test
  exit /b 1
)

python3.10 -m tests.%*