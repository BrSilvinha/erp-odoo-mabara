@echo off
rem Enciende el ERP ya instalado (sin reinstalar ni tocar los datos) y abre el navegador.
cd /d "%~dp0"
docker info >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Docker Desktop no esta encendido. Abralo, espere a que diga "Engine running" y vuelva a ejecutar este archivo.
  pause & exit /b 1
)
docker compose up -d
echo Esperando a Odoo...
:espera
timeout /t 3 /nobreak >nul
powershell -NoProfile -Command "try { if ((Invoke-WebRequest http://localhost:8069/web/login -UseBasicParsing).StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }"
if errorlevel 1 goto espera
start http://localhost:8069
echo Listo. Usuario: admin@mabara.demo   Clave: ver la linea ODOO_USER_PASSWORD del archivo .env
pause
