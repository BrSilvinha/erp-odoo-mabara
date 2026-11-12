"""Genera data/plantilla_importacion_odoo.csv (import nativo de Odoo: Inventario > Productos > Importar).

Contiene los 11 registros reales de la Tabla V. Los 246 registros restantes del maestro de 257 NO estan en
el documento: se agregan al CSV cuando se disponga del Anexo (mismo formato, una fila por material).
"""
import csv
from odoo_client import ROOT

COLS = ["default_code", "name", "categ_id", "uom_id", "type", "is_storable", "abc_class", "old_codes",
        "short_name", "item_type", "description"]
UOM = {"m": "m", "unidad": "Units", "bolsa x100": "bolsa x100"}
src = ROOT / "data" / "maestro_materiales.csv"
dst = ROOT / "data" / "plantilla_importacion_odoo.csv"
with open(src, encoding="utf-8", newline="") as f, open(dst, "w", encoding="utf-8-sig", newline="") as g:
    w = csv.writer(g)
    w.writerow(COLS)
    for r in csv.DictReader(f):
        w.writerow([r["codigo_maestro"], r["descripcion_estandar"], "Goods / " + r["familia"], UOM[r["unidad"]],
                    "consu", "1", r["abc"], r["codigos_anteriores"], r["descripcion_corta"], r["tipo_item"],
                    r["observaciones"]])
print("Plantilla generada:", dst)
