"""OPCIONAL - Datos DEMO (NO reales): ubicaciones, 2 proveedores, 1 cliente y stock inicial de MAT-0001..0011.
Solo para ejecutar los escenarios de prueba (03_run_scenarios.py) con setup_all.ps1 -Demo."""
from odoo_client import call, create, ref, search, search_read

print("== Ubicaciones DEMO")
stock_loc = ref("stock.stock_location_stock")
LOC = {}
for n in ["A-CABLES", "B-FIJACION", "C-TUBERIAS", "D-VARIOS"]:
    ids = search("stock.location", [["name", "=", n], ["location_id", "=", stock_loc]])
    LOC[n] = ids[0] if ids else create("stock.location", {"name": n, "location_id": stock_loc, "usage": "internal"})


def partner(name, **extra):
    ids = search("res.partner", [["name", "=", name]])
    return ids[0] if ids else create("res.partner", dict(name=name, **extra))


print("== Proveedores y cliente DEMO")
SUP1 = partner("Proveedor Eléctrico Andino S.A.C. (DEMO)", supplier_rank=1)
SUP2 = partner("Distribuidora Industrial Lima S.A.C. (DEMO)", supplier_rank=1)
partner("Cliente DEMO - Distribuidora Eléctrica (servicio)", customer_rank=1)


def tmpl(code):
    return search("product.template", [["default_code", "=", code]])[0]


PRICES = {"MAT-0001": (6.50, 6.83), "MAT-0002": (6.20, 6.51), "MAT-0003": (6.10, 6.41), "MAT-0006": (12.50, 11.80)}
for code, (p1, p2) in PRICES.items():
    for partner_id, price in ((SUP1, p1), (SUP2, p2)):
        if not search("product.supplierinfo", [["partner_id", "=", partner_id], ["product_tmpl_id", "=", tmpl(code)]]):
            create("product.supplierinfo", {"partner_id": partner_id, "product_tmpl_id": tmpl(code),
                                            "price": price, "min_qty": 0, "delay": 7})

print("== Stock inicial DEMO")
STOCK = {"MAT-0001": ("A-CABLES", 5000), "MAT-0002": ("B-FIJACION", 1800), "MAT-0003": ("B-FIJACION", 1200),
         "MAT-0004": ("C-TUBERIAS", 150), "MAT-0005": ("D-VARIOS", 500), "MAT-0006": ("C-TUBERIAS", 40),
         "MAT-0007": ("D-VARIOS", 60), "MAT-0008": ("D-VARIOS", 30), "MAT-0009": ("D-VARIOS", 25),
         "MAT-0010": ("D-VARIOS", 300), "MAT-0011": ("C-TUBERIAS", 80)}
for code, (loc, qty) in STOCK.items():
    pid = search("product.product", [["product_tmpl_id", "=", tmpl(code)]])[0]
    if search_read("stock.quant", [["product_id", "=", pid], ["location_id", "=", LOC[loc]]], ["quantity"]):
        continue
    qid = create("stock.quant", {"product_id": pid, "location_id": LOC[loc], "inventory_quantity": qty},
                 ctx={"inventory_mode": True})
    call("stock.quant", "action_apply_inventory", [[qid]])
print("Listo.")
