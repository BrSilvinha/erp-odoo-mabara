"""Carga las fotos de los materiales desde addons/mabara_theme/static/img (nombre de archivo = nombre del material).
Empareja por nombre normalizado (sin tildes, simbolos ni mayusculas); si no hay coincidencia unica la omite."""
import base64
import re
import unicodedata

from odoo_client import ROOT, call, search_read


def norm(txt):
    txt = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", txt)


img_dir = ROOT / "addons" / "mabara_theme" / "static" / "img"
products = search_read("product.template", [["default_code", "!=", False]], ["name", "default_code"],
                       context={"active_test": False}) if False else search_read(
    "product.template", [["default_code", "!=", False]], ["name", "default_code"])
loaded = 0
for f in sorted(img_dir.iterdir()):
    if f.suffix.lower() not in (".jpg", ".jpeg", ".png") or f.name.startswith("logo"):
        continue
    key = norm(f.stem)
    cands = [p for p in products if norm(p["name"]) == key] or \
            [p for p in products if key and (norm(p["name"]).startswith(key) or key.startswith(norm(p["name"])[:20]))]
    if len(cands) != 1:
        print("sin coincidencia unica para imagen:", f.name, len(cands))
        continue
    call("product.template", "write", [[cands[0]["id"]], {"image_1920": base64.b64encode(f.read_bytes()).decode()}])
    loaded += 1
    print("imagen cargada:", cands[0]["default_code"], "<-", f.name)
print("Imagenes cargadas:", loaded)
