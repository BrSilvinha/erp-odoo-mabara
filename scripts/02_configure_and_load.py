"""Fases 6 y 7 - Configura Odoo y carga el maestro de materiales del documento + datos DEMO.

Datos del documento: data/maestro_materiales.csv (Tabla V), data/familias_abc.csv (Tabla IV),
data/parametros_inventario.csv (Tablas XI-XIII).
Datos DEMO (NO provienen del documento): proveedores, ubicaciones, stock inicial, clientes.
Idempotente: se puede ejecutar varias veces.
"""
import csv
import pathlib
from odoo_client import ROOT, call, create, ref, search, search_read, write

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
import base64
logo = ROOT / "addons" / "mabara_theme" / "static" / "img" / "logo_mabara.png"
if logo.exists():
    write("res.company", [1], {"name": "MABARA CONTRATISTAS GENERALES SCRL",
                               "logo": base64.b64encode(logo.read_bytes()).decode()})

# ---------------------------------------------------------------- 2. Unidades
print("== Unidades de medida")


def get_uom(candidates, create_name=None):
    for c in candidates:
        ids = search("uom.uom", [["name", "=", c]])
        if ids:
            return ids[0]
    if create_name:
        return create("uom.uom", {"name": create_name})
    raise SystemExit("No se encontro UoM: %s" % candidates)


UOM = {
    "m": get_uom(["m", "Metro", "Meter"]),
    "unidad": get_uom(["Unidades", "Unidad", "Units", "Unit"]),
    "bolsa x100": get_uom(["bolsa x100"], create_name="bolsa x100"),
}
print("  ", UOM)

# ---------------------------------------------------------------- 3. Familias (categorias)
print("== Familias de materiales (14)")
parent = ref("product.product_category_goods")
CATEG = {}
for r in rows("familias_abc.csv"):
    ids = search("product.category", [["name", "=", r["familia"]]])
    if ids:
        write("product.category", ids, {"parent_id": parent})
    CATEG[r["familia"]] = ids[0] if ids else create("product.category", {"name": r["familia"], "parent_id": parent})

# ---------------------------------------------------------------- 4. Ubicaciones (DEMO)
print("== Ubicaciones DEMO")
stock_loc = ref("stock.stock_location_stock")
LOC = {}
for n in ["A-CABLES", "B-FIJACION", "C-TUBERIAS", "D-VARIOS"]:
    ids = search("stock.location", [["name", "=", n], ["location_id", "=", stock_loc]])
    LOC[n] = ids[0] if ids else create("stock.location", {"name": n, "location_id": stock_loc, "usage": "internal"})

# ---------------------------------------------------------------- 5. Productos (documento)
print("== Maestro de materiales (11 registros de la Tabla V)")
params = {r["codigo_maestro"]: r for r in rows("parametros_inventario.csv")}
buy = search("stock.route", [["rule_ids.action", "=", "buy"]], limit=1)
PROD = {}
for r in rows("maestro_materiales.csv"):
    code = r["codigo_maestro"]
    vals = {
        "name": r["descripcion_estandar"], "default_code": code, "type": "consu", "is_storable": True,
        "categ_id": CATEG[r["familia"]], "uom_id": UOM[r["unidad"]], "sale_ok": True, "purchase_ok": True,
        "abc_class": r["abc"], "old_codes": r["codigos_anteriores"], "short_name": r["descripcion_corta"],
        "item_type": r["tipo_item"], "description": r["observaciones"], "active": r["estado"] == "Activo",
        "route_ids": [(6, 0, buy)],
    }
    p = params.get(code)
    if p:
        vals.update({
            "standard_price": float(p["costo_unitario_C"]), "annual_demand": float(p["demanda_anual_D"]),
            "holding_rate": float(p["tasa_mantenimiento"]), "order_cost": float(p["costo_pedido_S"]),
            "monthly_demand": float(p["demanda_mensual_d"]), "monthly_sigma": float(p["desv_mensual"]),
            "lead_time_months": float(p["lead_time_meses"]), "service_z": float(p["z"]),
            "eoq_official": float(p["eoq"]), "safety_stock_official": float(p["stock_seguridad"]),
            "reorder_point_official": float(p["punto_reorden"]),
        })
    ids = search("product.template", [["default_code", "=", code]])
    if ids:
        write("product.template", ids, vals)
        PROD[code] = ids[0]
    else:
        PROD[code] = create("product.template", vals)
print("  ", len(PROD), "materiales")

# ---------------------------------------------------------------- 6. Proveedores y clientes (DEMO)
print("== Proveedores y cliente DEMO")


def partner(name, **extra):
    ids = search("res.partner", [["name", "=", name]])
    return ids[0] if ids else create("res.partner", dict(name=name, **extra))


SUP1 = partner("Proveedor Eléctrico Andino S.A.C. (DEMO)", supplier_rank=1)
SUP2 = partner("Distribuidora Industrial Lima S.A.C. (DEMO)", supplier_rank=1)
partner("Cliente DEMO - Distribuidora Eléctrica (servicio)", customer_rank=1)

# precios: MAT-0001..0003 = costo del documento (prov. 1) y +5 % (prov. 2, DEMO); MAT-0006 DEMO
PRICES = {"MAT-0001": (6.50, 6.83), "MAT-0002": (6.20, 6.51), "MAT-0003": (6.10, 6.41), "MAT-0006": (12.50, 11.80)}
for code, (p1, p2) in PRICES.items():
    for partner_id, price in ((SUP1, p1), (SUP2, p2)):
        if not search("product.supplierinfo", [["partner_id", "=", partner_id], ["product_tmpl_id", "=", PROD[code]]]):
            create("product.supplierinfo", {"partner_id": partner_id, "product_tmpl_id": PROD[code],
                                            "price": price, "min_qty": 0, "delay": 7})

# ---------------------------------------------------------------- 7. Politica de inventario
print("== Politica de inventario (ROP -> minimo, EOQ -> multiplo, lead time 0.23 meses = 7 dias)")
for code in params:
    call("product.template", "action_apply_inventory_policy", [[PROD[code]]])

# ---------------------------------------------------------------- 8. Stock inicial DEMO
print("== Stock inicial DEMO")
STOCK = {"MAT-0001": ("A-CABLES", 5000), "MAT-0002": ("B-FIJACION", 1800), "MAT-0003": ("B-FIJACION", 1200),
         "MAT-0004": ("C-TUBERIAS", 150), "MAT-0005": ("D-VARIOS", 500), "MAT-0006": ("C-TUBERIAS", 40),
         "MAT-0007": ("D-VARIOS", 60), "MAT-0008": ("D-VARIOS", 30), "MAT-0009": ("D-VARIOS", 25),
         "MAT-0010": ("D-VARIOS", 300), "MAT-0011": ("C-TUBERIAS", 80)}
for code, (loc, qty) in STOCK.items():
    pid = search("product.product", [["product_tmpl_id", "=", PROD[code]]])[0]
    if search_read("stock.quant", [["product_id", "=", pid], ["location_id", "=", LOC[loc]]], ["quantity"]):
        continue
    qid = create("stock.quant", {"product_id": pid, "location_id": LOC[loc], "inventory_quantity": qty},
                 ctx={"inventory_mode": True})
    call("stock.quant", "action_apply_inventory", [[qid]])
print("Listo.")

