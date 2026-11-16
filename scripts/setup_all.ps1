# Reconstruye todo el entorno MABARA ERP desde cero (Fases 3-8).
# ATENCION: -Reset elimina los volumenes de ESTE proyecto (mabara_erp_*), no los de otros proyectos.
# -Demo agrega datos de prueba (proveedores, cliente, stock) y ejecuta los escenarios; sin -Demo solo se cargan los 257 materiales.
param([switch]$Reset, [switch]$Demo)
$ErrorActionPreference = "Continue"
Set-Location (Split-Path $PSScriptRoot -Parent)
& (Join-Path $PSScriptRoot "00_init_env.ps1")

if ($Reset) { docker compose down -v }
docker compose up -d db
Write-Host "Esperando PostgreSQL..."
do { Start-Sleep 2 } until ((docker inspect -f '{{.State.Health.Status}}' mabara_db) -eq "healthy")

docker compose up -d odoo
do { Start-Sleep 3; try { $ok = (Invoke-WebRequest http://localhost:8069/web/login -UseBasicParsing).StatusCode -eq 200 } catch { $ok = $false } } until ($ok)

python scripts/01_create_db.py
Write-Host "Instalando modulos (stock, purchase, sale, account, l10n_pe, mabara_service_order, mabara_theme)..."
docker compose run --rm -T odoo odoo -d mabara_erp -i stock,purchase,purchase_requisition,sale_management,account,l10n_pe,mabara_service_order,mabara_theme --stop-after-init --log-level=warn
docker compose restart odoo
do { Start-Sleep 3; try { $ok = (Invoke-WebRequest http://localhost:8069/web/login -UseBasicParsing).StatusCode -eq 200 } catch { $ok = $false } } until ($ok)

python scripts/02_configure_and_load.py
python scripts/05_load_product_images.py
if ($Demo) {
    # Opcional: datos de prueba (NO reales) y escenarios A-H
    python scripts/06_demo_data.py
    python scripts/03_run_scenarios.py
}
$envv = @{}; Get-Content .env | Where-Object { $_ -match "=" } | ForEach-Object { $k, $v = $_ -split "=", 2; $envv[$k] = $v }
Write-Host "Listo: http://localhost:8069"
Write-Host "Usuario: $($envv['ODOO_USER'])   Clave: $($envv['ODOO_USER_PASSWORD'])   (tambien en el archivo .env)"
