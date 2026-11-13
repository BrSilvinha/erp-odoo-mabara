# Guía de demostración – ERP Odoo MABARA

Basada en `ERP.pdf` (Tablas II, V, VIII, XII–XVI y XVIII). Odoo 19.0 Community + PostgreSQL 16 en Docker.

## 0. Acceso
- URL: <http://localhost:8069> · Base de datos: `mabara_erp` · Usuario: `admin@mabara.demo`
- La contraseña de prueba y las claves de PostgreSQL / maestra están **solo** en `.env` (no se versiona ni se copia a la documentación).
- Levantar: `docker compose up -d` · Detener: `docker compose stop` · Reconstruir todo: `scripts\setup_all.ps1 -Reset`

## 1. Qué mostrar (orden sugerido, ~15 min)
| # | Dónde en Odoo | Qué se muestra | Referencia del documento |
|---|---|---|---|
| 1 | Inventario ▸ Productos (maestro de materiales) ▸ `MAT-0001` ▸ pestañas **Información general** y **Política de inventario (EOQ / SS / ROP)** | Código maestro, códigos anteriores, familia, ABC, parámetros D, S, H, σ, L, Z y los valores EOQ/SS/ROP **del documento** junto al recálculo con las fórmulas | Tablas V, IX, XII–XIV |
| 2 | Inventario ▸ Operaciones ▸ Reabastecimiento | Reglas de MAT-0001/2/3: mínimo = ROP, máximo = ROP + EOQ | Tabla XIV |
| 3 | Inventario ▸ Configuración ▸ Ubicaciones | Ubicaciones DEMO `A-CABLES`, `B-FIJACION`, `C-TUBERIAS`, `D-VARIOS` | Tabla XV |
| 4 | **Ventas ▸ Órdenes de Servicio** | Flujo de OS (escenarios A y B) | Tabla XVI, PRO-01 |
| 5 | **Compras ▸ Solicitudes de compra** | Solicitud → aprobación → cotizaciones | PRO-02 |
| 6 | Compras ▸ Pedidos | Cotizaciones por proveedor (alternativas), OC confirmada | PRO-02, política 5–6 |
| 7 | Inventario ▸ Operaciones ▸ Recepciones / Despachos a OS | Recepción contra OC y despacho a la OS | PRO-03, políticas 7–8 |

## 2. Escenario A – Stock disponible (en vivo)
1. **Ventas ▸ Órdenes de Servicio ▸ Nuevo**. Cliente `Cliente DEMO – Distribuidora Eléctrica`, descripción libre.
2. Materiales: `MAT-0001` 300 m, `MAT-0002` 100 bolsa x100, `MAT-0003` 50 unidad. **Emitir OS**.
3. **Verificar existencias y reservar** → estado *Materiales reservados*; todas las líneas con faltante 0.
4. Botón **Despachos** → abrir el despacho `WH/OSOUT/…` → **Validar**. La OS pasa a *Materiales entregados*.
5. **Registrar ejecución** → **Cerrar OS**. Verificar stock: MAT-0001 baja de 5 000 a 4 700 m.

