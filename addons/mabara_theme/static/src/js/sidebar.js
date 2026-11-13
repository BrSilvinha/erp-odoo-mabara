/** @odoo-module **/
import { Component, onMounted, onWillUnmount, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

// Menu lateral MABARA: reproduce la navegacion de la captura (Inventario, Informacion general,
// Operaciones, Productos, Informes, Configuracion). Cada opcion abre una accion nativa o del modulo.
const ITEMS = [
    { label: "Inventario", icon: "fa-cube", action: "stock.stock_picking_type_action" },
    { label: "Información general", icon: "fa-clock-o", action: "stock.action_product_stock_view" },
    {
        label: "Operaciones", icon: "fa-exchange", children: [
            { label: "Órdenes de Servicio", action: "mabara_service_order.action_service_order" },
            { label: "Solicitudes de compra", action: "mabara_service_order.action_purchase_request" },
            { label: "Órdenes de compra", action: "purchase.purchase_form_action" },
            { label: "Transferencias", action: "stock.action_picking_tree_all" },
            { label: "Reabastecimiento", action: "stock.action_orderpoint_replenish" },
            { label: "Existencias", action: "stock.action_view_inventory_tree" },
            { label: "Solicitudes de código", action: "mabara_service_order.action_code_request" },
        ],
    },
    {
        label: "Productos", icon: "fa-tags", children: [
            { label: "Productos", action: "stock.product_template_action_product" },
            { label: "Variantes de producto", action: "stock.stock_product_normal_action" },
            { label: "Reglas de reabastecimiento", action: "mabara_service_order.action_orderpoint_mabara" },
            { label: "Unidades de medida", action: "uom.product_uom_form_action" },
            { label: "Categorías de producto", action: "product.product_category_action_form" },
        ],
    },
    {
        label: "Informes", icon: "fa-bar-chart", children: [
            { label: "Análisis de existencias", action: "stock.action_product_stock_view" },
            { label: "Movimientos de stock", action: "stock.stock_move_line_action" },
            { label: "Análisis de compras", action: "purchase.action_purchase_order_report_all" },
            { label: "Análisis de ventas", action: "sale.report_all_channels_sales_action" },
        ],
    },
    {
        label: "Configuración", icon: "fa-cog", children: [
            { label: "Ajustes", action: "base.res_config_setting_act_window" },
            { label: "Almacenes", action: "stock.action_warehouse_form" },
            { label: "Ubicaciones", action: "stock.action_location_form" },
            { label: "Compañías", action: "base.action_res_company_form" },
            { label: "Usuarios", action: "base.action_res_users" },
        ],
    },
];

export class MabaraSidebar extends Component {
    static template = "mabara_theme.Sidebar";
    static props = {};

    setup() {
        this.items = ITEMS;
        this.action = useService("action");
        this.state = useState({ open: "Productos", current: null });
        const bus = this.env.bus;
        this.onUiUpdated = () => {
            const ctrl = this.action.currentController;
            this.state.current = (ctrl && ctrl.action && ctrl.action.xml_id) || null;
        };
        onMounted(() => {
            document.body.classList.add("mabara_has_sidebar");
            const navbar = document.querySelector(".o_main_navbar");
            if (navbar) {
                document.documentElement.style.setProperty(
                    "--mabara-navbar-height", navbar.offsetHeight + "px");
            }
            bus.addEventListener("ACTION_MANAGER:UI-UPDATED", this.onUiUpdated);
        });
        onWillUnmount(() => {
            document.body.classList.remove("mabara_has_sidebar");
            bus.removeEventListener("ACTION_MANAGER:UI-UPDATED", this.onUiUpdated);
        });
    }

    isActive(item) {
        if (item.children) {
            return item.children.some((c) => c.action === this.state.current);
        }
        return item.action === this.state.current;
    }

    onItem(item) {
        if (item.children) {
            this.state.open = this.state.open === item.label ? null : item.label;
        } else {
            this.go(item.action);
        }
    }

    go(xmlid) {
        this.state.current = xmlid;
        this.action.doAction(xmlid, { clearBreadcrumbs: true });
    }
}

registry.category("main_components").add("mabara_sidebar", { Component: MabaraSidebar });
