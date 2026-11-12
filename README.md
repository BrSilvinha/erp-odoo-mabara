# ERP Odoo MABARA – instalación y simulación

Implementación de Odoo 19.0 Community (Docker + PostgreSQL 16) basada en `ERP.pdf`: Ventas / Gestión de servicios,
Compras e Inventario, con parámetros ABC, EOQ, stock de seguridad y punto de reorden.

## Inicio rápido (Windows 11, Docker Desktop + WSL2)
1. `copy .env.example .env` y poner claves propias.
2. Crear `config\odoo.conf` a partir de `config\odoo.conf.example` con las mismas claves.
3. `powershell -ExecutionPolicy Bypass -File scripts\setup_all.ps1 -Reset` (⚠ `-Reset` borra los volúmenes `mabara_erp_*`).
4. Abrir <http://localhost:8069> (usuario y clave de demo en `.env`).

## Contenido
- `addons/mabara_service_order` – Orden de Servicio, solicitud de compra, políticas y campos EOQ/SS/ROP.
- `addons/mabara_theme` – menú horizontal, colores y ficha de material.
- `data/` – maestro (11 materiales del documento), familias ABC, parámetros, plantilla de importación.
- `scripts/` – creación de BD, carga de datos, escenarios A/B/C.
- `docs/` – guía de demostración, nativo vs. personalizado, comandos y cambios. `evidencias/` – resultados.

Los datos de stock inicial, proveedores y cliente son DEMO (no provienen del documento).
