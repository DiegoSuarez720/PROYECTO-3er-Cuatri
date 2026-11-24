"""Menú de listados rápidos de apoyo (Opción 7 -> 1, 2, 3 y 4)."""

from nucleo.utilidades import (
    limpiar_pantalla,
    mostrar_titulo,
    pausar,
    pedir_entero,
)
from nucleo.vistas import (
    mostrar_multas,
    mostrar_obras,
    mostrar_prestamos_activos_detalle,
    mostrar_resumen_disponibles,
)


class MenuListados:
    """Opción 7: obras, ejemplares disponibles, préstamos activos y multas."""

    def __init__(self, obras, prestamos, multas):
        self.obras = obras
        self.prestamos = prestamos
        self.multas = multas

    def menu_listados_apoyo(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo("LISTADOS RÁPIDOS DE APOYO")
            print("1. Obras registradas")
            print("2. Ejemplares disponibles para préstamo (resumen por obra)")
            print("3. Préstamos activos (detalle de ejemplares prestados)")
            print("4. Multas registradas")
            print("0. Volver\n")

            op = pedir_entero(
                "Opción", minimo=0, maximo=4, permitir_cancelar=False, permitir_atras=False
            )
            if op == 0:
                break
            elif op == 1:
                mostrar_obras(self.obras.listar_obras())
            elif op == 2:
                mostrar_resumen_disponibles(self.prestamos.listar_resumen_disponibles())
            elif op == 3:
                mostrar_prestamos_activos_detalle(
                    self.prestamos.listar_prestamos_activos_detalle()
                )
            elif op == 4:
                mostrar_multas(self.multas.listar_multas())
            pausar()
