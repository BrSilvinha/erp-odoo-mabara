@echo off
rem Instala todo el ERP MABARA con doble clic (requiere Docker Desktop encendido y Python en el PATH).
rem Parametros opcionales:  INSTALAR.bat -Reset   (borra la base y reconstruye)   |   INSTALAR.bat -Demo  (agrega datos de prueba)
cd /d "%~dp0"
echo ==============================================
echo   Instalador ERP Odoo - MABARA
echo ==============================================

where docker >nul 2>&1
if errorlevel 1 (
  echo [ERROR] No se encontro Docker. Instale Docker Desktop: https://www.docker.com/products/docker-desktop/
  pause & exit /b 1
)
docker info >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Docker Desktop no esta encendido. Abralo, espere a que diga "Engine running" y vuelva a ejecutar este archivo.
  pause & exit /b 1
)
where python >nul 2>&1
if errorlevel 1 (
  echo [ERROR] No se encontro Python. Instalelo desde https://www.python.org/downloads/ marcando "Add python.exe to PATH".
  pause & exit /b 1
)

echo Requisitos OK. Instalando (la primera vez tarda 15-25 minutos por la descarga de imagenes)...
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\setup_all.ps1 %*
if errorlevel 1 (
  echo [ERROR] La instalacion termino con errores. Revise los mensajes anteriores.
  pause & exit /b 1
)
start http://localhost:8069
pause
