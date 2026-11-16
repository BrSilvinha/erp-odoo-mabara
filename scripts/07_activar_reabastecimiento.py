"""Activa el reabastecimiento AUTOMATICO en todas las reglas (ejecutar solo despues de cargar el stock real y los
proveedores; con stock 0 el modo automatico generaria cotizaciones para todos los materiales)."""
from odoo_client import search, write

ops = search("stock.warehouse.orderpoint", [])
write("stock.warehouse.orderpoint", ops, {"trigger": "auto"})
print("Reglas en modo automatico:", len(ops))
