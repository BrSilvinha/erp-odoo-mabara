"""Fase 4 - Crea la base de datos mabara_erp (idempotente)."""
import xmlrpc.client, pathlib
env = dict(l.strip().split("=", 1) for l in pathlib.Path(__file__).parent.parent.joinpath(".env").read_text().splitlines() if "=" in l)
url = "http://localhost:8069"
db = xmlrpc.client.ServerProxy(url + "/xmlrpc/2/db")
if env["ODOO_DB_NAME"] in db.list():
    print("La base ya existe:", env["ODOO_DB_NAME"])
else:
    db.create_database(env["ODOO_ADMIN_PASSWD"], env["ODOO_DB_NAME"], False, "es_PE",
                       env["ODOO_USER_PASSWORD"], env["ODOO_USER"], "pe")
    print("Base creada:", env["ODOO_DB_NAME"])
