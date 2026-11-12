"""Fase 8 - Ejecuta los escenarios A (stock suficiente), B (stock insuficiente) y C (ROP/EOQ) +
pruebas de politicas. Escribe la evidencia en evidencias/escenarios.md
"""
import datetime
import xmlrpc.client
from odoo_client import ROOT, call, create, read, search, search_read, write

LOG = []


def log(txt=""):
    print(txt)
    LOG.append(txt)


def pid(code):
    return search("product.product", [["default_code", "=", code]])[0]


def stock(code):
    return read("product.product", [pid(code)], ["qty_available", "free_qty"])[0]


def os_state(oid):
    o = read("mabara.service.order", [oid], ["name", "state"])[0]
    return o["name"], o["state"]


def show_lines(oid):
    for l in search_read("mabara.service.order.line", [["order_id", "=", oid]],
                         ["product_id", "product_qty", "available_qty", "reserved_qty", "shortage_qty"]):
        log("| %s | %g | %g | %g | %g |" % (l["product_id"][1][:55], l["product_qty"], l["available_qty"],
                                            l["reserved_qty"], l["shortage_qty"]))


def new_os(desc, items):
    partner = search("res.partner", [["name", "like", "Cliente DEMO"]])[0]
    return create("mabara.service.order", {
        "partner_id": partner, "service_description": desc,
        "line_ids": [(0, 0, {"product_id": pid(c), "product_qty": q}) for c, q in items]})


def validate_picking(pk):
    res = call("stock.picking", "button_validate", [[pk]])
    if isinstance(res, dict):                      # asistente (backorder / inmediata)
        wiz = res.get("res_model")
        ctx = res.get("context", {})
        wid = create(wiz, {}, ctx=ctx)
        call(wiz, "process", [[wid]], {"context": ctx})
    return read("stock.picking", [pk], ["name", "state"])[0]


def step(n, txt):
    log("\n**Paso %s.** %s" % (n, txt))


def deliver(oid):
    pk = search("stock.picking", [["service_order_id", "=", oid], ["state", "not in", ["done", "cancel"]]])[0]
    r = validate_picking(pk)
    log("- Despacho `%s` -> estado **%s**" % (r["name"], r["state"]))


