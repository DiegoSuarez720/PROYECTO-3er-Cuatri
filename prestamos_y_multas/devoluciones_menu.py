"""Menú de devoluciones (Opción 4 -> 1 y 2)."""

from mysql.connector import Error

from nucleo.utilidades import (
    formatear_fecha,
    limpiar_pantalla,
    mostrar_aviso,
    mostrar_ayuda_cancelar,
    mostrar_error,
    mostrar_exito,
    mostrar_tabla,
    mostrar_titulo,
    OperacionCancelada,
    PasoAnterior,
    pausar,
    pedir_entero,
    pedir_fecha,
    pedir_texto,
)
from nucleo.vistas import (
    confirmar_continuar,
    mostrar_prestamos_activos_resumen,
)
from prestamos_y_multas.multas_sql import TARIFA_MULTA_DIA


class MenuDevoluciones:
    """Opción 4: registrar devolución y consultar devoluciones por fecha (filtro de 3 opciones)."""

    def __init__(self, devoluciones, empleado_activo):
        self.devoluciones = devoluciones
        self.empleado_activo = empleado_activo

    def flujo_devoluciones(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo(
                "DEVOLUCIONES DE EJEMPLARES",
                f"Recibe: {self.empleado_activo.nombre_completo} (multa automática si hay retraso: ${TARIFA_MULTA_DIA}/día)",
            )
            print("1. Registrar nueva devolución")
            print("2. Consultar devoluciones registradas en una fecha")
            print("0. Volver\n")

            op = pedir_entero(
                "Opción", minimo=0, maximo=2, permitir_cancelar=False, permitir_atras=False
            )
            if op == 0:
                return
            if op == 1:
                self._registrar_devolucion()
            elif op == 2:
                self._consultar_devoluciones_por_fecha()

    def _consultar_devoluciones_por_fecha(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo("DEVOLUCIONES REGISTRADAS EN UNA FECHA")

            fechas = self.devoluciones.listar_fechas_devoluciones()
            if not fechas:
                mostrar_aviso("No hay devoluciones registradas en la base de datos.")
                pausar()
                return

            mostrar_tabla(
                "Fechas con Devoluciones Registradas",
                ["Fecha", "Total", "A tiempo", "Con retraso"],
                [
                    (f["fecha_devolucion"], f["total"], f["a_tiempo"], f["con_retraso"])
                    for f in fechas
                ],
            )
            mostrar_ayuda_cancelar()

            fecha = None
            opcion_filtro = None
            paso = 0

            try:
                while paso < 2:
                    try:
                        if paso == 0:
                            fecha = pedir_fecha(
                                "Fecha de devolución a consultar",
                                permitir_futuro=False,
                            )
                            paso = 1
                        elif paso == 1:
                            print("\nTipo de devoluciones a mostrar:")
                            print("1. Solo entregadas a tiempo")
                            print("2. Solo entregadas con retraso")
                            print("3. Todas las devoluciones de esa fecha")
                            opcion_filtro = pedir_entero("Elige una opción (1-3)", minimo=1, maximo=3)
                            paso = 2
                    except PasoAnterior:
                        if paso == 0:
                            return
                        paso -= 1
                        mostrar_aviso("Regresando al campo anterior...")

                mapa_filtros = {
                    1: ("a_tiempo", "a tiempo "),
                    2: ("retraso", "con retraso "),
                    3: ("todas", ""),
                }
                filtro, etiqueta = mapa_filtros[opcion_filtro]

                registros = self.devoluciones.consultar_devoluciones_por_fecha(
                    fecha, filtro=filtro
                )
                if not registros:
                    mostrar_aviso(
                        f"No se encontraron devoluciones {etiqueta}el {formatear_fecha(fecha)}."
                    )
                else:
                    filas = [
                        (
                            r["fecha_devolucion"],
                            r["folio"],
                            r["fecha_salida"],
                            r["fecha_limite"],
                            r["isbn"],
                            r["ejemplar"],
                            r["titulo"],
                            r["subtitulo"],
                        )
                        for r in registros
                    ]
                    mostrar_tabla(
                        f"Devoluciones {etiqueta}del {formatear_fecha(fecha)} ({len(registros)} registro(s))",
                        [
                            "Fecha Dev.",
                            "Folio",
                            "Fecha Prést.",
                            "Fecha Límite",
                            "ISBN",
                            "Ej. #",
                            "Título",
                            "Subtítulo",
                        ],
                        filas,
                    )

                if not confirmar_continuar("¿Deseas consultar devoluciones de OTRA fecha?"):
                    return
            except OperacionCancelada:
                return
            except Error as e:
                mostrar_error(f"Error al consultar devoluciones: {e}")
                pausar()
                return

    def _registrar_devolucion(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo(
                "REGISTRAR DEVOLUCIÓN DE EJEMPLAR",
                f"Recibe: {self.empleado_activo.nombre_completo} (multa automática si hay retraso: ${TARIFA_MULTA_DIA}/día)",
            )

            activos = self.devoluciones.listar_prestamos_activos_resumen()
            if not activos:
                mostrar_aviso("No hay préstamos activos con devoluciones pendientes.")
                pausar()
                return

            mostrar_ayuda_cancelar()
            folio = None
            pendientes = []
            isbn = None
            ejemplares_isbn = []
            num_ej = None
            fecha_dev = None
            paso = 0

            try:
                while paso < 4:
                    try:
                        if paso == 0:
                            mostrar_prestamos_activos_resumen(activos)
                            val_folio = pedir_entero("Folio del préstamo a devolver", minimo=1)
                            pends = self.devoluciones.listar_ejemplares_pendientes_prestamo(val_folio)
                            if not pends:
                                mostrar_error(
                                    "Ese folio no existe o ya no tiene ejemplares pendientes."
                                )
                                continue
                            folio = val_folio
                            pendientes = pends
                            filas = [
                                (
                                    p["obra"],
                                    p["titulo"],
                                    p["ejemplar"],
                                    p["fecha_salida"],
                                    p["fecha_limite"],
                                )
                                for p in pendientes
                            ]
                            mostrar_tabla(
                                f"Ejemplares pendientes del Préstamo #{folio}",
                                ["ISBN", "Título", "Ejemplar #", "Fecha Salida", "Fecha Límite"],
                                filas,
                            )
                            paso = 1
                        elif paso == 1:
                            isbns_pendientes = list(dict.fromkeys(p["obra"] for p in pendientes))
                            val_isbn = pedir_texto("ISBN del ejemplar devuelto", max_len=17)
                            if val_isbn not in isbns_pendientes:
                                mostrar_error(
                                    "Ese ISBN no corresponde a ningún ejemplar pendiente de este préstamo."
                                )
                                continue
                            isbn = val_isbn
                            ejemplares_isbn = [p for p in pendientes if p["obra"] == isbn]
                            paso = 2
                        elif paso == 2:
                            nums_validos = [p["ejemplar"] for p in ejemplares_isbn]
                            print(
                                f"Ejemplares pendientes de '{ejemplares_isbn[0]['titulo']}': "
                                + ", ".join(f"#{n}" for n in nums_validos)
                            )
                            val_ej = pedir_entero("Número de ejemplar devuelto", minimo=1)
                            if val_ej not in nums_validos:
                                mostrar_error(
                                    f"El ejemplar #{val_ej} no está pendiente en este préstamo. "
                                    f"Opciones válidas: {nums_validos}"
                                )
                                continue
                            num_ej = val_ej
                            paso = 3
                        elif paso == 3:
                            fecha_salida = ejemplares_isbn[0]["fecha_salida"]
                            fecha_dev = pedir_fecha(
                                "Fecha real de devolución",
                                fecha_min=fecha_salida,
                                permitir_futuro=False,
                            )
                            paso = 4
                    except PasoAnterior:
                        if paso == 0:
                            mostrar_aviso("Regresando al menú anterior...")
                            return
                        paso -= 1
                        mostrar_aviso("Regresando al paso anterior...")

                resultado = self.devoluciones.registrar_devolucion(
                    folio, isbn, num_ej, fecha_dev, self.empleado_activo.id_empleado
                )
                mostrar_exito(f"Devolución #{resultado['id_devolucion']} registrada correctamente.")
                if resultado["con_retraso"]:
                    mostrar_aviso(
                        f"Entrega con RETRASO de {resultado['dias_retraso']} día(s) "
                        f"(fecha límite: {formatear_fecha(resultado['fecha_limite'])})."
                    )
                    mostrar_aviso(
                        f"Multa #{resultado['id_multa']} generada automáticamente: "
                        f"{resultado['dias_retraso']} día(s) x ${resultado['monto_dia']} = "
                        f"${resultado['total']} [Pendiente]."
                    )
                else:
                    mostrar_exito("Devolución entregada a tiempo (sin multa).")

                if not self.devoluciones.listar_prestamos_activos_resumen():
                    mostrar_aviso("Ya no quedan más préstamos activos pendientes.")
                    pausar()
                    return
                if not confirmar_continuar("¿Deseas registrar OTRA devolución?"):
                    return
            except OperacionCancelada:
                mostrar_aviso("Operación cancelada. Regresando al menú...")
                pausar()
                return
            except (ValueError, Error) as e:
                mostrar_error(f"No se pudo registrar la devolución: {e}")
                if not confirmar_continuar("¿Deseas intentar otra devolución?"):
                    return
