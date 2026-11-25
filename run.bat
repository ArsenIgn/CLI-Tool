@echo off
setlocal
set "PYTHONPATH=%~dp0;%PYTHONPATH%"
python -m src.main %*
exit /b %errorlevel%
