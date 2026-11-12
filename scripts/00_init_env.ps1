# Crea .env y config\odoo.conf con claves aleatorias (solo si no existen). Es seguro ejecutarlo varias veces.
$root = Split-Path $PSScriptRoot -Parent
$envFile = Join-Path $root ".env"
$confFile = Join-Path $root "config\odoo.conf"

function New-Pw { -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 20 | ForEach-Object { [char]$_ }) }

if (-not (Test-Path $envFile)) {
    $lines = @(
        "POSTGRES_USER=odoo",
        "POSTGRES_PASSWORD=$(New-Pw)",
        "POSTGRES_DB=postgres",
        "ODOO_ADMIN_PASSWD=$(New-Pw)",
        "ODOO_DB_NAME=mabara_erp",
        "ODOO_USER=admin@mabara.demo",
        "ODOO_USER_PASSWORD=$(New-Pw)"
    )
    Set-Content -Path $envFile -Value $lines -Encoding ascii
    Write-Host "Creado .env con claves aleatorias"
}

if (-not (Test-Path $confFile)) {
    $e = @{}
    Get-Content $envFile | Where-Object { $_ -match "=" } | ForEach-Object { $k, $v = $_ -split "=", 2; $e[$k] = $v }
    New-Item -ItemType Directory -Force (Split-Path $confFile) | Out-Null
    $conf = @(
        "[options]",
        "admin_passwd = $($e['ODOO_ADMIN_PASSWD'])",
        "db_host = db",
        "db_port = 5432",
        "db_user = $($e['POSTGRES_USER'])",
        "db_password = $($e['POSTGRES_PASSWORD'])",
        "addons_path = /mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons",
        "list_db = True",
        "dbfilter = ^$($e['ODOO_DB_NAME'])`$"
    )
    Set-Content -Path $confFile -Value $conf -Encoding ascii
    Write-Host "Creado config\odoo.conf"
}