log("# Evidencias de simulacion - MABARA ERP (Odoo 19 Community)")
log("Generado: %s\n" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
log("> Stock inicial, proveedores, precios de MAT-0006 y cliente son datos DEMO (no provienen del documento).")

# ======================================================================= ESCENARIO A
log("\n---\n## Escenario A - Stock disponible")
a_before = {c: stock(c)["qty_available"] for c in ("MAT-0001", "MAT-0002", "MAT-0003")}
log("Stock inicial: " + ", ".join("%s=%g" % kv for kv in a_before.items()))
oa = new_os("Instalacion de tendido electrico (Escenario A)",
            [("MAT-0001", 300), ("MAT-0002", 100), ("MAT-0003", 50)])
step(1, "Solicitud registrada: %s (estado %s)" % os_state(oa))
call("mabara.service.order", "action_issue", [[oa]])
step(2, "OS emitida -> %s / %s" % os_state(oa))
call("mabara.service.order", "action_check_stock", [[oa]])
step(3, "Verificar existencias y reservar -> %s / %s" % os_state(oa))
log("| Material | Requerido | Disponible | Reservado | Faltante |\n|---|---|---|---|---|")
show_lines(oa)
step(4, "Entrega (despacho a la OS)")
deliver(oa)
log("- OS -> %s / %s" % os_state(oa))
call("mabara.service.order", "action_execute", [[oa]])
call("mabara.service.order", "action_close", [[oa]])
step(5, "Ejecucion y cierre -> %s / %s" % os_state(oa))
a_after = {c: stock(c)["qty_available"] for c in a_before}
log("Stock final: " + ", ".join("%s=%g (antes %g)" % (c, a_after[c], a_before[c]) for c in a_after))
assert os_state(oa)[1] == "closed" and a_after["MAT-0001"] == a_before["MAT-0001"] - 300
log("\n**RESULTADO A: OK**")

# ======================================================================= ESCENARIO B
log("\n---\n## Escenario B - Stock insuficiente (compra)")
b0 = stock("MAT-0006")["qty_available"]
log("Stock inicial MAT-0006 (Tubo SAP 3/4\" x 3 m) = %g" % b0)
ob = new_os("Canalizacion de acometida (Escenario B)", [("MAT-0006", 120), ("MAT-0004", 50)])
call("mabara.service.order", "action_issue", [[ob]])
call("mabara.service.order", "action_check_stock", [[ob]])
step(1, "OS %s / %s - faltante detectado" % os_state(ob))
log("| Material | Requerido | Disponible | Reservado | Faltante |\n|---|---|---|---|---|")
show_lines(ob)
assert os_state(ob)[1] == "waiting_supply"

call("mabara.service.order", "action_create_purchase_request", [[ob]])
pr = search("mabara.purchase.request", [["service_order_id", "=", ob]])[0]
prr = read("mabara.purchase.request", [pr], ["name", "state"])[0]
step(2, "Solicitud de compra generada: **%s** (%s)" % (prr["name"], prr["state"]))
for l in search_read("mabara.purchase.request.line", [["request_id", "=", pr]], ["product_id", "product_qty"]):
    log("- %s: %g" % (l["product_id"][1], l["product_qty"]))
call("mabara.purchase.request", "action_submit", [[pr]])
call("mabara.purchase.request", "action_approve", [[pr]])
step(3, "Solicitud revisada y aprobada -> %s" % read("mabara.purchase.request", [pr], ["state"])[0]["state"])
call("mabara.purchase.request", "action_create_rfq", [[pr]])
rfqs = search_read("purchase.order", [["purchase_request_id", "=", pr]],
                   ["name", "partner_id", "amount_total", "state", "alternative_po_ids"], order="id")
step(4, "Cotizaciones solicitadas y comparadas")
log("| RFQ | Proveedor | Total (PEN) | Estado |\n|---|---|---|---|")
for r in rfqs:
    log("| %s | %s | %.2f | %s |" % (r["name"], r["partner_id"][1], r["amount_total"], r["state"]))
best = min(rfqs, key=lambda r: r["amount_total"])
log("- Proveedor seleccionado (menor precio): **%s**" % best["partner_id"][1])

res = call("purchase.order", "button_confirm", [[best["id"]]])
if isinstance(res, dict) and res.get("res_model"):            # asistente de alternativas
    wiz = res["res_model"]
    ctx = res.get("context", {})
    wid = create(wiz, {}, ctx=ctx)
    try:
        call(wiz, "action_cancel_alternatives", [[wid]], {"context": ctx})
    except xmlrpc.client.Fault:
        call(wiz, "action_keep_alternatives", [[wid]], {"context": ctx})
po = read("purchase.order", [best["id"]], ["name", "state", "picking_ids"])[0]
if po["state"] == "to approve":
    call("purchase.order", "button_approve", [[best["id"]]])
    po = read("purchase.order", [best["id"]], ["name", "state", "picking_ids"])[0]
step(5, "Orden de Compra **%s** -> estado **%s**" % (po["name"], po["state"]))
others = search_read("purchase.order", [["purchase_request_id", "=", pr], ["id", "!=", best["id"]]], ["name", "state"])
log("- Otras cotizaciones: " + ", ".join("%s (%s)" % (o["name"], o["state"]) for o in others))
assert po["state"] == "purchase"

rc = po["picking_ids"][0]
validate_picking(rc)
rcr = read("stock.picking", [rc], ["name", "state"])[0]
step(6, "Recepcion `%s` validada contra la OC -> **%s**" % (rcr["name"], rcr["state"]))
log("- Stock MAT-0006: %g -> %g" % (b0, stock("MAT-0006")["qty_available"]))

call("mabara.service.order", "action_reserve", [[ob]])
step(7, "Reserva tras abastecimiento -> %s / %s" % os_state(ob))
log("| Material | Requerido | Disponible | Reservado | Faltante |\n|---|---|---|---|---|")
show_lines(ob)
step(8, "Entrega de materiales")
deliver(ob)
log("- OS -> %s / %s" % os_state(ob))
call("mabara.service.order", "action_execute", [[ob]])
call("mabara.service.order", "action_close", [[ob]])
step(9, "Ejecucion y cierre -> %s / %s" % os_state(ob))
log("Stock final MAT-0006 = %g (80 comprados + 40 existentes - 120 entregados)" % stock("MAT-0006")["qty_available"])
assert os_state(ob)[1] == "closed" and stock("MAT-0006")["qty_available"] == 0
log("\n**RESULTADO B: OK**")

# ======================================================================= ESCENARIO C
log("\n---\n## Escenario C (adicional) - Regla de reabastecimiento ROP / EOQ (MAT-0001)")
c0 = stock("MAT-0001")["qty_available"]
log("Stock MAT-0001 = %g m | ROP = 3492 | EOQ = 4398 | max = ROP+EOQ = 7890" % c0)
oc = new_os("Tendido de red secundaria (Escenario C)", [("MAT-0001", 1210)])
call("mabara.service.order", "action_issue", [[oc]])
call("mabara.service.order", "action_check_stock", [[oc]])
deliver(oc)
c1 = stock("MAT-0001")["qty_available"]
log("Tras despachar 1,210 m: stock = %g m (< ROP 3,492)" % c1)
cron = search("ir.cron", [["cron_name", "=", "Procurement: run scheduler"]])
call("ir.cron", "method_direct_trigger", [cron])
rules = search_read("purchase.order.line", [["product_id", "=", pid("MAT-0001")], ["order_id.state", "=", "draft"],
                                            ["orderpoint_id", "!=", False]],
                    ["order_id", "product_qty", "orderpoint_id"])
log("Programador de reabastecimiento ejecutado. RFQ generadas por la regla:")
for r in rules:
    log("- %s | cantidad %g m | regla %s" % (r["order_id"][1], r["product_qty"], r["orderpoint_id"][1]))
assert rules, "la regla ROP no genero la necesidad de compra"
call("purchase.order", "button_confirm", [[rules[0]["order_id"][0]]])
log("- RFQ originada por regla de reabastecimiento puede confirmarse sin solicitud manual (politica 4).")
log("\n**RESULTADO C: OK**")

# ======================================================================= POLITICAS
log("\n---\n## Pruebas de politicas (deben ser rechazadas)")
# Politica 8: salida sin OS
std_out = search("stock.picking.type", [["code", "=", "outgoing"], ["name", "not like", "Orden de Servicio"]], limit=1)[0]
pt = read("stock.picking.type", [std_out], ["default_location_src_id", "default_location_dest_id"])[0]
mv = {"product_id": pid("MAT-0005"), "product_uom_qty": 5, "product_uom": 1,
      "location_id": pt["default_location_src_id"][0], "location_dest_id": pt["default_location_dest_id"][0]}
if "name" in call("stock.move", "fields_get", [], {"attributes": ["type"]}):
    mv["name"] = "prueba politica 8"
pk = create("stock.picking", {"picking_type_id": std_out, "location_id": mv["location_id"],
                               "location_dest_id": mv["location_dest_id"], "move_ids": [(0, 0, mv)]})
call("stock.picking", "action_confirm", [[pk]])
call("stock.picking", "action_assign", [[pk]])
try:
    call("stock.picking", "button_validate", [[pk]])
    log("- Politica 8 (salida sin OS): **NO se bloqueo** (FALLO)")
    raise SystemExit(1)
except xmlrpc.client.Fault as e:
    log("- Politica 8 (salida sin OS): bloqueada -> `%s`" % [l for l in str(e).splitlines() if "Politica" in l][0][:140]
        if "Politica" in str(e) else "- Politica 8: bloqueada")
# Politicas 4/5: OC sin solicitud
sup = search("res.partner", [["name", "like", "Proveedor Eléctrico"]])[0]
po = create("purchase.order", {"partner_id": sup, "order_line": [(0, 0, {"product_id": pid("MAT-0005"), "product_qty": 10})]})
try:
    call("purchase.order", "button_confirm", [[po]])
    log("- Politicas 4/5 (OC sin solicitud): **NO se bloqueo** (FALLO)")
    raise SystemExit(1)
except xmlrpc.client.Fault as e:
    log("- Politicas 4/5 (OC sin solicitud ni regla): bloqueada")
call("purchase.order", "button_cancel", [[po]])
# Politica: ejecutar sin entregar materiales
od = new_os("Prueba flujo", [("MAT-0005", 1)])
try:
    call("mabara.service.order", "action_execute", [[od]])
    raise SystemExit("FALLO: permitio ejecutar sin entrega")
except xmlrpc.client.Fault:
    log("- Ejecutar una OS sin materiales entregados: bloqueado")
call("mabara.service.order", "action_cancel", [[od]])
log("\n**RESULTADO POLITICAS: OK**")

out = ROOT / "evidencias" / "escenarios.md"
out.write_text("\n".join(LOG), encoding="utf-8")
print("\nEvidencia escrita en", out)

