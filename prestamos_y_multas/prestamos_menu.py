"""Menú de préstamos (Opción 3 -> 1, 2 y 3)."""

from datetime import date, timedelta
from mysql.connector import Error

from nucleo.modelos import Prestamo
from nucleo.utilidades import (
    confirmar,
    formatear_fecha,
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
    pedir_fecha,
    pedir_texto,
)
from nucleo.vistas import confirmar_continuar, mostrar_resumen_disponibles
from registros.catalogos_menu import seleccionar_o_crear_usuario


class MenuPrestamos:
    """Opción 3: registrar préstamo, detalle por folio y consulta por fecha."""

    def __init__(self, prestamos, obras, multas, catalogos, empleado_activo):
        self.prestamos = prestamos
        self.obras = obras
        self.multas = multas
        self.catalogos = catalogos
        self.empleado_activo = empleado_activo

    def flujo_prestamos(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo(
                "PRÉSTAMOS DE EJEMPLARES",
                "Registro de préstamos y consulta de historial por folio o fecha",
            )
            print("1. Registrar nuevo préstamo")
            print("2. Consultar detalle de un préstamo (por Folio)")
            print("3. Consultar préstamos realizados en una fecha")
            print("0. Volver\n")

            op = pedir_entero(
                "Opción", minimo=0, maximo=3, permitir_cancelar=False, permitir_atras=False
            )
            if op == 0:
                return
            if op == 1:
                self._registrar_prestamo()
            elif op == 2:
                self._consultar_detalle_prestamo()
            elif op == 3:
                self._consultar_prestamos_por_fecha()

    def _consultar_detalle_prestamo(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo("DETALLE DE PRÉSTAMO POR FOLIO")

            todos = self.prestamos.listar_todos_prestamos()
            if not todos:
                mostrar_aviso("No hay préstamos registrados en la base de datos.")
                pausar()
                return

            filas_resumen = [
                (
                    p["folio"],
                    p["fecha_salida"],
                    p["fecha_limite"],
                    p["usuario"],
                    p["total_ejemplares"],
                    p["pendientes"],
                )
                for p in todos
            ]
            mostrar_tabla(
                "Préstamos registrados",
                ["Folio", "Salida", "Límite", "Usuario", "Total Ej.", "Pendientes"],
                filas_resumen,
            )
            mostrar_ayuda_cancelar()
            try:
                while True:
                    folio = pedir_entero("Número de préstamo (Folio) a consultar", minimo=1)
                    detalle = self.prestamos.consultar_detalle_prestamo(folio)
                    if not detalle:
                        mostrar_error("No existe ningún préstamo con ese folio.")
                        continue
                    break

                cab = detalle[0]
                mostrar_ficha(
                    f"INFORMACIÓN DEL PRÉSTAMO #{cab['folio']}",
                    [
                        ("Número de préstamo", cab["folio"]),
                        ("Fecha del préstamo", cab["fecha_salida"]),
                        ("Fecha límite", cab["fecha_limite"]),
                        ("Usuario", cab["usuario"]),
                        ("Total de ejemplares", len(detalle)),
                    ],
                )

                filas_ej = [
                    (
                        d["isbn"],
                        d["titulo"],
                        d["subtitulo"],
                        d["ejemplar"],
                        formatear_fecha(d["fecha_devolucion"])
                        if d["fecha_devolucion"]
                        else "Pendiente",
                    )
                    for d in detalle
                ]
                mostrar_tabla(
                    f"Ejemplares incluidos en el Préstamo #{cab['folio']}",
                    ["ISBN", "Título", "Subtítulo", "Ej. #", "Fecha Devolución"],
                    filas_ej,
                )

                if not confirmar_continuar("¿Deseas consultar OTRO préstamo?"):
                    return
            except (OperacionCancelada, PasoAnterior):
                return
            except Error as e:
                mostrar_error(f"Error al consultar préstamo: {e}")
                pausar()
                return

    def _consultar_prestamos_por_fecha(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo("PRÉSTAMOS REALIZADOS EN UNA FECHA")

            fechas = self.prestamos.listar_fechas_prestamos()
            if not fechas:
                mostrar_aviso("No hay préstamos registrados en la base de datos.")
                pausar()
                return

            mostrar_tabla(
                "Fechas con Préstamos Registrados",
                ["Fecha", "Préstamos", "Ejemplares"],
                [(f["fecha_salida"], f["total_prestamos"], f["total_ejemplares"]) for f in fechas],
            )
            mostrar_ayuda_cancelar()
            try:
                fecha = pedir_fecha("Fecha de préstamo a consultar", permitir_futuro=False)
                registros = self.prestamos.consultar_prestamos_por_fecha(fecha)
                if not registros:
                    mostrar_aviso(
                        f"No se encontraron préstamos registrados el {formatear_fecha(fecha)}."
                    )
                else:
                    filas = [
                        (
                            r["fecha_salida"],
                            r["folio"],
                            r["usuario"],
                            r["cantidad_ejemplares"],
                            r["fecha_limite"],
                            r["empleado"],
                        )
                        for r in registros
                    ]
                    mostrar_tabla(
                        f"Préstamos del {formatear_fecha(fecha)} ({len(registros)} registro(s))",
                        [
                            "Fecha",
                            "Folio",
                            "Usuario",
                            "Cant. Ej.",
                            "Fecha Devolución",
                            "Empleado",
                        ],
                        filas,
                    )

                if not confirmar_continuar("¿Deseas consultar préstamos de OTRA fecha?"):
                    return
            except (OperacionCancelada, PasoAnterior):
                return
            except Error as e:
                mostrar_error(f"Error al consultar préstamos por fecha: {e}")
                pausar()
                return

    def _registrar_prestamo(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo(
                "REGISTRAR NUEVO PRÉSTAMO",
                "Plazo automático: 14 días | Escribe 'nuevo' en usuario para registrarlo al momento",
            )

            resumen_disp = self.prestamos.listar_resumen_disponibles()
            if not resumen_disp:
                mostrar_aviso("No hay ejemplares disponibles para préstamo.")
                pausar()
                return

            mostrar_ayuda_cancelar()
            id_usuario = None
            fecha_salida = None
            fecha_limite = None
            seleccionados = []
            paso = 0

            try:
                while paso < 3:
                    try:
                        if paso == 0:
                            id_usuario = seleccionar_o_crear_usuario(self.catalogos)
                            cant_multas, monto_pend = self.multas.contar_multas_pendientes_usuario(
                                id_usuario
                            )
                            if cant_multas > 0:
                                mostrar_aviso(
                                    f"Atención: Este usuario tiene {cant_multas} multa(s) "
                                    f"pendiente(s) por un total de ${monto_pend}."
                                )
                            paso = 1
                        elif paso == 1:
                            fecha_min_prestamo = date.today() - timedelta(days=365)
                            fecha_salida = pedir_fecha(
                                "Fecha de salida del préstamo",
                                fecha_min=fecha_min_prestamo,
                                permitir_futuro=False,
                            )
                            fecha_limite = fecha_salida + timedelta(days=Prestamo.DIAS_PLAZO)
                            print(
                                f"Fecha límite calculada automáticamente (+14 días): "
                                f"{formatear_fecha(fecha_limite)}"
                            )
                            paso = 2
                        elif paso == 2:
                            mostrar_resumen_disponibles(resumen_disp)
                            seleccionados = self._capturar_ejemplares_prestamo(
                                fecha_salida, seleccionados
                            )
                            paso = 3
                    except PasoAnterior:
                        if paso == 0:
                            mostrar_aviso("Regresando al menú anterior...")
                            return
                        paso -= 1
                        mostrar_aviso("Regresando al paso anterior...")

                prestamo = Prestamo(
                    fecha_salida=fecha_salida,
                    fecha_limite=fecha_limite,
                    empleado=self.empleado_activo.id_empleado,
                    usuario=id_usuario,
                    ejemplares=seleccionados,
                )
                folio = self.prestamos.registrar_prestamo(prestamo)
                mostrar_exito(
                    f"Préstamo registrado correctamente con Folio #{folio} | "
                    f"Ejemplares: {len(seleccionados)} | Fecha límite: {formatear_fecha(fecha_limite)}"
                )
                if not confirmar_continuar("¿Deseas registrar OTRO préstamo?"):
                    return
            except OperacionCancelada:
                mostrar_aviso("Préstamo cancelado. Regresando al menú...")
                pausar()
                return
            except (ValueError, Error) as e:
                mostrar_error(f"No se pudo registrar el préstamo: {e}")
                if not confirmar_continuar("¿Deseas intentar registrar otro préstamo?"):
                    return

    def _capturar_ejemplares_prestamo(self, fecha_salida, seleccionados_actuales=None):
        """Selecciona 1 o más ejemplares (ISBN -> número) con retroceso paso a paso."""
        seleccionados = list(seleccionados_actuales) if seleccionados_actuales else []

        while True:
            if not seleccionados:
                isbn = pedir_texto("ISBN de la obra a prestar", max_len=17)
                agregado = self._elegir_ejemplar_de_isbn(isbn, seleccionados, fecha_salida)
                if not agregado:
                    continue
            try:
                agregar_otro = confirmar("¿Deseas agregar OTRO ejemplar a este mismo préstamo?")
            except PasoAnterior:
                quitado = seleccionados.pop()
                mostrar_aviso(
                    f"Regresando al paso anterior (se quitó {quitado[0]} - Ejemplar #{quitado[1]})."
                )
                continue

            if not agregar_otro:
                return seleccionados

            try:
                isbn = pedir_texto("ISBN de la siguiente obra a prestar", max_len=17)
            except PasoAnterior:
                mostrar_aviso("Regresando a la confirmación de ejemplares...")
                continue

            self._elegir_ejemplar_de_isbn(isbn, seleccionados, fecha_salida)

    def _elegir_ejemplar_de_isbn(self, isbn, seleccionados, fecha_salida):
        """Valida existencia, fecha de adquisición y disponibilidad de ejemplares de un ISBN."""
        if not self.obras.existe_obra(isbn):
            mostrar_error("Ese ISBN no existe en el catálogo. Intenta con otro.")
            return False

        fecha_adq = self.obras.obtener_fecha_primera_adquisicion(isbn)
        if fecha_adq and fecha_salida < fecha_adq:
            mostrar_error(
                f"Esta obra se adquirió el {formatear_fecha(fecha_adq)}; "
                f"no puedes prestarla con fecha de salida {formatear_fecha(fecha_salida)}."
            )
            return False

        copias_bd = self.prestamos.obtener_ejemplares_disponibles_por_isbn(isbn)
        copias_libres = [c for c in copias_bd if (isbn, c["ejemplar"]) not in seleccionados]
        if not copias_libres:
            mostrar_aviso(
                "Esta obra ya no tiene ejemplares disponibles (están prestados o ya los agregaste)."
            )
            return False

        numeros_libres = [c["ejemplar"] for c in copias_libres]
        titulo_obra = copias_libres[0]["titulo"]
        lista_txt = ", ".join(f"#{n}" for n in numeros_libres)
        print(f"\nObra: {titulo_obra}")
        print(f"Ejemplares disponibles para prestar: {lista_txt}")

        while True:
            try:
                num_ej = pedir_entero(
                    "Número de ejemplar a prestar (escribe 'atras' para elegir otro ISBN)",
                    minimo=1,
                )
            except PasoAnterior:
                mostrar_aviso("Regresando a la selección de ISBN...")
                return False

            if num_ej not in numeros_libres:
                mostrar_error(
                    f"El ejemplar #{num_ej} no existe o no está disponible. "
                    f"Opciones válidas: {lista_txt}"
                )
                continue

            seleccionados.append((isbn, num_ej))
            mostrar_exito(f"Agregado al préstamo: {titulo_obra} ({isbn}) - Ejemplar #{num_ej}")
            return True
