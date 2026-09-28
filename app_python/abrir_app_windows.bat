@echo off
REM Doble clic para abrir la aplicacion de los planes.
cd /d "%~dp0"
py -3 ejecutar.py 2>nul
if errorlevel 1 python ejecutar.py
if errorlevel 1 (
  echo.
  echo No se pudo iniciar. Verifique que Python este instalado: https://www.python.org/downloads/
  pause
)
