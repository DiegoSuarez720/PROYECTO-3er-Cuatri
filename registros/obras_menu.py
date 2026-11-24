"""Este archivo tiene el menu de obras (opcion 1) y la asignacion de localizacion (opcion 2)."""

from datetime import date
from mysql.connector import Error

from nucleo.modelos import Obra
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
    pedir_fecha,
    pedir_texto,
    validar_isbn,
    validar_texto_descriptivo,
    validar_titulo,
)
from nucleo.vistas import confirmar_continuar, mostrar_obras
from registros.catalogos_menu import (
    capturar_lista_asociada,
    seleccionar_o_crear_autor,
    seleccionar_o_crear_categoria,
    seleccionar_o_crear_editorial,
    seleccionar_o_crear_localizacion,
    seleccionar_o_crear_proveedor,
    seleccionar_o_crear_tipo,
)


class MenuObras:
    """Esta clase es la opcion 1: registra obra, abastece y muestra la ficha completa. Opcion 2: asigna localizacion a los ejemplares."""

    def __init__(self, obras, catalogos):
        self.obras = obras
        self.catalogos = catalogos

    def flujo_obras(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo(
                "OBRAS Y ABASTECIMIENTO",
                "Alta de obras, abastecimiento de ejemplares y consulta de ficha completa",
            )
            print("1. Registrar obra nueva (tipo, categoría, autores, editorial, proveedor y ejemplares)")
            print("2. Abastecer más ejemplares a una obra ya registrada")
            print("3. Consultar información completa de una obra")
            print("4. Actualizar datos de una obra")
            print("0. Volver\n")

            op = pedir_entero(
                "Opción", minimo=0, maximo=4, permitir_cancelar=False, permitir_atras=False
            )
            if op == 0:
                return
            if op == 1:
                self._registrar_obra_nueva()
            elif op == 2:
                self._abastecer_existente()
            elif op == 3:
                self._consultar_obra_completa()
            elif op == 4:
                self._actualizar_obra()

    def _actualizar_obra(self):
        # Cambia titulo, subtitulo, anio, paginas, tipo y categoria de una obra
        def validar_subtitulo_o_guion(texto):
            # Acepta '-' para dejar el subtitulo vacio
            if texto.strip() == "-":
                return (True, "")
            return validar_texto_descriptivo(texto)

        while True:
            limpiar_pantalla()
            mostrar_titulo("ACTUALIZAR DATOS DE UNA OBRA")

            obras = self.obras.listar_obras()
            if not obras:
                mostrar_aviso("No hay obras registradas en la base de datos.")
                pausar()
                return

            mostrar_ayuda_cancelar()
            anio_actual = date.today().year
            anio_limite = anio_actual
            isbn = None
            obra_actual = None
            titulo = None
            subtitulo = None
            anio = None
            paginas = None
            id_tipo = None
            cod_categoria = None
            paso = 0

            try:
                while paso < 7:
                    try:
                        if paso == 0:
                            mostrar_obras(obras)
                            val = pedir_texto("ISBN de la obra a editar", max_len=17).upper()
                            info = self.obras.obtener_obra_para_editar(val)
                            if not info:
                                mostrar_error("No se encontró ninguna obra con ese ISBN.")
                                continue
                            isbn = val
                            obra_actual = info
                            primera = self.obras.obtener_fecha_primera_adquisicion(isbn)
                            anio_limite = anio_actual
                            if primera is not None:
                                anio_limite = min(anio_actual, primera.year)
                            print(
                                "\n(Presiona Enter para conservar el valor actual | "
                                "en subtítulo escribe '-' para dejarlo vacío)\n"
                            )
                            paso = 1
                        elif paso == 1:
                            titulo = pedir_texto(
                                "Título (máx. 50 caracteres)",
                                max_len=50,
                                valor_defecto=obra_actual["titulo"],
                                validador=validar_titulo,
                            )
                            paso = 2
                        elif paso == 2:
                            val_sub = pedir_texto(
                                "Subtítulo (máx. 100 caracteres)",
                                max_len=100,
                                obligatorio=False,
                                valor_defecto=obra_actual["subtitulo"] or None,
                                validador=validar_subtitulo_o_guion,
                            )
                            subtitulo = None if val_sub == "-" else val_sub
                            paso = 3
                        elif paso == 3:
                            anio = pedir_entero(
                                f"Año de publicación (1450-{anio_limite})",
                                minimo=1450,
                                maximo=anio_limite,
                                valor_defecto=obra_actual["anio"],
                            )
                            paso = 4
                        elif paso == 4:
                            paginas = pedir_entero(
                                "Número de páginas (1-10000)",
                                minimo=1,
                                maximo=10000,
                                valor_defecto=obra_actual["num_paginas"],
                            )
                            paso = 5
                        elif paso == 5:
                            print(f"Tipo de obra actual: {obra_actual['tipo_obra']}")
                            if confirmar("¿Deseas cambiar el tipo de obra?"):
                                try:
                                    id_tipo = seleccionar_o_crear_tipo(self.catalogos)
                                    paso = 6
                                except PasoAnterior:
                                    mostrar_aviso("Regresando a la pregunta del tipo de obra...")
                                    continue
                            else:
                                id_tipo = obra_actual["tipo"]
                                paso = 6
                        elif paso == 6:
                            print(f"Categoría actual: {obra_actual['genero']}")
                            if confirmar("¿Deseas cambiar la categoría?"):
                                try:
                                    cod_categoria = seleccionar_o_crear_categoria(self.catalogos)
                                    paso = 7
                                except PasoAnterior:
                                    mostrar_aviso("Regresando a la pregunta de la categoría...")
                                    continue
                            else:
                                cod_categoria = obra_actual["categoria"]
                                paso = 7
                    except PasoAnterior:
                        if paso == 0:
                            mostrar_aviso("Regresando al menú anterior...")
                            return
                        paso -= 1
                        mostrar_aviso("Regresando al paso anterior...")

                self.obras.actualizar_obra(
                    isbn, titulo, subtitulo, anio, paginas, id_tipo, cod_categoria
                )
                mostrar_exito(f"Obra '{titulo}' actualizada correctamente.")
                if not confirmar_continuar("¿Deseas actualizar OTRA obra?"):
                    return
            except OperacionCancelada:
                mostrar_aviso("Operación cancelada. Regresando al menú...")
                pausar()
                return
            except (ValueError, Error) as e:
                mostrar_error(f"No se pudo actualizar la obra: {e}")
                if not confirmar_continuar("¿Deseas intentar actualizar otra obra?"):
                    return

    def _consultar_obra_completa(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo("CONSULTA DE INFORMACIÓN COMPLETA DE UNA OBRA")

            obras = self.obras.listar_obras()
            if not obras:
                mostrar_aviso("No hay obras registradas en la base de datos.")
                pausar()
                return

            mostrar_obras(obras)
            mostrar_ayuda_cancelar()
            try:
                while True:
                    isbn = pedir_texto("ISBN de la obra a consultar", max_len=17)
                    filas = self.obras.consultar_obra_completa(isbn)
                    if not filas:
                        mostrar_error("No se encontró ninguna obra con ese ISBN.")
                        continue
                    break

                base = filas[0]
                editoriales = list(dict.fromkeys(f["editorial"] for f in filas))
                paises = list(dict.fromkeys(f["pais"] for f in filas))
                autores = list(dict.fromkeys(f["autor"] for f in filas))

                mostrar_ficha(
                    f"FICHA COMPLETA DE OBRA ({base['isbn']})",
                    [
                        ("ISBN", base["isbn"]),
                        ("Título", base["titulo"]),
                        ("Subtítulo", base["subtitulo"]),
                        ("Tipo de obra", base["tipo_obra"]),
                        ("Año de publicación", base["anio_publicacion"]),
                        ("Editorial(es)", editoriales),
                        ("País(es)", paises),
                        ("Autor(es)", autores),
                    ],
                )
                if not confirmar_continuar("¿Deseas consultar OTRA obra?"):
                    return
            except (OperacionCancelada, PasoAnterior):
                return
            except Error as e:
                mostrar_error(f"Error al consultar obra: {e}")
                pausar()
                return

    def _registrar_obra_nueva(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo(
                "ALTA DE OBRA NUEVA",
                "Puedes elegir datos existentes o escribir 'nuevo' para registrarlos al momento",
            )
            mostrar_ayuda_cancelar()

            anio_actual = date.today().year
            isbn = None
            titulo = None
            subtitulo = None
            anio = None
            paginas = None
            id_tipo = None
            cod_categoria = None
            ids_autores = []
            ids_editoriales = []
            rfc_prov = None
            fecha_adq = None
            cantidad = None
            id_loc = None
            paso = 0

            try:
                while paso < 13:
                    try:
                        if paso == 0:
                            val = pedir_texto(
                                "ISBN (10 o 13 dígitos, ej. 978-84-9759-220-8)",
                                max_len=17,
                                validador=validar_isbn,
                            ).upper()
                            if self.obras.existe_obra(val):
                                mostrar_aviso(
                                    "Ese ISBN ya existe. Usa otro ISBN o elige la opción 2 para abastecer."
                                )
                                continue
                            isbn = val
                            paso = 1
                        elif paso == 1:
                            titulo = pedir_texto(
                                "Título (máx. 50 caracteres)",
                                max_len=50,
                                validador=validar_titulo,
                            )
                            paso = 2
                        elif paso == 2:
                            subtitulo = pedir_texto(
                                "Subtítulo (máx. 100 caracteres)",
                                max_len=100,
                                obligatorio=False,
                                validador=validar_texto_descriptivo,
                            )
                            paso = 3
                        elif paso == 3:
                            anio = pedir_entero(
                                f"Año de publicación (1450-{anio_actual})",
                                minimo=1450,
                                maximo=anio_actual,
                            )
                            paso = 4
                        elif paso == 4:
                            paginas = pedir_entero("Número de páginas (1-10000)", minimo=1, maximo=10000)
                            paso = 5
                        elif paso == 5:
                            id_tipo = seleccionar_o_crear_tipo(self.catalogos)
                            paso = 6
                        elif paso == 6:
                            cod_categoria = seleccionar_o_crear_categoria(self.catalogos)
                            paso = 7
                        elif paso == 7:
                            ids_autores = capturar_lista_asociada(
                                "OTRO autor",
                                "autores",
                                lambda: seleccionar_o_crear_autor(self.catalogos),
                                ids_autores,
                            )
                            paso = 8
                        elif paso == 8:
                            ids_editoriales = capturar_lista_asociada(
                                "OTRA editorial",
                                "editoriales",
                                lambda: seleccionar_o_crear_editorial(self.catalogos),
                                ids_editoriales,
                            )
                            paso = 9
                        elif paso == 9:
                            rfc_prov = seleccionar_o_crear_proveedor(self.catalogos)
                            paso = 10
                        elif paso == 10:
                            fecha_min_adq = date(max(1900, anio), 1, 1)
                            fecha_adq = pedir_fecha(
                                "Fecha de adquisición",
                                fecha_min=fecha_min_adq,
                                permitir_futuro=False,
                            )
                            paso = 11
                        elif paso == 11:
                            cantidad = pedir_entero(
                                "Cantidad de ejemplares recibidos (1-500)",
                                minimo=1,
                                maximo=500,
                            )
                            paso = 12
                        elif paso == 12:
                            if not self.catalogos.listar_localizaciones():
                                mostrar_aviso(
                                    "No hay localizaciones en la BD. Registra una para los ejemplares:"
                                )
                                id_loc = seleccionar_o_crear_localizacion(self.catalogos, 
                                    permitir_sin_asignar=False
                                )
                                paso = 13
                            else:
                                asignar = confirmar(
                                    "¿Deseas asignar una localización específica desde ahora? (No = Sin asignar)"
                                )
                                if asignar:
                                    try:
                                        id_loc = seleccionar_o_crear_localizacion(self.catalogos, 
                                            permitir_sin_asignar=True
                                        )
                                        paso = 13
                                    except PasoAnterior:
                                        mostrar_aviso("Regresando a la pregunta de localización...")
                                        continue
                                else:
                                    id_loc = None
                                    paso = 13
                    except PasoAnterior:
                        if paso == 0:
                            mostrar_aviso("Regresando al menú anterior...")
                            return
                        paso -= 1
                        mostrar_aviso("Regresando al paso anterior...")

                obra = Obra(
                    isbn=isbn,
                    titulo=titulo,
                    subtitulo=subtitulo,
                    anio_publicacion=anio,
                    num_paginas=paginas,
                    tipo=id_tipo,
                    categoria=cod_categoria,
                    autores=ids_autores,
                    editoriales=ids_editoriales,
                )

                inicio, fin = self.obras.registrar_obra_completa(
                    obra, rfc_prov, fecha_adq, cantidad, id_localizacion=id_loc
                )
                mostrar_exito(
                    f"Obra '{obra.titulo}' registrada con éxito. "
                    f"Se generaron los ejemplares #{inicio} al #{fin}."
                )
                if not confirmar_continuar("¿Deseas registrar OTRA obra nueva?"):
                    return
            except OperacionCancelada:
                mostrar_aviso("Operación cancelada. Regresando al menú...")
                pausar()
                return
            except (ValueError, Error) as e:
                mostrar_error(f"No se pudo registrar la obra: {e}")
                if not confirmar_continuar("¿Deseas intentar registrar otra obra?"):
                    return

    def _abastecer_existente(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo("ABASTECER OBRA EXISTENTE")

            obras = self.obras.listar_obras()
            if not obras:
                mostrar_aviso("No hay obras registradas todavía. Usa la opción 1 para dar de alta una.")
                pausar()
                return

            mostrar_ayuda_cancelar()
            isbn = None
            obra_bd = None
            rfc_prov = None
            fecha_adq = None
            cantidad = None
            id_loc = None
            paso = 0

            try:
                while paso < 5:
                    try:
                        if paso == 0:
                            mostrar_obras(obras)
                            val = pedir_texto("ISBN de la obra a abastecer", max_len=17)
                            info = self.obras.obtener_obra(val)
                            if not info:
                                mostrar_error("No se encontró ninguna obra con ese ISBN.")
                                continue
                            isbn = val
                            obra_bd = info
                            paso = 1
                        elif paso == 1:
                            rfc_prov = seleccionar_o_crear_proveedor(self.catalogos)
                            paso = 2
                        elif paso == 2:
                            fecha_min_adq = date(max(1900, obra_bd["anio"]), 1, 1)
                            fecha_adq = pedir_fecha(
                                "Fecha de adquisición",
                                fecha_min=fecha_min_adq,
                                permitir_futuro=False,
                            )
                            paso = 3
                        elif paso == 3:
                            cantidad = pedir_entero(
                                "Cantidad de nuevos ejemplares (1-500)",
                                minimo=1,
                                maximo=500,
                            )
                            paso = 4
                        elif paso == 4:
                            if not self.catalogos.listar_localizaciones():
                                id_loc = seleccionar_o_crear_localizacion(self.catalogos, 
                                    permitir_sin_asignar=False
                                )
                                paso = 5
                            else:
                                asignar = confirmar(
                                    "¿Asignar una localización específica a estos ejemplares?"
                                )
                                if asignar:
                                    try:
                                        id_loc = seleccionar_o_crear_localizacion(self.catalogos, 
                                            permitir_sin_asignar=True
                                        )
                                        paso = 5
                                    except PasoAnterior:
                                        mostrar_aviso("Regresando a la pregunta de localización...")
                                        continue
                                else:
                                    id_loc = None
                                    paso = 5
                    except PasoAnterior:
                        if paso == 0:
                            mostrar_aviso("Regresando al menú anterior...")
                            return
                        paso -= 1
                        mostrar_aviso("Regresando al paso anterior...")

                inicio, fin = self.obras.abastecer_obra_existente(
                    isbn, rfc_prov, fecha_adq, cantidad, id_localizacion=id_loc
                )
                mostrar_exito(
                    f"Abastecimiento guardado. Nuevos ejemplares generados: #{inicio} al #{fin}."
                )
                if not confirmar_continuar("¿Deseas registrar OTRO abastecimiento?"):
                    return
            except OperacionCancelada:
                mostrar_aviso("Operación cancelada. Regresando al menú...")
                pausar()
                return
            except (ValueError, Error) as e:
                mostrar_error(f"No se pudo registrar el abastecimiento: {e}")
                if not confirmar_continuar("¿Deseas intentar otro abastecimiento?"):
                    return

    def flujo_asignar_localizacion(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo("ASIGNAR LOCALIZACIÓN A EJEMPLARES")

            obras = self.obras.listar_obras()
            if not obras:
                mostrar_aviso("No hay obras registradas.")
                pausar()
                return

            mostrar_ayuda_cancelar()
            isbn = None
            ejemplares = []
            id_loc = None
            aplicar_todos = False
            num_ej = None
            paso = 0

            try:
                while paso < 4:
                    try:
                        if paso == 0:
                            mostrar_obras(obras)
                            val = pedir_texto("ISBN de la obra", max_len=17)
                            ejs = self.obras.listar_ejemplares_obra(val)
                            if not ejs:
                                mostrar_error("Esa obra no existe o no tiene ejemplares registrados.")
                                continue
                            isbn = val
                            ejemplares = ejs
                            filas = [
                                (
                                    e["ejemplar"],
                                    e["localizacion"],
                                    e["seccion"],
                                    e["pasillo"],
                                    e["estante"],
                                    e["estado"],
                                )
                                for e in ejemplares
                            ]
                            mostrar_tabla(
                                f"Ejemplares de {isbn}",
                                ["Ejemplar #", "ID Loc.", "Sección", "Pasillo", "Estante", "Estado"],
                                filas,
                            )
                            paso = 1
                        elif paso == 1:
                            id_loc = seleccionar_o_crear_localizacion(self.catalogos, 
                                permitir_sin_asignar=False
                            )
                            paso = 2
                        elif paso == 2:
                            aplicar_todos = confirmar(
                                "¿Aplicar esta localización a TODOS los ejemplares de esta obra?"
                            )
                            paso = 4 if aplicar_todos else 3
                        elif paso == 3:
                            numeros_validos = [e["ejemplar"] for e in ejemplares]
                            val_ej = pedir_entero("Número de ejemplar específico", minimo=1)
                            if val_ej not in numeros_validos:
                                mostrar_error(
                                    f"Ese ejemplar no existe. Disponibles en esta obra: {numeros_validos}"
                                )
                                continue
                            num_ej = val_ej
                            paso = 4
                    except PasoAnterior:
                        if paso == 0:
                            mostrar_aviso("Regresando al menú anterior...")
                            return
                        paso -= 1
                        mostrar_aviso("Regresando al paso anterior...")

                if aplicar_todos:
                    afectados = self.obras.asignar_localizacion_todos(isbn, id_loc)
                    mostrar_exito(
                        f"Se actualizaron {afectados} ejemplares a la localización #{id_loc}."
                    )
                else:
                    self.obras.asignar_localizacion_ejemplar(isbn, num_ej, id_loc)
                    mostrar_exito(f"Ejemplar #{num_ej} actualizado a la localización #{id_loc}.")

                if not confirmar_continuar(
                    "¿Deseas asignar localización a OTRA obra o ejemplar?"
                ):
                    return
            except OperacionCancelada:
                mostrar_aviso("Operación cancelada. Regresando al menú...")
                pausar()
                return
            except Error as e:
                mostrar_error(f"Error al actualizar localización: {e}")
                if not confirmar_continuar("¿Deseas intentar otra asignación?"):
                    return
