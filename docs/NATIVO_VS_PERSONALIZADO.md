# Funcionalidades nativas vs. personalizadas

| Requisito del documento | Resolución | Tipo |
|---|---|---|
| Productos, unidades, familias (categorías), ubicaciones, existencias, entradas/salidas | Inventario de Odoo | **Nativo** |
| Código maestro = referencia interna; descripción estándar = nombre; estado activo/archivado | Campos estándar de producto | **Nativo** |
| Reserva y despacho de materiales | Transferencias (stock.picking) con reserva | **Nativo** |
| Proveedores, cotizaciones (RFQ), comparación de alternativas, OC, aprobación por monto, recepción contra OC | Compras + `purchase_requisition` (alternativas) | **Nativo** |
| Reglas de reabastecimiento | `stock.warehouse.orderpoint` (mín = ROP, máx = ROP + EOQ) | **Nativo (parametrizado)** |
| Lead time del proveedor | `delay` en la tarifa del proveedor (0.23 meses ≈ 7 días) | **Nativo (parametrizado)** |
| Código anterior, descripción corta, tipo de ítem, **clasificación ABC** | Campos nuevos en producto (módulo `mabara_service_order`) | **Personalizado (campos)** |
| **EOQ, SS, ROP** | Odoo no los calcula. Se guardan los valores **oficiales del documento** y se recalculan con las fórmulas del documento sólo como verificación (coinciden en los 3 materiales). Botón “Aplicar política” los traslada a la regla | **Personalizado** |
| **Solicitud de servicio y Orden de Servicio** con materiales, estados, seguimiento, ejecución y cierre | Modelo `mabara.service.order` (Odoo Community no incluye Field Service) | **Personalizado** |
| **Solicitud de compra** interna con revisión/aprobación (etapa 6) | Modelo `mabara.purchase.request` (Community no trae solicitudes internas) | **Personalizado** |
| Trazabilidad OS ↔ requerimiento ↔ solicitud ↔ OC ↔ recepción ↔ despacho | Campos `service_order_id` / `purchase_request_id` en picking y OC | **Personalizado** |
| Menú horizontal único, colores, logo y ficha de material (`mabara_theme`) | Módulo de tema + vista heredada + menús que reutilizan acciones nativas | **Personalizado (interfaz)** |
| Corrección de solicitud de OS, asignación de cuadrilla, devolución de solicitud de compra, devolución de materiales, solicitud de código de material, recepción mismo día y diferencias (Fig. 1–3) | Estados/acciones en `mabara.service.order`, `mabara.purchase.request`, `mabara.code.request` y campos en `stock.picking` | **Personalizado** |
| Menú lateral, franja de indicadores, pestañas y lista de reglas de reabastecimiento | Componente OWL `MabaraSidebar`, vistas heredadas | **Personalizado (interfaz)** |
| Políticas 3, 4, 5, 7 y 8 | Validaciones en solicitud de compra, OC, recepción y despacho (las políticas 1, 2 y 6 se cumplen por el diseño del flujo; la 9 y la 10 son reglas de conducta y no se pueden bloquear por código) | **Personalizado** |

## Decisiones técnicas (no especificadas en el documento)
1. **Odoo 19.0** (no 20.0): una versión con más de un año de madurez y etiqueta Docker fija.
2. **EOQ en Odoo 19**: ya no existe “múltiplo de pedido” en las reglas; se usa máximo = ROP + EOQ, de modo que el pedido es ≈ EOQ cuando el stock cae al ROP (ej. 4 400 m frente a 4 398 m del documento).
3. **Stock de seguridad**: queda como atributo y referencia; el ROP ya lo incluye (ROP = d·L + SS).
4. **Lead time**: 0.23 meses = 7 días (×30, redondeado).
5. **Unidad “bolsa x100”**: unidad propia para no alterar el valor del documento.
6. **Aprobación de OC**: activada para OC ≥ S/ 1 000 (el documento exige “revisión y aprobación” sin indicar monto).
7. **Ventas, Contabilidad y `l10n_pe`** se instalaron para igualar la interfaz de referencia (casilla «Puede ser vendido», IGV 18 %, menú Contabilidad); el documento sólo exige Ventas/Gestión de servicios, Compras e Inventario.
8. **PostgreSQL** no se publica al host (el 5432 ya estaba ocupado por otro proyecto); sólo Odoo accede.

## Datos
- **Cargado (real)**: los 257 materiales de `MABARA_257.xlsx` (`data/materiales_257.csv`): descripción, 13 familias, unidad, costo (rotulado «sim.» en el Excel), demanda, desviación, costo de pedido, tasa de mantenimiento, lead time, Z, EOQ, SS y ROP. 198 reglas de reabastecimiento en modo manual (los 59 materiales MAT-0199..0257 tienen ROP = 0).
- **No incluido en el Excel (vacío)**: clasificación ABC, proveedores y sus precios, clientes, ubicaciones, stock inicial.
- **Datos DEMO (opcional)**: `scripts/06_demo_data.py` con `setup_all.ps1 -Demo` (ubicaciones, 2 proveedores, cliente y stock de MAT-0001..0011) y los escenarios A–H. Sin `-Demo` no se crea nada de esto.
- Ver `docs/Manual_de_usuario_ERP_MABARA.pdf`, sección 3, para cargar lo que falta.
