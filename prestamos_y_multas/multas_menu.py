"""Este archivo tiene el menu de multas (opcion 5 -> 1, 2 y 3): generar multas, marcar como pagada y consultar."""

from mysql.connector import Error

from nucleo.utilidades import (
    confirmar,
    limpiar_pantalla,
    mostrar_aviso,
    mostrar_ayuda_cancelar,
    mostrar_error,
    mostrar_exito,
    mostrar_ficha,
    mostrar_tabla,
    mostrar_titulo,
    OperacionCancelada,
    PasoAnterior,
    pausar,
    pedir_entero,
)
from nucleo.vistas import confirmar_continuar, mostrar_multas
from prestamos_y_multas.multas_sql import TARIFA_MULTA_DIA


class MenuMultas:
    """Esta clase es la opcion 5: genera multas, marca como pagada y consulta historial y detalle."""

    def __init__(self, multas):
        self.multas = multas

    def flujo_multas(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo(
                "MULTAS POR DEVOLUCIÓN TARDÍA",
                f"Las multas se generan automáticamente al devolver tarde (${TARIFA_MULTA_DIA}/día)",
            )
            print("1. Generar automáticamente multas faltantes (para devoluciones tardías sin multa)")
            print("2. Marcar una multa pendiente como 'Pagada'")
            print("3. Ver historial y consultar detalle completo de una multa")
            print("0. Volver\n")

            op = pedir_entero(
                "Opción", minimo=0, maximo=3, permitir_cancelar=False, permitir_atras=False
            )

            if op == 0:
                break
            elif op == 1:
                try:
                    creadas = self.multas.generar_multas_automaticas()
                    if not creadas:
                        mostrar_aviso("Todas las devoluciones tardías ya tienen su multa generada.")
                    else:
                        filas = [
                            (
                                c["id_multa"],
                                c["prestamo"],
                                c["obra"],
                                c["ejemplar"],
                                c["dias_retraso"],
                                f"${c['total']}",
                            )
                            for c in creadas
                        ]
                        mostrar_tabla(
                            "Multas generadas automáticamente",
                            ["Multa #", "Folio", "ISBN", "Ej. #", "Días", "Total"],
                            filas,
                        )
                        mostrar_exito(f"Se generaron {len(creadas)} multa(s) automáticamente.")
                except Error as e:
                    mostrar_error(f"Error al generar multas: {e}")
                pausar()
            elif op == 2:
                self._pagar_multas()
            elif op == 3:
                self._consultar_detalle_multas()

    def _consultar_detalle_multas(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo("HISTORIAL Y DETALLE COMPLETO DE MULTAS")
            multas = self.multas.listar_multas()
            if not multas:
                mostrar_aviso("No hay multas registradas.")
                pausar()
                return

            mostrar_multas(multas)
            mostrar_ayuda_cancelar()
            try:
                if not confirmar("¿Deseas ver la ficha completa de una multa específica?"):
                    return

                while True:
                    id_multa = pedir_entero("Número de multa a consultar", minimo=1)
                    detalle = self.multas.consultar_detalle_multa(id_multa)
                    if not detalle:
                        mostrar_error("No existe ninguna multa con ese número.")
                        continue
                    break

                mostrar_ficha(
                    f"INFORMACIÓN COMPLETA DE LA MULTA #{detalle['id_multa']}",
                    [
                        ("Número de multa", detalle["id_multa"]),
                        ("Estado", detalle["estado"]),
                        ("Número de préstamo", detalle["prestamo"]),
                        ("Fecha del préstamo", detalle["fecha_salida"]),
                        ("Usuario", detalle["usuario"]),
                        ("ISBN", detalle["isbn"]),
                        ("Título", detalle["titulo"]),
                        ("Subtítulo", detalle["subtitulo"]),
                        ("Número de ejemplar", detalle["ejemplar"]),
                        ("Fecha establecida", detalle["fecha_limite"]),
                        ("Fecha real devolución", detalle["fecha_devolucion"]),
                        ("Días de retraso", detalle["dias_retraso"]),
                        ("Monto por día", f"${detalle['monto_dia']}"),
                        ("Monto total", f"${detalle['total']}"),
                    ],
                )
                if not confirmar_continuar("¿Deseas consultar el detalle de OTRA multa?"):
                    return
            except (OperacionCancelada, PasoAnterior):
                return
            except Error as e:
                mostrar_error(f"Error al consultar multa: {e}")
                pausar()
                return

    def _pagar_multas(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo("COBRO DE MULTAS PENDIENTES")
            pendientes = self.multas.listar_multas(solo_pendientes=True)
            if not pendientes:
                mostrar_aviso("No hay multas pendientes de pago.")
                pausar()
                return

            mostrar_multas(pendientes)
            mostrar_ayuda_cancelar()
            try:
                while True:
                    id_multa = pedir_entero("ID de la multa a pagar", minimo=1)
                    multa_bd = self.multas.obtener_multa(id_multa)
                    if not multa_bd:
                        mostrar_error("No existe ninguna multa con ese ID.")
                        continue
                    if multa_bd["estado"] != "Pendiente":
                        mostrar_aviso(
                            f"La multa #{id_multa} ya tiene estado '{multa_bd['estado']}'."
                        )
                        continue
                    self.multas.marcar_pagada(id_multa)
                    mostrar_exito(
                        f"Multa #{id_multa} (${multa_bd['total']}) marcada como 'Pagada'."
                    )
                    break

                if not self.multas.listar_multas(solo_pendientes=True):
                    mostrar_aviso("Ya no quedan multas pendientes de pago.")
                    pausar()
                    return
                if not confirmar_continuar(
                    "¿Deseas marcar OTRA multa pendiente como 'Pagada'?"
                ):
                    return
            except (OperacionCancelada, PasoAnterior):
                mostrar_aviso("Regresando al menú de multas...")
                return
            except Error as e:
                mostrar_error(f"Error al actualizar la multa: {e}")
                if not confirmar_continuar("¿Deseas intentar con otra multa?"):
                    return