## 3. Escenario B – Stock insuficiente (en vivo)
1. Nueva OS con `MAT-0006` (Tubo SAP 3/4" x 3 m) **120** y `MAT-0004` 50 (stock DEMO de MAT-0006 = 40). Emitir.
2. **Verificar existencias**: estado *Por abastecer*, faltante de 80 en MAT-0006.
3. **Generar solicitud de compra** → *Enviar a aprobación* → *Aprobar* → **Solicitar cotizaciones** (se crean dos RFQ, una por proveedor, enlazadas como alternativas).
4. En Compras abrir una RFQ ▸ **Comparar líneas de producto**; elegir el menor precio ▸ **Confirmar pedido** (cancelar la alternativa).
5. **Recibir** (botón Recepción en la OC) ▸ Validar. El stock pasa de 40 a 120.
6. Volver a la OS ▸ **Reintentar reserva** → *Materiales reservados* → validar el despacho → ejecutar → cerrar.

## 4. Escenario C (extra) – Disparo por ROP/EOQ
Despachar a una OS 1 210 m de `MAT-0001` (4 700 → 3 490 m, por debajo del ROP 3 492). Ejecutar **Inventario ▸ Operaciones ▸ Reabastecimiento ▸ Ejecutar programador** (es la tarea programada «Procurement: run scheduler»): se genera una RFQ de ≈ 4 400 m (hasta ROP + EOQ).

## 4b. Flujos de los diagramas (Fig. 1, 2 y 3)
- **D – Solicitud no conforme (Fig. 1, paso 2.a)**: en una OS en estado *Solicitud* escribe el «Motivo de corrección» y pulsa **Solicitar corrección** → estado *Por corregir*; el Área Comercial completa y pulsa **Reenviar corregida**; luego **Emitir OS** (exige responsable o cuadrilla).
- **E – Solicitud de compra no conforme (Fig. 2, paso 4.a)**: en la solicitud *Por revisar* escribe el «Motivo de devolución» y pulsa **Devolver para corrección** → *Devuelta*; corrige y **Reenviar corregida**.
- **F – Devolución de materiales (Fig. 3)**: en una OS con materiales entregados pulsa **Devolver materiales no utilizados**; ajusta la cantidad realmente devuelta y valida el ingreso (tipo «Devolución de materiales de OS»).
- **G – Material no codificado (Fig. 3)**: Inventario ▸ **Solicitudes de código de material**: Almacén solicita → el Administrador del ERP asigna el código y lo crea en el maestro → se comunica la disponibilidad.
- **H – Recepción (Fig. 3)**: en la recepción de una OC, informa el documento de respaldo (guía de remisión) y la fecha física; el ingreso se bloquea si la fecha no es hoy, y si se recibe distinto a lo pedido la diferencia queda registrada y comunicada en la OC (Compras).

## 5. Políticas que se pueden probar
- **Política 8**: validar una entrega estándar (WH/OUT) sin OS → error “toda salida de materiales debe estar asociada a una Orden de Servicio”.
- **Política 3**: enviar a revisión una solicitud de compra cuya OS aún no verificó existencias → error.
- **Política 4**: solicitud de compra sin OS → error.
- **Política 7**: validar una recepción de proveedor sin Orden de Compra → error.
- **Políticas 4/5**: confirmar una OC creada a mano, sin solicitud ni regla → error.
- Ejecutar una OS sin materiales entregados → error.

## 6. Reproducción automática y evidencias
`scripts\setup_all.ps1 -Reset` reconstruye y ejecuta los tres escenarios. La salida queda en `evidencias\escenarios.md`.

## 7. Interfaz (módulo `mabara_theme`)
- **Menú lateral izquierdo** como la captura de referencia (Inventario, Información general, Operaciones, Productos ▸ Productos / Variantes / Reglas de reabastecimiento / Unidades / Categorías, Informes, Configuración).
- Ficha de material con franja de indicadores (demanda, EOQ, SS, ROP, lead time, clase ABC) y pestañas Información general / Inventario / Compras / Ubicaciones / Contabilidad / Notas.
- Lista de **Reglas de reabastecimiento** con código, descripción, unidad, ABC, demanda, EOQ, SS, ROP, lead time y estado.
- Barra superior blanca con el logo, menú horizontal único **Inventario · Ventas · Compras · Contabilidad · Informes · Configuración** y el nombre de la empresa junto al usuario.
- Azul corporativo en botones y enlaces, casillas moradas, ficha de material con los campos del maestro (Tabla IX) en «Información general».
- Logo: `addons\mabara_theme\static\img\logo_mabara.png` (se carga al reconstruir). Para cambiarlo: Configuración ▸ Compañías, y guardar el mismo archivo en esa ruta para que no se pierda con `-Reset`.
- Las apps nativas (Compras, Inventario, Ventas, Contabilidad…) están ocultas: todo se abre dentro del menú MABARA, para que la barra superior sea siempre la misma.
- Resaltado del menú: sin relleno azul; al pasar el cursor el texto pasa a azul con una línea fina inferior.
- Contabilidad usa la localización de Perú (`l10n_pe`): IGV 18 %.
