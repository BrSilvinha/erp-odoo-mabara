"""Cliente XML-RPC minimo para Odoo 19 (usa las credenciales de ../.env)."""
import pathlib
import xmlrpc.client

ROOT = pathlib.Path(__file__).resolve().parent.parent
ENV = dict(l.strip().split("=", 1) for l in ROOT.joinpath(".env").read_text(encoding="utf-8").splitlines() if "=" in l)
URL = "http://localhost:8069"
DB = ENV["ODOO_DB_NAME"]
LOGIN = ENV["ODOO_USER"]
PWD = ENV["ODOO_USER_PASSWORD"]

_common = xmlrpc.client.ServerProxy(URL + "/xmlrpc/2/common", allow_none=True)
UID = _common.authenticate(DB, LOGIN, PWD, {})
_obj = xmlrpc.client.ServerProxy(URL + "/xmlrpc/2/object", allow_none=True)


def call(model, method, args=None, kwargs=None):
    try:
        return _obj.execute_kw(DB, UID, PWD, model, method, args or [], kwargs or {})
    except xmlrpc.client.Fault as e:
        # Odoo ejecuta el metodo pero no puede serializar un retorno None por XML-RPC
        if "cannot marshal None" in str(e):
            return None
        raise


def search(model, domain, **kw):
    return call(model, "search", [domain], kw)


def read(model, ids, fields):
    return call(model, "read", [ids], {"fields": fields})


def search_read(model, domain, fields, **kw):
    return call(model, "search_read", [domain], dict(fields=fields, **kw))


def create(model, vals, ctx=None):
    return call(model, "create", [vals], {"context": ctx or {}})


def write(model, ids, vals):
    return call(model, "write", [ids, vals])


def ref(xmlid):
    module, name = xmlid.split(".", 1)
    return call("ir.model.data", "search_read", [[["module", "=", module], ["name", "=", name]]],
                {"fields": ["res_id"], "limit": 1})[0]["res_id"]
