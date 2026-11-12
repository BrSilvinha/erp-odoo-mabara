"""Menu horizontal unico MABARA: Inventario, Ventas, Compras, Contabilidad, Informes, Configuracion.

Se crea una unica "aplicacion" MABARA cuyos menus de primer nivel se muestran en la barra superior.
Cada opcion reutiliza la accion nativa de Odoo (o la del modulo mabara_service_order); las acciones
que no existan en la instalacion se omiten.
"""

MENU = [
    ('Inventario', [
        ('Productos (maestro de materiales)', ['stock.product_template_action_product']),
        ('Familias de materiales', ['product.product_category_action_form']),
        ('Existencias', ['stock.action_view_inventory_tree']),
        ('Transferencias', ['stock.action_picking_tree_all']),
        ('Reabastecimiento', ['stock.action_orderpoint_replenish']),
        ('Reglas de reabastecimiento (ROP / EOQ)', ['stock.action_orderpoint']),
        ('Ubicaciones', ['stock.action_location_form']),
    ]),
    ('Ventas', [
        ('Ordenes de Servicio', ['mabara_service_order.action_service_order']),
        ('Cotizaciones', ['sale.action_quotations_with_onboarding']),
        ('Pedidos de venta', ['sale.action_orders']),
        ('Clientes', ['account.res_partner_action_customer']),
    ]),
    ('Compras', [
        ('Solicitudes de compra', ['mabara_service_order.action_purchase_request']),
        ('Solicitudes de cotizacion', ['purchase.purchase_rfq']),
        ('Ordenes de compra', ['purchase.purchase_form_action']),
        ('Acuerdos / alternativas', ['purchase_requisition.action_purchase_requisition']),
        ('Proveedores', ['account.res_partner_action_supplier']),
    ]),
    ('Contabilidad', [
        ('Facturas de clientes', ['account.action_move_out_invoice_type']),
        ('Facturas de proveedores', ['account.action_move_in_invoice_type']),
        ('Pagos', ['account.action_account_payments']),
        ('Asientos contables', ['account.action_account_moves_all_a']),
        ('Impuestos', ['account.action_tax_form']),
        ('Plan de cuentas', ['account.action_account_form']),
    ]),
    ('Informes', [
        ('Analisis de existencias', ['stock.action_product_stock_view']),
        ('Movimientos de stock', ['stock.stock_move_line_action']),
        ('Analisis de compras', ['purchase.action_purchase_order_report_all']),
        ('Analisis de ventas', ['sale.report_all_channels_sales_action']),
    ]),
    ('Configuracion', [
        ('Ajustes', ['base.res_config_setting_act_window']),
        ('Companias', ['base.action_res_company_form']),
        ('Usuarios', ['base.action_res_users']),
        ('Almacenes', ['stock.action_warehouse_form']),
    ]),
]

ACCENTS = {'Ordenes': 'Órdenes', 'Cotizaciones': 'Cotizaciones', 'cotizacion': 'cotización',
           'Analisis': 'Análisis', 'Companias': 'Compañías', 'Configuracion': 'Configuración'}


def _label(txt):
    for k, v in ACCENTS.items():
        txt = txt.replace(k, v)
    return txt


KEEP_ROOTS = ('mail.menu_root_discuss', 'base.menu_administration')


def hide_native_apps(env):
    """Desactiva las aplicaciones nativas (Compras, Inventario, ...): todo se abre dentro del menu MABARA,
    asi la barra superior nunca cambia al menu propio de otra app."""
    keep = {env.ref(x, raise_if_not_found=False) for x in KEEP_ROOTS}
    keep = {m.id for m in keep if m}
    roots = env['ir.ui.menu'].search([('parent_id', '=', False), ('name', '!=', 'MABARA')])
    roots.filtered(lambda m: m.id not in keep).write({'active': False})


def post_init_hook(env):
    Menu = env['ir.ui.menu']
    if Menu.search([('name', '=', 'MABARA'), ('parent_id', '=', False)]):
        hide_native_apps(env)
        return
    root = Menu.create({'name': 'MABARA', 'sequence': 0})
    for seq, (section, items) in enumerate(MENU, start=1):
        children = []
        for item, xmlids in items:
            action = next((a for a in (env.ref(x, raise_if_not_found=False) for x in xmlids) if a), None)
            if action:
                children.append((item, action))
        if not children:
            continue
        parent = Menu.create({'name': _label(section), 'parent_id': root.id, 'sequence': seq * 10})
        for i, (item, action) in enumerate(children, start=1):
            Menu.create({'name': _label(item), 'parent_id': parent.id, 'sequence': i * 10,
                         'action': '%s,%d' % (action._name, action.id)})
    # Las apps nativas (incluido el antiguo "Servicios MABARA") quedan integradas en este menu
    hide_native_apps(env)
    # La empresa
    company = env.ref('base.main_company')
    company.write({'name': 'MABARA CONTRATISTAS GENERALES SCRL'})
