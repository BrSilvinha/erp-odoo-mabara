# Comandos utilizados y cambios realizados

## Estructura
```
ERP_EDOO/
├─ docker-compose.yml        Odoo 19.0 + PostgreSQL 16, volúmenes persistentes, puerto 8069
├─ .env                      credenciales (no se versiona)
├─ config/odoo.conf          conexión a PostgreSQL, dbfilter
├─ addons/mabara_service_order/   módulo personalizado
├─ data/                     CSV del documento y plantilla de importación
├─ scripts/                  01 crear BD · 02 configurar y cargar · 03 escenarios · 04 plantilla · setup_all.ps1
├─ docs/                     esta documentación
└─ evidencias/escenarios.md  resultado de las simulaciones
```

## Por fase
| Fase | Comando / acción |
|---|---|
| 2 | `docker --version`, `docker compose version`, `wsl --status`, `docker ps -a` (sólo lectura). Docker 29.2.1, WSL2 Ubuntu activo; puerto 5432 ocupado por otro proyecto → no se publica PostgreSQL |
| 3 | `docker pull odoo:19.0` · `docker compose up -d` |
| 4 | `python scripts/01_create_db.py` (idioma es_PE, país Perú, moneda PEN, sin datos demo de Odoo) |
| 5 | `docker compose run --rm odoo odoo -d mabara_erp -i stock,purchase,purchase_requisition,mabara_service_order --stop-after-init` |
| 6–7 | `python scripts/02_configure_and_load.py` (ubicaciones, aprobación de OC, familias, maestro, parámetros, reglas, proveedores, stock) |
| 8 | `python scripts/03_run_scenarios.py` |
| Todo | `scripts\setup_all.ps1 -Reset` |

## Módulos instalados
Inventario (`stock`), Compras (`purchase`), Acuerdos de compra (`purchase_requisition`, para comparar cotizaciones) y el módulo propio `mabara_service_order`. No se instalaron Ventas ni Proyecto: la gestión de servicios se resolvió con el módulo propio.

## Problemas encontrados y corregidos
1. **BOM en el manifiesto**: una edición con PowerShell añadió BOM UTF-8 y Odoo no cargaba el módulo → BOM eliminado.
2. **`qty_multiple` inexistente en Odoo 19** → política EOQ por máximo = ROP + EOQ.
3. **Métodos devolvían `None`** (no serializable por XML-RPC) → ahora devuelven `True`.
4. **Categorías bajo “Expenses”**: en Odoo 19 no existe la categoría “All” → familias bajo “Goods”.
5. **Programador**: en Odoo 19 es `stock.rule.run_scheduler`.
6. **Script no idempotente en escenarios** (datos duplicados al repetirlo) → `setup_all.ps1 -Reset` reconstruye limpio.

## Pendientes / límites
- El PDF no contiene los 246 materiales restantes ni los anexos; se cargaron los 11 materiales reales.
- Los diagramas del PDF (Fig. 1–10) son imágenes y no se analizaron; el flujo se basó en el texto y en la Tabla XVI.
- La API XML-RPC usada por los scripts está marcada como obsoleta en Odoo 19 (se retira en 22); la interfaz web no depende de ella.
