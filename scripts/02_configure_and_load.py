"""Fases 6 y 7 - Configura Odoo y carga el maestro REAL de 257 materiales (data/materiales_257.csv).

NO crea proveedores, clientes, ubicaciones, stock ni ordenes de servicio de prueba (eso es opcional: 06_demo_data.py).
La clasificacion ABC no viene en el Excel y se deja vacia (no se inventa).
Idempotente: se puede ejecutar varias veces.
"""
import base64
import csv
from odoo_client import ROOT, call, create, ref, search, write

DATA = ROOT / "data"


def rows(name):
    with open(DATA / name, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------- 1. Ajustes
print("== Ajustes generales")
fields = call("res.config.settings", "fields_get", [], {"attributes": ["type"]})
want = {"group_stock_multi_locations": True,         # ubicaciones de almacen
        "group_product_variant": True,               # pestana "Atributos y variantes"
        "po_order_approval": True,                   # aprobacion de OC
        "po_double_validation_amount": 1000.0}       # OC >= S/ 1,000 requiere aprobacion
vals = {k: v for k, v in want.items() if k in fields}
print("   ajustes aplicados:", vals, "| no disponibles:", [k for k in want if k not in fields])
sid = create("res.config.settings", vals)
call("res.config.settings", "execute", [[sid]])

# ---------------------------------------------------------------- 1b. Empresa y logo
print("== Empresa y logo")
logo = ROOT / "addons" / "mabara_theme" / "static" / "img" / "logo_mabara.png"
if logo.exists():
    write("res.company", [1], {"name": "MABARA CONTRATISTAS GENERALES SCRL",
                               "logo": base64.b64encode(logo.read_bytes()).decode()})

data = rows("materiales_257.csv")

# ---------------------------------------------------------------- 2. Unidades
print("== Unidades de medida")
UOM = {}
NATIVE = {"m": ["m", "Metro", "Meter"], "unidad": ["Unidades", "Unidad", "Units", "Unit"]}
for u in sorted({r["unidad"] for r in data}):
    ids = []
    for cand in NATIVE.get(u, [u]):
        ids = search("uom.uom", [["name", "=", cand]])
        if ids:
            break
    UOM[u] = ids[0] if ids else create("uom.uom", {"name": u})
print("  ", UOM)

# ---------------------------------------------------------------- 3. Familias (categorias del Excel)
print("== Familias de materiales")
parent = ref("product.product_category_goods")
CATEG = {}
for fam in sorted({r["familia"] for r in data}):
    ids = search("product.category", [["name", "=", fam]])
    if ids:
        write("product.category", ids, {"parent_id": parent})
    CATEG[fam] = ids[0] if ids else create("product.category", {"name": fam, "parent_id": parent})
print("  ", len(CATEG), "familias")

# ---------------------------------------------------------------- 4. Productos
print("== Maestro de materiales (%d registros de MABARA_257)" % len(data))
buy = search("stock.route", [["rule_ids.action", "=", "buy"]], limit=1)
PROD = {}
for r in data:
    code = r["codigo_maestro"]
    vals = {
        "name": r["descripcion"], "default_code": code, "type": "consu", "is_storable": True,
        "categ_id": CATEG[r["familia"]], "uom_id": UOM[r["unidad"]], "sale_ok": True, "purchase_ok": True,
        "standard_price": float(r["costo"]), "annual_demand": float(r["demanda_anual"]),
        "holding_rate": float(r["tasa_mant"]), "order_cost": float(r["costo_pedido"]),
        "monthly_demand": float(r["demanda_mensual"]), "monthly_sigma": float(r["desv_mensual"]),
        "lead_time_months": float(r["lead_time_meses"]), "service_z": float(r["z"]),
        "eoq_official": float(r["eoq"]), "safety_stock_official": float(r["stock_seguridad"]),
        "reorder_point_official": float(r["rop"]), "route_ids": [(6, 0, buy)],
    }
    ids = search("product.template", [["default_code", "=", code]])
    if ids:
        write("product.template", ids, vals)
        PROD[code] = ids[0]
    else:
        PROD[code] = create("product.template", vals)
print("  ", len(PROD), "materiales")

# ---------------------------------------------------------------- 5. Reglas de reabastecimiento
# Se crean en modo MANUAL: con stock 0 el modo automatico generaria 257 solicitudes de cotizacion en el primer
# cron. Cuando cargue el stock real, cambie el disparador a "Automatico" en Inventario > Reglas de reabastecimiento.
print("== Reglas de reabastecimiento (ROP -> minimo, ROP+EOQ -> maximo, lead time 0.23 meses = 7 dias)")
skipped = []
for r in data:
    if float(r["rop"]) > 0 and float(r["eoq"]) > 0:
        call("product.template", "action_apply_inventory_policy", [[PROD[r["codigo_maestro"]]]])
    else:
        skipped.append(r["codigo_maestro"])
ops = search("stock.warehouse.orderpoint", [])
write("stock.warehouse.orderpoint", ops, {"trigger": "manual"})
print("  ", len(ops), "reglas (disparador manual); sin regla por ROP/EOQ = 0 en el Excel:", len(skipped), skipped)
print("Listo.")
