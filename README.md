# ERP Odoo MABARA – instalación y simulación

ERP **Odoo 19.0 Community** con PostgreSQL 16, en Docker, para demostrar la gestión de **órdenes de servicio, compras e inventario** (con clasificación ABC, EOQ, stock de seguridad y punto de reorden) de la empresa MABARA.

Con esta guía puedes descargarlo y dejarlo funcionando en tu PC en unos 15–25 minutos (la mayor parte es la descarga de imágenes la primera vez).

---

## 1. Requisitos

| Qué | Para qué | Cómo comprobarlo (en PowerShell) |
|---|---|---|
| **Windows 10/11** con **WSL2** | Docker lo necesita | `wsl --status` |
| **Docker Desktop** (corriendo) | Ejecuta Odoo y PostgreSQL | `docker --version` y `docker compose version` |
| **Git** | Descargar el proyecto | `git --version` |
| **Python 3.10 o superior** (en el PATH) | Scripts de carga de datos (no necesita instalar paquetes) | `python --version` |
| ~10 GB de disco libre y 8 GB de RAM | Imágenes de Docker y base de datos | – |
| Puerto **8069** libre | Acceso a Odoo | `netstat -ano \| findstr :8069` (no debe mostrar nada) |

Enlaces: [Docker Desktop](https://www.docker.com/products/docker-desktop/) · [Git](https://git-scm.com/downloads) · [Python](https://www.python.org/downloads/) (al instalar, marca **“Add python.exe to PATH”**).

> Antes de seguir, abre **Docker Desktop** y espera a que indique que el motor está en ejecución.

---

## 2. Descargar el proyecto

El repositorio es **público**: no necesitas cuenta de GitHub ni invitación.

**Sin Git:** en <https://github.com/BrSilvinha/erp-odoo-mabara> pulsa **Code ▸ Download ZIP**, descomprime la carpeta y salta a la sección 3 (solo necesitas Docker Desktop y Python). Si Windows muestra «Windows protegió su PC» al abrir `INSTALAR.bat`, pulsa **Más información ▸ Ejecutar de todos modos**.

**Con Git:**

```powershell
cd $HOME\Documents
git clone https://github.com/BrSilvinha/erp-odoo-mabara.git
cd erp-odoo-mabara
```

Si Git pide iniciar sesión, usa tu cuenta de GitHub (se abre el navegador). Alternativa: `gh auth login` si tienes GitHub CLI.

---

## 3. Instalar todo con un solo comando

**Forma rápida:** haz doble clic en **`INSTALAR.bat`** (en la carpeta del proyecto). Comprueba que estén Docker y Python, instala todo y abre el navegador. Para encender el sistema en otra ocasión, doble clic en **`INICIAR.bat`**.

O, a mano, desde la carpeta del proyecto en **PowerShell**:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup_all.ps1
```

El script hace, en orden:

1. Crea `.env` y `config\odoo.conf` con **claves aleatorias** (solo si no existen; no los subas a GitHub, ya están ignorados).
2. Levanta PostgreSQL 16 y Odoo 19.0 con Docker Compose (la primera vez descarga ~3.5 GB).
3. Crea la base de datos `mabara_erp` (idioma es_PE, país Perú, moneda PEN).
4. Instala los módulos: Inventario, Compras, Ventas, Contabilidad (localización Perú), acuerdos de compra y los dos módulos del proyecto (`mabara_service_order`, `mabara_theme`).
5. Carga los datos reales: 13 familias, **257 materiales** de `data\materiales_257.csv` (MABARA_257.xlsx) con sus parámetros EOQ/SS/ROP, y 198 reglas de reabastecimiento (modo manual). **No** crea proveedores, clientes, ubicaciones, stock ni órdenes de servicio.
6. **Solo con `-Demo`:** crea datos de prueba (ubicaciones, 2 proveedores, cliente y stock) y ejecuta los escenarios A–H y las pruebas de políticas, y escribe el resultado en `evidencias\escenarios.md`.

Para probar el flujo completo sin cargar datos reales, ejecuta `powershell -ExecutionPolicy Bypass -File scripts\setup_all.ps1 -Reset -Demo`. **No uses `-Demo` con datos reales.** Para operar con datos reales, carga lo que falta siguiendo el manual (`docs\Manual_de_usuario_ERP_MABARA.pdf`, sección 4).

Al terminar con `-Demo` verás algo así:

```
RESULTADO A: OK
RESULTADO B: OK
RESULTADO C: OK
RESULTADO D: OK ... RESULTADO H: OK
RESULTADO POLITICAS: OK
Listo: http://localhost:8069
Usuario: admin@mabara.demo   Clave: ********   (tambien en el archivo .env)
```

> ⚠ Con `-Demo`, ejecutar el script **por segunda vez** vuelve a correr los escenarios y duplica esas órdenes de ejemplo. Si quieres empezar limpio usa `-Reset` (sección 7), que **borra toda la base** de este proyecto.

---

## 4. Entrar al sistema

1. Abre <http://localhost:8069> en el navegador (se recomienda **Chrome o Edge**).
2. **Usuario:** `admin@mabara.demo`
3. **Clave:** la que mostró el script al final (también está en el archivo `.env`, línea `ODOO_USER_PASSWORD`).

Si ves una pantalla vieja o sin colores, recarga con **Ctrl + F5**.

---

## 5. Qué probar (recorrido rápido)

El menú superior es: **Inventario · Ventas · Compras · Contabilidad · Informes · Configuración**, y a la izquierda hay un menú lateral (Inventario, Información general, Operaciones, Productos, Informes, Configuración).

| # | Dónde | Qué verás |
|---|---|---|
| 1 | Inventario ▸ Productos ▸ `MAT-0001` ▸ pestaña **Política de inventario** | Parámetros del documento: EOQ 4 398, stock de seguridad 651, ROP 3 492, lead time 0.23 meses |
| 2 | Inventario ▸ Reglas de reabastecimiento | Mínimo = ROP y máximo = ROP + EOQ para los 3 materiales priorizados |
| 3 | **Ventas ▸ Órdenes de Servicio** | Las órdenes que dejaron los escenarios A y B (cerradas) |
| 4 | **Compras ▸ Solicitudes de compra** | Solicitud del escenario B, con sus cotizaciones y la orden de compra |
| 5 | Inventario ▸ Transferencias | Recepción de compra y despachos a las órdenes de servicio |
| 6 | Compras ▸ Órdenes de compra | Una RFQ generada automáticamente por la regla de reabastecimiento (escenario C) |

Además de A, B y C se simulan los flujos de los diagramas: D (solicitud de OS no conforme), E (solicitud de compra devuelta), F (devolución de materiales), G (solicitud de código de material) y H (recepción el mismo día y con diferencias).

Para **ejecutar los escenarios tú mismo, paso a paso en pantalla**, sigue `docs\GUIA_DEMOSTRACION.md`.

Resumen de los escenarios:
- **A – Stock disponible:** crear la OS → verificar existencias y reservar → entregar → ejecutar → cerrar.
- **B – Stock insuficiente:** detectar el faltante → solicitud de compra → aprobar → cotizar a 2 proveedores → orden de compra → recibir → entregar → cerrar.
- **C – Punto de reorden:** al bajar el stock del ROP, el programador genera la compra por el EOQ.

---

## 6. Uso diario

```powershell
docker compose stop        # apagar (conserva los datos)
docker compose up -d       # volver a encender
docker compose logs -f odoo   # ver registros de Odoo (Ctrl+C para salir)
```

---

## 7. Empezar de cero o desinstalar

```powershell
# Reconstruir TODO desde cero (borra la base de datos de este proyecto)
powershell -ExecutionPolicy Bypass -File scripts\setup_all.ps1 -Reset

# Desinstalar por completo (borra contenedores y datos de este proyecto)
docker compose down -v
```

`-v` / `-Reset` solo eliminan los volúmenes `mabara_erp_*`, no los de otros proyectos.

---

## 8. Problemas frecuentes

| Síntoma | Causa y solución |
|---|---|
| `docker: command not found` o “cannot connect to the Docker daemon” | Docker Desktop no está abierto. Ábrelo y espera a que diga *Engine running*. |
| `python` no se reconoce o abre la Microsoft Store | Instala Python con “Add to PATH”, o desactiva el alias en *Configuración ▸ Aplicaciones ▸ Alias de ejecución de aplicaciones*. |
| `port is already allocated` (8069) | Otro programa usa el puerto 8069. Ciérralo o cambia `"8069:8069"` por `"8070:8069"` en `docker-compose.yml` y entra por <http://localhost:8070> (y ajusta `URL` en `scripts\odoo_client.py` y `01_create_db.py`). |
| `container name "/mabara_db" is already in use` | Ya existe una instalación previa. Usa `docker compose up -d` o `setup_all.ps1 -Reset`. |
| Aviso rojo/amarillo “push service error” (en Brave) | Es el navegador bloqueando notificaciones push. Ciérralo, o usa Chrome/Edge. No afecta al ERP. |
| La instalación parece detenida | La primera vez descarga imágenes y compila módulos; puede tardar 10–20 min. Revisa `docker compose logs -f odoo`. |
| Error de política: “toda salida de materiales debe estar asociada a una Orden de Servicio” | Es una regla del documento (política 8), no un fallo. Despacha desde la Orden de Servicio. |
| En el log aparece `cannot marshal None` | Ruido conocido de los scripts de automatización; no afecta la interfaz. |

---

## 9. Para el dueño del repositorio: dar acceso a otra persona

1. En GitHub abre el repositorio ▸ **Settings ▸ Collaborators ▸ Add people**.
2. Escribe el usuario o correo de GitHub de la persona y envía la invitación.
3. Esa persona la acepta (llega por correo o en <https://github.com/notifications>) y ya puede hacer el `git clone` de la sección 2.

---

## 10. Contenido del proyecto

```
addons/mabara_service_order   Orden de Servicio, solicitud de compra, políticas y campos EOQ/SS/ROP
addons/mabara_theme           Menú horizontal, colores, logo y ficha de material
data/                         materiales_257.csv (maestro real) y datos de referencia del documento académico
scripts/                      00 claves · 01 base de datos · 02 carga · 03 escenarios · 05 fotos · 06 demo · 07 reabastecimiento · setup_all.ps1
docs/                         Manual de usuario (PDF), guía de demostración, nativo vs. personalizado, comandos y cambios
evidencias/escenarios.md      Resultado de las simulaciones
docker-compose.yml            Odoo 19.0 + PostgreSQL 16 (volúmenes persistentes, puerto 8069)
```

**Importante:**
- Se cargan los 257 materiales reales (`data\materiales_257.csv`). Faltan por cargar ubicaciones, proveedores con precios, clientes, stock inicial y la clasificación ABC (ver el manual, sección 4). El costo unitario del Excel está rotulado «sim.» (simulado): confirmar que es real.
- Los datos de prueba (ubicaciones, proveedores, cliente, stock) solo se crean con `-Demo` (`scripts\06_demo_data.py`).
- Con stock y proveedores cargados, activa la reposición automática con `python scripts\07_activar_reabastecimiento.py`.
- El documento académico base (`ERP.pdf`) **no** está en el repositorio.
- Documentación detallada de qué es nativo de Odoo y qué es personalizado: `docs\NATIVO_VS_PERSONALIZADO.md`.
