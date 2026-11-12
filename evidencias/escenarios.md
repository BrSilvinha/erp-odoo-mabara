# Evidencias de simulacion - MABARA ERP (Odoo 19 Community)
Generado: 2026-11-12 11:17

> Stock inicial, proveedores, precios de MAT-0006 y cliente son datos DEMO (no provienen del documento).

---
## Escenario A - Stock disponible
Stock inicial: MAT-0001=5000, MAT-0002=1800, MAT-0003=1200

**Paso 1.** Solicitud registrada: OS/00001 (estado draft)

**Paso 2.** OS emitida -> OS/00001 / issued

**Paso 3.** Verificar existencias y reservar -> OS/00001 / ready
| Material | Requerido | Disponible | Reservado | Faltante |
|---|---|---|---|---|
| [MAT-0001] Cable concéntrico de aluminio 2x6 mm² | 300 | 5000 | 300 | 0 |
| [MAT-0002] Cintillos plásticos grandes bolsa x100 | 100 | 1800 | 100 | 0 |
| [MAT-0003] Templadores para tendido eléctrico | 50 | 1200 | 50 | 0 |

**Paso 4.** Entrega (despacho a la OS)
- Despacho `WH/OSOUT/00001` -> estado **done**
- OS -> OS/00001 / delivered

**Paso 5.** Ejecucion y cierre -> OS/00001 / closed
Stock final: MAT-0001=4700 (antes 5000), MAT-0002=1700 (antes 1800), MAT-0003=1150 (antes 1200)

**RESULTADO A: OK**

---
## Escenario B - Stock insuficiente (compra)
Stock inicial MAT-0006 (Tubo SAP 3/4" x 3 m) = 40

**Paso 1.** OS OS/00002 / waiting_supply - faltante detectado
| Material | Requerido | Disponible | Reservado | Faltante |
|---|---|---|---|---|
| [MAT-0006] Tubo SAP 3/4" x 3 m | 120 | 40 | 40 | 80 |
| [MAT-0004] Curva SAP 3/4" x 90° | 50 | 150 | 50 | 0 |

**Paso 2.** Solicitud de compra generada: **SC/00001** (draft)
- [MAT-0006] Tubo SAP 3/4" x 3 m: 80

**Paso 3.** Solicitud revisada y aprobada -> approved

**Paso 4.** Cotizaciones solicitadas y comparadas
| RFQ | Proveedor | Total (PEN) | Estado |
|---|---|---|---|
| P00001 | Distribuidora Industrial Lima S.A.C. (DEMO) | 1113.92 | draft |
| P00002 | Proveedor Eléctrico Andino S.A.C. (DEMO) | 1180.00 | draft |
- Proveedor seleccionado (menor precio): **Distribuidora Industrial Lima S.A.C. (DEMO)**

**Paso 5.** Orden de Compra **P00001** -> estado **purchase**
- Otras cotizaciones: P00002 (draft)

**Paso 6.** Recepcion `WH/IN/00001` validada contra la OC -> **done**
- Stock MAT-0006: 40 -> 120

**Paso 7.** Reserva tras abastecimiento -> OS/00002 / ready
| Material | Requerido | Disponible | Reservado | Faltante |
|---|---|---|---|---|
| [MAT-0006] Tubo SAP 3/4" x 3 m | 120 | 120 | 120 | 0 |
| [MAT-0004] Curva SAP 3/4" x 90° | 50 | 150 | 50 | 0 |

**Paso 8.** Entrega de materiales
- Despacho `WH/OSOUT/00002` -> estado **done**
- OS -> OS/00002 / delivered

**Paso 9.** Ejecucion y cierre -> OS/00002 / closed
Stock final MAT-0006 = 0 (80 comprados + 40 existentes - 120 entregados)

**RESULTADO B: OK**

---
## Escenario C (adicional) - Regla de reabastecimiento ROP / EOQ (MAT-0001)
Stock MAT-0001 = 4700 m | ROP = 3492 | EOQ = 4398 | max = ROP+EOQ = 7890
- Despacho `WH/OSOUT/00003` -> estado **done**
Tras despachar 1,210 m: stock = 3490 m (< ROP 3,492)
Programador de reabastecimiento ejecutado. RFQ generadas por la regla:
- P00003 | cantidad 4400 m | regla OP/00001
- RFQ originada por regla de reabastecimiento puede confirmarse sin solicitud manual (politica 4).

**RESULTADO C: OK**

---
## Pruebas de politicas (deben ser rechazadas)
- Politica 8 (salida sin OS): bloqueada -> `<Fault 2: 'Politica 8: toda salida de materiales debe estar asociada a una Orden de Servicio.'>`
- Politicas 4/5 (OC sin solicitud ni regla): bloqueada
- Ejecutar una OS sin materiales entregados: bloqueado

**RESULTADO POLITICAS: OK**