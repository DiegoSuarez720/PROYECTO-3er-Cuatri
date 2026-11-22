"""Archivo principal con los menús en terminal (CLI estándar) para Registros y Catálogos."""

from datetime import timedelta
from mysql.connector import Error

from conexion import ConexionDB
from modelos import (
    Autor,
    Categoria,
    Editorial,
    Empleado,
    Localizacion,
    Obra,
    Pais,
    Prestamo,
    Proveedor,
    TipoObra,
    Usuario,
)
from operaciones import (
    GestorAuth,
    GestorCatalogos,
    GestorMultas,
    GestorObras,
    GestorPrestamos,
    TARIFA_MULTA_DIA,
)
from utilidades import (
    OperacionCancelada,
    confirmar,
    limpiar_pantalla,
    mostrar_aviso,
    mostrar_ayuda_cancelar,
    mostrar_error,
    mostrar_exito,
    mostrar_tabla,
    mostrar_titulo,
    pausar,
    pedir_entero,
    pedir_fecha,
    pedir_texto,
)


class AplicacionBiblioteca:
    """Controla el flujo de menús en terminal para los 5 registros y catálogos."""

    def __init__(self):
        self.auth = GestorAuth()
        self.catalogos = GestorCatalogos()
        self.obras = GestorObras()
        self.prestamos = GestorPrestamos()
        self.multas = GestorMultas()
        self.empleado_activo = None

    def ejecutar(self):
        """Punto de entrada del programa."""
        try:
            ConexionDB().conectar()
        except ConnectionError as e:
            mostrar_error(str(e))
            return

        try:
            while True:
                if not self.iniciar_sesion():
                    break
                self.menu_principal()
        finally:
            ConexionDB().cerrar()
            print("\nConexión cerrada. ¡Hasta luego!")

    # ==========================================================
    # INICIO DE SESIÓN
    # ==========================================================
    def iniciar_sesion(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo(
                "SISTEMA DE PRÉSTAMOS BIBLIOTECARIOS",
                "Inicio de sesión de empleados (escribe 'salir' en usuario para terminar)",
            )
            usuario = pedir_texto("Usuario", max_len=30, permitir_cancelar=False)
            if usuario.lower() in ("salir", "cancelar"):
                return False

            try:
                contrasena = pedir_texto(
                    "Contraseña (o escribe 'cancelar' para cambiar usuario)", max_len=50
                )
            except OperacionCancelada:
                continue

            try:
                empleado = self.auth.iniciar_sesion(usuario, contrasena)
            except Error as e:
                mostrar_error(f"Error al consultar empleado: {e}")
                pausar()
                continue

            if empleado:
                self.empleado_activo = empleado
                mostrar_exito(f"Bienvenido, {empleado.nombre_completo}.")
                pausar()
                return True

            mostrar_error("Usuario o contraseña incorrectos.")
            pausar()

    # ==========================================================
    # MENÚ PRINCIPAL
    # ==========================================================
    def menu_principal(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo(
                "MENÚ PRINCIPAL - REGISTROS Y CATÁLOGOS",
                f"Empleado en sesión: {self.empleado_activo.nombre_completo} (@{self.empleado_activo.nombre_user})",
            )
            print("1. Registro 1: Obra completa / Abastecer ejemplares")
            print("2. Registro 2: Asignar localización a ejemplares")
            print("3. Registro 3: Préstamo de ejemplares")
            print("4. Registro 4: Devolución de ejemplares")
            print("5. Registro 5: Multas por devolución tardía")
            print("6. Catálogos auxiliares (Autores, Usuarios, Proveedores, etc.)")
            print("7. Listados rápidos de apoyo")
            print("0. Cerrar sesión\n")

            opcion = pedir_entero(
                "Selecciona una opción", minimo=0, maximo=7, permitir_cancelar=False
            )

            if opcion == 1:
                self.flujo_registro_obra()
            elif opcion == 2:
                self.flujo_asignar_localizacion()
            elif opcion == 3:
                self.flujo_registrar_prestamo()
            elif opcion == 4:
                self.flujo_registrar_devolucion()
            elif opcion == 5:
                self.flujo_multas()
            elif opcion == 6:
                self.menu_catalogos()
            elif opcion == 7:
                self.menu_listados_apoyo()
            elif opcion == 0:
                self.empleado_activo = None
                break

    # ==========================================================
    # REGISTRO 1: OBRA COMPLETA / ABASTECIMIENTO
    # ==========================================================
    def flujo_registro_obra(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo(
                "REGISTRO 1: OBRA COMPLETA Y ABASTECIMIENTO",
                "Registra una obra nueva o agrega más ejemplares a una existente",
            )
            print("1. Registrar obra nueva (con autores, editorial, proveedor y ejemplares)")
            print("2. Abastecer más ejemplares a una obra ya registrada")
            print("0. Volver\n")

            op = pedir_entero("Opción", minimo=0, maximo=2, permitir_cancelar=False)
            if op == 0:
                return
            if op == 1:
                self._registrar_obra_nueva()
            elif op == 2:
                self._abastecer_existente()

    def _registrar_obra_nueva(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo("REGISTRO 1: ALTA DE OBRA NUEVA")

            tipos = self.catalogos.listar_tipos()
            categorias = self.catalogos.listar_categorias()
            autores = self.catalogos.listar_autores()
            editoriales = self.catalogos.listar_editoriales()
            proveedores = self.catalogos.listar_proveedores()
            localizaciones = self.catalogos.listar_localizaciones()

            faltantes = []
            if not tipos:
                faltantes.append("Tipos de obra")
            if not categorias:
                faltantes.append("Categorías")
            if not autores:
                faltantes.append("Autores")
            if not editoriales:
                faltantes.append("Editoriales")
            if not proveedores:
                faltantes.append("Proveedores")
            if not localizaciones:
                faltantes.append("Localizaciones")

            if faltantes:
                mostrar_aviso(
                    "Antes de registrar una obra, captura al menos un registro en: "
                    + ", ".join(faltantes)
                    + " (en la opción 6 - Catálogos auxiliares)."
                )
                pausar()
                return

            mostrar_ayuda_cancelar()
            try:
                while True:
                    isbn = pedir_texto("ISBN (máx. 17 caracteres)", max_len=17)
                    if isbn == "0":
                        raise OperacionCancelada()
                    if self.obras.existe_obra(isbn):
                        mostrar_aviso(
                            "Ese ISBN ya existe. Usa otro ISBN o elige la opción 2 para abastecer."
                        )
                        continue
                    break

                titulo = pedir_texto("Título (máx. 50 caracteres)", max_len=50)
                subtitulo = pedir_texto(
                    "Subtítulo (máx. 100 caracteres)", max_len=100, obligatorio=False
                )
                anio = pedir_entero("Año de publicación (4 dígitos)", minimo=1000, maximo=2100)
                paginas = pedir_entero("Número de páginas", minimo=1)

                self._mostrar_tipos(tipos)
                while True:
                    id_tipo = pedir_entero("ID del tipo de obra (0 para cancelar)", minimo=0)
                    if id_tipo == 0:
                        raise OperacionCancelada()
                    if not self.catalogos.existe_tipo(id_tipo):
                        mostrar_error("Ese ID de tipo de obra no existe.")
                        continue
                    break

                self._mostrar_categorias(categorias)
                while True:
                    cod_categoria = pedir_texto("Código de categoría", max_len=5).upper()
                    if cod_categoria == "0":
                        raise OperacionCancelada()
                    if not self.catalogos.existe_categoria(cod_categoria):
                        mostrar_error("Ese código de categoría no existe.")
                        continue
                    break

                self._mostrar_autores(autores)
                ids_autores = []
                while True:
                    id_autor = pedir_entero("ID del autor a asociar (0 para cancelar)", minimo=0)
                    if id_autor == 0:
                        raise OperacionCancelada()
                    if not self.catalogos.existe_autor(id_autor):
                        mostrar_error("Ese ID de autor no existe.")
                        continue
                    if id_autor in ids_autores:
                        mostrar_aviso("Ese autor ya fue agregado a esta obra.")
                    else:
                        ids_autores.append(id_autor)
                    if not confirmar("¿Deseas agregar OTRO autor a esta obra?"):
                        break

                self._mostrar_editoriales(editoriales)
                ids_editoriales = []
                while True:
                    id_ed = pedir_entero("ID de la editorial a asociar (0 para cancelar)", minimo=0)
                    if id_ed == 0:
                        raise OperacionCancelada()
                    if not self.catalogos.existe_editorial(id_ed):
                        mostrar_error("Ese ID de editorial no existe.")
                        continue
                    if id_ed in ids_editoriales:
                        mostrar_aviso("Esa editorial ya fue agregada a esta obra.")
                    else:
                        ids_editoriales.append(id_ed)
                    if not confirmar("¿Deseas agregar OTRA editorial a esta obra?"):
                        break

                self._mostrar_proveedores(proveedores)
                while True:
                    rfc_prov = pedir_texto("RFC del proveedor", max_len=13).upper()
                    if rfc_prov == "0":
                        raise OperacionCancelada()
                    if not self.catalogos.existe_proveedor(rfc_prov):
                        mostrar_error("Ese RFC de proveedor no existe.")
                        continue
                    break

                fecha_adq = pedir_fecha("Fecha de adquisición")
                cantidad = pedir_entero("Cantidad de ejemplares recibidos", minimo=1)

                id_loc = None
                if confirmar(
                    "¿Deseas asignar una localización específica desde ahora? (No = Sin asignar)"
                ):
                    self._mostrar_localizaciones(localizaciones)
                    while True:
                        id_loc = pedir_entero("ID de localización (0 para usar Sin asignar)", minimo=0)
                        if id_loc == 0:
                            id_loc = None
                            break
                        if not self.catalogos.existe_localizacion(id_loc):
                            mostrar_error("Ese ID de localización no existe.")
                            continue
                        break

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
                if not confirmar("¿Deseas registrar OTRA obra nueva?"):
                    return
            except OperacionCancelada:
                mostrar_aviso("Operación cancelada. Regresando al menú...")
                pausar()
                return
            except (ValueError, Error) as e:
                mostrar_error(f"No se pudo registrar la obra: {e}")
                if not confirmar("¿Deseas intentar registrar otra obra?"):
                    return

    def _abastecer_existente(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo("REGISTRO 1: ABASTECER OBRA EXISTENTE")

            obras = self.obras.listar_obras()
            proveedores = self.catalogos.listar_proveedores()
            if not obras or not proveedores:
                mostrar_aviso("Necesitas al menos una obra y un proveedor registrados.")
                pausar()
                return

            mostrar_ayuda_cancelar()
            try:
                self._mostrar_obras(obras)
                while True:
                    isbn = pedir_texto("ISBN de la obra a abastecer", max_len=17)
                    if isbn == "0":
                        raise OperacionCancelada()
                    if not self.obras.existe_obra(isbn):
                        mostrar_error("No se encontró ninguna obra con ese ISBN.")
                        continue
                    break

                self._mostrar_proveedores(proveedores)
                while True:
                    rfc_prov = pedir_texto("RFC del proveedor", max_len=13).upper()
                    if rfc_prov == "0":
                        raise OperacionCancelada()
                    if not self.catalogos.existe_proveedor(rfc_prov):
                        mostrar_error("Ese RFC de proveedor no existe.")
                        continue
                    break

                fecha_adq = pedir_fecha("Fecha de adquisición")
                cantidad = pedir_entero("Cantidad de nuevos ejemplares", minimo=1)

                id_loc = None
                if confirmar("¿Asignar una localización específica a estos ejemplares?"):
                    locs = self.catalogos.listar_localizaciones()
                    self._mostrar_localizaciones(locs)
                    while True:
                        id_loc = pedir_entero("ID de localización (0 para Sin asignar)", minimo=0)
                        if id_loc == 0:
                            id_loc = None
                            break
                        if not self.catalogos.existe_localizacion(id_loc):
                            mostrar_error("Ese ID de localización no existe.")
                            continue
                        break

                inicio, fin = self.obras.abastecer_obra_existente(
                    isbn, rfc_prov, fecha_adq, cantidad, id_localizacion=id_loc
                )
                mostrar_exito(
                    f"Abastecimiento guardado. Nuevos ejemplares generados: #{inicio} al #{fin}."
                )
                if not confirmar("¿Deseas registrar OTRO abastecimiento?"):
                    return
            except OperacionCancelada:
                mostrar_aviso("Operación cancelada. Regresando al menú...")
                pausar()
                return
            except (ValueError, Error) as e:
                mostrar_error(f"No se pudo registrar el abastecimiento: {e}")
                if not confirmar("¿Deseas intentar otro abastecimiento?"):
                    return

    # ==========================================================
    # REGISTRO 2: ASIGNAR LOCALIZACIÓN A EJEMPLARES
    # ==========================================================
    def flujo_asignar_localizacion(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo("REGISTRO 2: ASIGNAR LOCALIZACIÓN A EJEMPLARES")

            obras = self.obras.listar_obras()
            locs = self.catalogos.listar_localizaciones()
            if not obras:
                mostrar_aviso("No hay obras registradas.")
                pausar()
                return
            if not locs:
                mostrar_aviso("No hay localizaciones registradas.")
                pausar()
                return

            mostrar_ayuda_cancelar()
            try:
                self._mostrar_obras(obras)
                while True:
                    isbn = pedir_texto("ISBN de la obra", max_len=17)
                    if isbn == "0":
                        raise OperacionCancelada()
                    ejemplares = self.obras.listar_ejemplares_obra(isbn)
                    if not ejemplares:
                        mostrar_error("Esa obra no existe o no tiene ejemplares registrados.")
                        continue
                    break

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

                self._mostrar_localizaciones(locs)
                while True:
                    id_loc = pedir_entero("Nuevo ID de localización (0 para cancelar)", minimo=0)
                    if id_loc == 0:
                        raise OperacionCancelada()
                    if not self.catalogos.existe_localizacion(id_loc):
                        mostrar_error("Ese ID de localización no existe.")
                        continue
                    break

                if confirmar("¿Aplicar esta localización a TODOS los ejemplares de esta obra?"):
                    afectados = self.obras.asignar_localizacion_todos(isbn, id_loc)
                    mostrar_exito(
                        f"Se actualizaron {afectados} ejemplares a la localización #{id_loc}."
                    )
                else:
                    numeros_validos = [e["ejemplar"] for e in ejemplares]
                    while True:
                        num_ej = pedir_entero(
                            "Número de ejemplar específico (0 para cancelar)", minimo=0
                        )
                        if num_ej == 0:
                            raise OperacionCancelada()
                        if num_ej not in numeros_validos:
                            mostrar_error(
                                f"Ese ejemplar no existe. Disponibles en esta obra: {numeros_validos}"
                            )
                            continue
                        break
                    self.obras.asignar_localizacion_ejemplar(isbn, num_ej, id_loc)
                    mostrar_exito(f"Ejemplar #{num_ej} actualizado a la localización #{id_loc}.")

                if not confirmar("¿Deseas asignar localización a OTRA obra o ejemplar?"):
                    return
            except OperacionCancelada:
                mostrar_aviso("Operación cancelada. Regresando al menú...")
                pausar()
                return
            except Error as e:
                mostrar_error(f"Error al actualizar localización: {e}")
                if not confirmar("¿Deseas intentar otra asignación?"):
                    return

    # ==========================================================
    # REGISTRO 3: PRÉSTAMO DE EJEMPLARES
    # ==========================================================
    def flujo_registrar_prestamo(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo(
                "REGISTRO 3: PRÉSTAMO DE EJEMPLARES",
                "Plazo automático de devolución: 2 semanas (14 días)",
            )

            usuarios = self.catalogos.listar_usuarios()
            resumen_disp = self.prestamos.listar_resumen_disponibles()
            if not usuarios:
                mostrar_aviso("Registra primero al menos un usuario en Catálogos auxiliares.")
                pausar()
                return
            if not resumen_disp:
                mostrar_aviso("No hay ejemplares disponibles para préstamo.")
                pausar()
                return

            mostrar_ayuda_cancelar()
            try:
                self._mostrar_usuarios(usuarios)
                while True:
                    id_usuario = pedir_entero("ID del usuario (0 para cancelar)", minimo=0)
                    if id_usuario == 0:
                        raise OperacionCancelada()
                    if not self.catalogos.existe_usuario(id_usuario):
                        mostrar_error("No existe ningún usuario con ese ID. Intenta de nuevo.")
                        continue
                    break

                fecha_salida = pedir_fecha("Fecha de salida del préstamo")
                fecha_limite = fecha_salida + timedelta(days=Prestamo.DIAS_PLAZO)
                print(f"Fecha límite calculada automáticamente (+14 días): {fecha_limite}")

                self._mostrar_resumen_disponibles(resumen_disp)

                seleccionados = []
                while True:
                    if seleccionados:
                        etiqueta_isbn = (
                            "ISBN de otra obra (0 para guardar préstamo, 'cancelar' para anular)"
                        )
                    else:
                        etiqueta_isbn = "ISBN de la obra a prestar ('cancelar' para regresar)"

                    isbn = pedir_texto(etiqueta_isbn, max_len=17)
                    if isbn == "0":
                        break

                    if not self.obras.existe_obra(isbn):
                        mostrar_error("Ese ISBN no existe en el catálogo. Intenta con otro.")
                        continue

                    copias_bd = self.prestamos.obtener_ejemplares_disponibles_por_isbn(isbn)
                    copias_libres = [
                        c for c in copias_bd if (isbn, c["ejemplar"]) not in seleccionados
                    ]

                    if not copias_libres:
                        mostrar_aviso(
                            "Esta obra ya no tiene ejemplares disponibles (están prestados o ya los agregaste)."
                        )
                        continue

                    numeros_libres = [c["ejemplar"] for c in copias_libres]
                    titulo_obra = copias_libres[0]["titulo"]
                    lista_txt = ", ".join(f"#{n}" for n in numeros_libres)
                    print(f"\nObra: {titulo_obra}")
                    print(f"Ejemplares disponibles para prestar: {lista_txt}")

                    while True:
                        num_ej = pedir_entero(
                            "Número de ejemplar a prestar (0 para elegir otro ISBN)",
                            minimo=0,
                        )
                        if num_ej == 0:
                            break
                        if num_ej not in numeros_libres:
                            mostrar_error(
                                f"El ejemplar #{num_ej} no existe o no está disponible. "
                                f"Opciones válidas: {lista_txt}"
                            )
                            if confirmar("¿Deseas elegir otro ISBN?"):
                                break
                            continue

                        seleccionados.append((isbn, num_ej))
                        mostrar_exito(
                            f"Agregado al préstamo: {titulo_obra} ({isbn}) - Ejemplar #{num_ej}"
                        )
                        break

                    if seleccionados:
                        if not confirmar("¿Deseas agregar OTRO ejemplar a este mismo préstamo?"):
                            break
                    else:
                        if not confirmar(
                            "Aún no agregas ejemplares. ¿Deseas intentar con otro ISBN?"
                        ):
                            break

                if not seleccionados:
                    mostrar_aviso("Préstamo cancelado (no se seleccionaron ejemplares).")
                    pausar()
                    return

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
                    f"Ejemplares: {len(seleccionados)} | Fecha límite: {fecha_limite}"
                )
                if not confirmar("¿Deseas registrar OTRO préstamo?"):
                    return
            except OperacionCancelada:
                mostrar_aviso("Préstamo cancelado. Regresando al menú...")
                pausar()
                return
            except (ValueError, Error) as e:
                mostrar_error(f"No se pudo registrar el préstamo: {e}")
                if not confirmar("¿Deseas intentar registrar otro préstamo?"):
                    return

    # ==========================================================
    # REGISTRO 4: DEVOLUCIÓN DE EJEMPLARES (CON MULTA AUTOMÁTICA)
    # ==========================================================
    def flujo_registrar_devolucion(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo(
                "REGISTRO 4: DEVOLUCIÓN DE EJEMPLARES",
                f"Recibe: {self.empleado_activo.nombre_completo} (multa automática si hay retraso: ${TARIFA_MULTA_DIA}/día)",
            )

            activos = self.prestamos.listar_prestamos_activos_resumen()
            if not activos:
                mostrar_aviso("No hay préstamos activos con devoluciones pendientes.")
                pausar()
                return

            mostrar_ayuda_cancelar()
            try:
                self._mostrar_prestamos_activos_resumen(activos)

                while True:
                    folio = pedir_entero("Folio del préstamo a devolver (0 para cancelar)", minimo=0)
                    if folio == 0:
                        raise OperacionCancelada()
                    pendientes = self.prestamos.listar_ejemplares_pendientes_prestamo(folio)
                    if not pendientes:
                        mostrar_error("Ese folio no existe o ya no tiene ejemplares pendientes.")
                        continue
                    break

                filas = [
                    (p["obra"], p["titulo"], p["ejemplar"], p["fecha_salida"], p["fecha_limite"])
                    for p in pendientes
                ]
                mostrar_tabla(
                    f"Ejemplares pendientes del Préstamo #{folio}",
                    ["ISBN", "Título", "Ejemplar #", "Fecha Salida", "Fecha Límite"],
                    filas,
                )

                isbns_pendientes = list(dict.fromkeys(p["obra"] for p in pendientes))
                while True:
                    isbn = pedir_texto("ISBN del ejemplar devuelto", max_len=17)
                    if isbn == "0":
                        raise OperacionCancelada()
                    if isbn not in isbns_pendientes:
                        mostrar_error(
                            "Ese ISBN no corresponde a ningún ejemplar pendiente de este préstamo."
                        )
                        continue
                    break

                ejemplares_isbn = [p for p in pendientes if p["obra"] == isbn]
                nums_validos = [p["ejemplar"] for p in ejemplares_isbn]
                print(
                    f"Ejemplares pendientes de '{ejemplares_isbn[0]['titulo']}': "
                    + ", ".join(f"#{n}" for n in nums_validos)
                )

                while True:
                    num_ej = pedir_entero("Número de ejemplar devuelto (0 para cancelar)", minimo=0)
                    if num_ej == 0:
                        raise OperacionCancelada()
                    if num_ej not in nums_validos:
                        mostrar_error(
                            f"El ejemplar #{num_ej} no está pendiente en este préstamo. "
                            f"Opciones válidas: {nums_validos}"
                        )
                        continue
                    break

                fecha_salida = ejemplares_isbn[0]["fecha_salida"]
                while True:
                    fecha_dev = pedir_fecha("Fecha real de devolución")
                    if fecha_dev < fecha_salida:
                        mostrar_error(
                            f"La fecha de devolución no puede ser anterior a la fecha de salida ({fecha_salida})."
                        )
                        continue
                    break

                resultado = self.prestamos.registrar_devolucion(
                    folio, isbn, num_ej, fecha_dev, self.empleado_activo.id_empleado
                )
                mostrar_exito(f"Devolución #{resultado['id_devolucion']} registrada correctamente.")
                if resultado["con_retraso"]:
                    mostrar_aviso(
                        f"Entrega con RETRASO de {resultado['dias_retraso']} día(s) "
                        f"(fecha límite: {resultado['fecha_limite']})."
                    )
                    mostrar_aviso(
                        f"Multa #{resultado['id_multa']} generada automáticamente: "
                        f"{resultado['dias_retraso']} día(s) x ${resultado['monto_dia']} = "
                        f"${resultado['total']} [Pendiente]."
                    )
                else:
                    mostrar_exito("Devolución entregada a tiempo (sin multa).")

                if not self.prestamos.listar_prestamos_activos_resumen():
                    mostrar_aviso("Ya no quedan más préstamos activos pendientes.")
                    pausar()
                    return
                if not confirmar("¿Deseas registrar OTRA devolución?"):
                    return
            except OperacionCancelada:
                mostrar_aviso("Operación cancelada. Regresando al menú...")
                pausar()
                return
            except (ValueError, Error) as e:
                mostrar_error(f"No se pudo registrar la devolución: {e}")
                if not confirmar("¿Deseas intentar otra devolución?"):
                    return

    # ==========================================================
    # REGISTRO 5: MULTAS POR DEVOLUCIÓN TARDÍA
    # ==========================================================
    def flujo_multas(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo(
                "REGISTRO 5: MULTAS POR DEVOLUCIÓN TARDÍA",
                f"Las multas se generan automáticamente al devolver tarde (${TARIFA_MULTA_DIA}/día)",
            )
            print("1. Generar automáticamente multas faltantes (para devoluciones tardías sin multa)")
            print("2. Marcar una multa pendiente como 'Pagada'")
            print("3. Ver historial completo de multas")
            print("0. Volver\n")

            op = pedir_entero("Opción", minimo=0, maximo=3, permitir_cancelar=False)

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
                self._mostrar_multas(self.multas.listar_multas())
                pausar()

    def _pagar_multas(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo("COBRO DE MULTAS PENDIENTES")
            pendientes = self.multas.listar_multas(solo_pendientes=True)
            if not pendientes:
                mostrar_aviso("No hay multas pendientes de pago.")
                pausar()
                return

            self._mostrar_multas(pendientes)
            mostrar_ayuda_cancelar()
            try:
                while True:
                    id_multa = pedir_entero("ID de la multa a pagar (0 para cancelar)", minimo=0)
                    if id_multa == 0:
                        raise OperacionCancelada()
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
                if not confirmar("¿Deseas marcar OTRA multa pendiente como 'Pagada'?"):
                    return
            except OperacionCancelada:
                mostrar_aviso("Operación cancelada. Regresando al menú...")
                pausar()
                return
            except Error as e:
                mostrar_error(f"Error al actualizar la multa: {e}")
                if not confirmar("¿Deseas intentar con otra multa?"):
                    return

    # ==========================================================
    # CATÁLOGOS AUXILIARES
    # ==========================================================
    def menu_catalogos(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo("CATÁLOGOS AUXILIARES")
            print("1. Países")
            print("2. Tipos de obra")
            print("3. Categorías / Géneros")
            print("4. Autores")
            print("5. Editoriales")
            print("6. Proveedores y teléfonos")
            print("7. Localizaciones (Sección / Pasillo / Estante)")
            print("8. Usuarios y teléfonos")
            print("9. Empleados")
            print("0. Volver al menú principal\n")

            op = pedir_entero(
                "Selecciona un catálogo", minimo=0, maximo=9, permitir_cancelar=False
            )

            if op == 0:
                break
            elif op == 1:
                self._catalogo_paises()
            elif op == 2:
                self._catalogo_tipos()
            elif op == 3:
                self._catalogo_categorias()
            elif op == 4:
                self._catalogo_autores()
            elif op == 5:
                self._catalogo_editoriales()
            elif op == 6:
                self._catalogo_proveedores()
            elif op == 7:
                self._catalogo_localizaciones()
            elif op == 8:
                self._catalogo_usuarios()
            elif op == 9:
                self._catalogo_empleados()

    def _catalogo_paises(self):
        primera_vez = True
        while True:
            limpiar_pantalla()
            mostrar_titulo("CATÁLOGO DE PAÍSES")
            self._mostrar_paises(self.catalogos.listar_paises())
            try:
                if primera_vez:
                    if not confirmar("¿Registrar un nuevo país?"):
                        return
                    primera_vez = False

                mostrar_ayuda_cancelar()
                while True:
                    clave = pedir_texto(
                        "Clave de país (ej. MEX, ESP, USA; máx. 5)", max_len=5
                    ).upper()
                    if self.catalogos.existe_pais(clave):
                        mostrar_error(f"Ya existe un país registrado con la clave '{clave}'.")
                        continue
                    break
                while True:
                    nombre = pedir_texto("Nombre del país", max_len=50)
                    if self.catalogos.existe_pais_nombre(nombre):
                        mostrar_error(f"Ya existe un país registrado con el nombre '{nombre}'.")
                        continue
                    break
                self.catalogos.crear_pais(Pais(clave, nombre))
                mostrar_exito("País registrado correctamente.")
                if not confirmar("¿Deseas registrar OTRO país?"):
                    return
            except OperacionCancelada:
                mostrar_aviso("Operación cancelada. Regresando al menú...")
                pausar()
                return
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
                if not confirmar("¿Deseas intentar registrar otro país?"):
                    return

    def _catalogo_tipos(self):
        primera_vez = True
        while True:
            limpiar_pantalla()
            mostrar_titulo("CATÁLOGO DE TIPOS DE OBRA")
            self._mostrar_tipos(self.catalogos.listar_tipos())
            try:
                if primera_vez:
                    if not confirmar("¿Registrar un nuevo tipo de obra?"):
                        return
                    primera_vez = False

                mostrar_ayuda_cancelar()
                while True:
                    nombre = pedir_texto("Tipo de obra (ej. Libro, Revista, Tesis)", max_len=50)
                    if self.catalogos.existe_tipo_nombre(nombre):
                        mostrar_error(f"Ya existe un tipo de obra registrado como '{nombre}'.")
                        continue
                    break
                nuevo_id = self.catalogos.crear_tipo(TipoObra(nombre))
                mostrar_exito(f"Tipo de obra registrado con ID #{nuevo_id}.")
                if not confirmar("¿Deseas registrar OTRO tipo de obra?"):
                    return
            except OperacionCancelada:
                mostrar_aviso("Operación cancelada. Regresando al menú...")
                pausar()
                return
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
                if not confirmar("¿Deseas intentar registrar otro tipo de obra?"):
                    return

    def _catalogo_categorias(self):
        primera_vez = True
        while True:
            limpiar_pantalla()
            mostrar_titulo("CATÁLOGO DE CATEGORÍAS")
            self._mostrar_categorias(self.catalogos.listar_categorias())
            try:
                if primera_vez:
                    if not confirmar("¿Registrar una nueva categoría?"):
                        return
                    primera_vez = False

                mostrar_ayuda_cancelar()
                while True:
                    codigo = pedir_texto(
                        "Código de categoría (ej. FIC, INF, HIS; máx. 5)", max_len=5
                    ).upper()
                    if self.catalogos.existe_categoria(codigo):
                        mostrar_error(f"Ya existe una categoría con el código '{codigo}'.")
                        continue
                    break
                while True:
                    genero = pedir_texto("Género / descripción (máx. 30)", max_len=30)
                    if self.catalogos.existe_categoria_genero(genero):
                        mostrar_error(
                            f"Ya existe una categoría registrada con el género '{genero}'."
                        )
                        continue
                    break
                self.catalogos.crear_categoria(Categoria(codigo, genero))
                mostrar_exito("Categoría registrada correctamente.")
                if not confirmar("¿Deseas registrar OTRA categoría?"):
                    return
            except OperacionCancelada:
                mostrar_aviso("Operación cancelada. Regresando al menú...")
                pausar()
                return
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
                if not confirmar("¿Deseas intentar registrar otra categoría?"):
                    return

    def _catalogo_autores(self):
        primera_vez = True
        while True:
            limpiar_pantalla()
            mostrar_titulo("CATÁLOGO DE AUTORES")
            self._mostrar_autores(self.catalogos.listar_autores())
            try:
                if primera_vez:
                    if not confirmar("¿Registrar un nuevo autor?"):
                        return
                    primera_vez = False

                mostrar_ayuda_cancelar()
                nombre = pedir_texto("Nombre de pila", max_len=50)
                ap1 = pedir_texto("Primer apellido", max_len=50)
                ap2 = pedir_texto("Segundo apellido", max_len=50, obligatorio=False)
                if self.catalogos.existe_autor_nombre(nombre, ap1, ap2):
                    mostrar_error("Ya existe un autor registrado con ese mismo nombre completo.")
                else:
                    nuevo_id = self.catalogos.crear_autor(Autor(nombre, ap1, ap2))
                    mostrar_exito(f"Autor registrado con ID #{nuevo_id}.")

                if not confirmar("¿Deseas registrar OTRO autor?"):
                    return
            except OperacionCancelada:
                mostrar_aviso("Operación cancelada. Regresando al menú...")
                pausar()
                return
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
                if not confirmar("¿Deseas intentar registrar otro autor?"):
                    return

    def _catalogo_editoriales(self):
        primera_vez = True
        while True:
            limpiar_pantalla()
            mostrar_titulo("CATÁLOGO DE EDITORIALES")
            self._mostrar_editoriales(self.catalogos.listar_editoriales())
            try:
                if primera_vez:
                    if not confirmar("¿Registrar una nueva editorial?"):
                        return
                    primera_vez = False

                paises = self.catalogos.listar_paises()
                if not paises:
                    mostrar_aviso("Primero registra al menos un país.")
                    pausar()
                    return

                self._mostrar_paises(paises)
                mostrar_ayuda_cancelar()
                nombre = pedir_texto("Nombre de la editorial", max_len=50)
                while True:
                    clave_pais = pedir_texto("Clave del país", max_len=5).upper()
                    if clave_pais == "0":
                        raise OperacionCancelada()
                    if not self.catalogos.existe_pais(clave_pais):
                        mostrar_error("Esa clave de país no existe.")
                        continue
                    break

                if self.catalogos.existe_editorial_nombre(nombre, clave_pais):
                    mostrar_error(
                        f"Ya existe la editorial '{nombre}' registrada en el país '{clave_pais}'."
                    )
                else:
                    nuevo_id = self.catalogos.crear_editorial(Editorial(nombre, clave_pais))
                    mostrar_exito(f"Editorial registrada con ID #{nuevo_id}.")

                if not confirmar("¿Deseas registrar OTRA editorial?"):
                    return
            except OperacionCancelada:
                mostrar_aviso("Operación cancelada. Regresando al menú...")
                pausar()
                return
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
                if not confirmar("¿Deseas intentar registrar otra editorial?"):
                    return

    def _catalogo_proveedores(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo("CATÁLOGO DE PROVEEDORES")
            self._mostrar_proveedores(self.catalogos.listar_proveedores())
            print("1. Registrar nuevo proveedor")
            print("2. Agregar teléfono a proveedor existente")
            print("0. Volver\n")
            op = pedir_entero("Opción", minimo=0, maximo=2, permitir_cancelar=False)
            if op == 0:
                return
            if op == 1:
                self._registrar_proveedores_continuo()
            elif op == 2:
                self._agregar_telefono_proveedor_continuo()

    def _registrar_proveedores_continuo(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo("REGISTRO DE PROVEEDORES")
            self._mostrar_proveedores(self.catalogos.listar_proveedores())
            mostrar_ayuda_cancelar()
            try:
                while True:
                    rfc = pedir_texto("RFC del proveedor (máx. 13)", max_len=13).upper()
                    if self.catalogos.existe_proveedor(rfc):
                        mostrar_error(f"Ya existe un proveedor registrado con el RFC '{rfc}'.")
                        continue
                    break
                empresa = pedir_texto("Nombre de la empresa", max_len=50)
                telefonos = [pedir_texto("Teléfono principal (obligatorio, máx. 20)", max_len=20)]
                while confirmar("¿Deseas agregar OTRO teléfono para este proveedor?"):
                    tel = pedir_texto("Teléfono adicional (máx. 20)", max_len=20)
                    if tel in telefonos:
                        mostrar_aviso("Ese teléfono ya fue agregado a la lista.")
                    else:
                        telefonos.append(tel)
                self.catalogos.crear_proveedor(Proveedor(rfc, empresa, telefonos))
                mostrar_exito("Proveedor registrado correctamente.")
                if not confirmar("¿Deseas registrar OTRO proveedor?"):
                    return
            except OperacionCancelada:
                mostrar_aviso("Operación cancelada. Regresando al menú...")
                pausar()
                return
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
                if not confirmar("¿Deseas intentar registrar otro proveedor?"):
                    return

    def _agregar_telefono_proveedor_continuo(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo("AGREGAR TELÉFONO A PROVEEDOR")
            proveedores = self.catalogos.listar_proveedores()
            if not proveedores:
                mostrar_aviso("No hay proveedores registrados.")
                pausar()
                return
            self._mostrar_proveedores(proveedores)
            mostrar_ayuda_cancelar()
            try:
                while True:
                    rfc = pedir_texto("RFC del proveedor", max_len=13).upper()
                    if rfc == "0":
                        raise OperacionCancelada()
                    if not self.catalogos.existe_proveedor(rfc):
                        mostrar_error("No existe ningún proveedor con ese RFC.")
                        continue
                    break
                while True:
                    tel = pedir_texto("Nuevo teléfono (máx. 20)", max_len=20)
                    if self.catalogos.existe_telefono_proveedor(rfc, tel):
                        mostrar_error("Ese teléfono ya está registrado para este proveedor.")
                        continue
                    break
                self.catalogos.agregar_telefono_proveedor(rfc, tel)
                mostrar_exito("Teléfono agregado al proveedor.")
                if not confirmar("¿Deseas agregar OTRO teléfono a un proveedor?"):
                    return
            except OperacionCancelada:
                mostrar_aviso("Operación cancelada. Regresando al menú...")
                pausar()
                return
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
                if not confirmar("¿Deseas intentar de nuevo?"):
                    return

    def _catalogo_localizaciones(self):
        primera_vez = True
        while True:
            limpiar_pantalla()
            mostrar_titulo("CATÁLOGO DE LOCALIZACIONES")
            self._mostrar_localizaciones(self.catalogos.listar_localizaciones())
            try:
                if primera_vez:
                    if not confirmar("¿Registrar una nueva localización?"):
                        return
                    primera_vez = False

                mostrar_ayuda_cancelar()
                seccion = pedir_texto("Sección (ej. Literatura, Ingeniería)", max_len=50)
                pasillo = pedir_entero("Número de pasillo", minimo=0)
                estante = pedir_entero("Número de estante", minimo=0)
                if self.catalogos.existe_localizacion_datos(seccion, pasillo, estante):
                    mostrar_error(
                        "Ya existe una localización registrada con esa misma sección, pasillo y estante."
                    )
                else:
                    nuevo_id = self.catalogos.crear_localizacion(
                        Localizacion(estante, seccion, pasillo)
                    )
                    mostrar_exito(f"Localización registrada con ID #{nuevo_id}.")

                if not confirmar("¿Deseas registrar OTRA localización?"):
                    return
            except OperacionCancelada:
                mostrar_aviso("Operación cancelada. Regresando al menú...")
                pausar()
                return
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
                if not confirmar("¿Deseas intentar registrar otra localización?"):
                    return

    def _catalogo_usuarios(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo("CATÁLOGO DE USUARIOS")
            self._mostrar_usuarios(self.catalogos.listar_usuarios())
            print("1. Registrar nuevo usuario")
            print("2. Agregar teléfono a usuario existente")
            print("0. Volver\n")
            op = pedir_entero("Opción", minimo=0, maximo=2, permitir_cancelar=False)
            if op == 0:
                return
            if op == 1:
                self._registrar_usuarios_continuo()
            elif op == 2:
                self._agregar_telefono_usuario_continuo()

    def _registrar_usuarios_continuo(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo("REGISTRO DE USUARIOS")
            self._mostrar_usuarios(self.catalogos.listar_usuarios())
            mostrar_ayuda_cancelar()
            try:
                nombre = pedir_texto("Nombre de pila", max_len=50)
                ap1 = pedir_texto("Primer apellido", max_len=50)
                ap2 = pedir_texto("Segundo apellido", max_len=50, obligatorio=False)
                calle = pedir_texto("Calle (máx. 30)", max_len=30)
                numero = pedir_texto("Número exterior/interior (máx. 10)", max_len=10)
                colonia = pedir_texto("Colonia (máx. 50)", max_len=50)
                if self.catalogos.existe_usuario_datos(nombre, ap1, ap2, calle, numero, colonia):
                    mostrar_error("Ya existe un usuario registrado con ese mismo nombre y dirección.")
                else:
                    telefonos = [
                        pedir_texto("Teléfono principal (obligatorio, máx. 20)", max_len=20)
                    ]
                    while confirmar("¿Deseas agregar OTRO teléfono para este usuario?"):
                        tel = pedir_texto("Teléfono adicional (máx. 20)", max_len=20)
                        if tel in telefonos:
                            mostrar_aviso("Ese teléfono ya fue agregado a la lista.")
                        else:
                            telefonos.append(tel)

                    usr = Usuario(
                        nombre_pila=nombre,
                        primer_ap=ap1,
                        segundo_ap=ap2,
                        dir_calle=calle,
                        dir_numero=numero,
                        dir_colonia=colonia,
                        telefonos=telefonos,
                    )
                    nuevo_id = self.catalogos.crear_usuario(usr)
                    mostrar_exito(f"Usuario registrado con ID #{nuevo_id}.")

                if not confirmar("¿Deseas registrar OTRO usuario?"):
                    return
            except OperacionCancelada:
                mostrar_aviso("Operación cancelada. Regresando al menú...")
                pausar()
                return
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
                if not confirmar("¿Deseas intentar registrar otro usuario?"):
                    return

    def _agregar_telefono_usuario_continuo(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo("AGREGAR TELÉFONO A USUARIO")
            usuarios = self.catalogos.listar_usuarios()
            if not usuarios:
                mostrar_aviso("No hay usuarios registrados.")
                pausar()
                return
            self._mostrar_usuarios(usuarios)
            mostrar_ayuda_cancelar()
            try:
                while True:
                    id_usr = pedir_entero("ID del usuario (0 para cancelar)", minimo=0)
                    if id_usr == 0:
                        raise OperacionCancelada()
                    if not self.catalogos.existe_usuario(id_usr):
                        mostrar_error("No existe ningún usuario con ese ID.")
                        continue
                    break
                while True:
                    tel = pedir_texto("Nuevo teléfono (máx. 20)", max_len=20)
                    if self.catalogos.existe_telefono_usuario(id_usr, tel):
                        mostrar_error("Ese teléfono ya está registrado para este usuario.")
                        continue
                    break
                self.catalogos.agregar_telefono_usuario(id_usr, tel)
                mostrar_exito("Teléfono agregado al usuario.")
                if not confirmar("¿Deseas agregar OTRO teléfono a un usuario?"):
                    return
            except OperacionCancelada:
                mostrar_aviso("Operación cancelada. Regresando al menú...")
                pausar()
                return
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
                if not confirmar("¿Deseas intentar de nuevo?"):
                    return

    def _catalogo_empleados(self):
        primera_vez = True
        while True:
            limpiar_pantalla()
            mostrar_titulo("CATÁLOGO DE EMPLEADOS")
            filas = [
                (
                    e["id_empleado"],
                    f"{e['nombre_pila']} {e['primer_ap']} {e['segundo_ap'] or ''}".strip(),
                    e["nombre_user"],
                )
                for e in self.catalogos.listar_empleados()
            ]
            mostrar_tabla("Empleados", ["ID", "Nombre completo", "Usuario"], filas)

            try:
                if primera_vez:
                    if not confirmar("¿Registrar un nuevo empleado?"):
                        return
                    primera_vez = False

                mostrar_ayuda_cancelar()
                nombre = pedir_texto("Nombre de pila", max_len=50)
                ap1 = pedir_texto("Primer apellido", max_len=50)
                ap2 = pedir_texto("Segundo apellido", max_len=50, obligatorio=False)
                while True:
                    user = pedir_texto("Nombre de usuario (único, máx. 30)", max_len=30)
                    if self.catalogos.existe_empleado_user(user):
                        mostrar_error(
                            f"El nombre de usuario '{user}' ya está en uso. Elige otro."
                        )
                        continue
                    break
                pwd = pedir_texto("Contraseña (máx. 50)", max_len=50)
                nuevo_id = self.catalogos.crear_empleado(
                    Empleado(nombre, ap1, user, pwd, segundo_ap=ap2)
                )
                mostrar_exito(f"Empleado registrado con ID #{nuevo_id}.")
                if not confirmar("¿Deseas registrar OTRO empleado?"):
                    return
            except OperacionCancelada:
                mostrar_aviso("Operación cancelada. Regresando al menú...")
                pausar()
                return
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
                if not confirmar("¿Deseas intentar registrar otro empleado?"):
                    return

    # ==========================================================
    # LISTADOS RÁPIDOS DE APOYO
    # ==========================================================
    def menu_listados_apoyo(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo("LISTADOS RÁPIDOS DE APOYO")
            print("1. Obras registradas")
            print("2. Ejemplares disponibles para préstamo (resumen por obra)")
            print("3. Préstamos activos (detalle de ejemplares prestados)")
            print("4. Multas registradas")
            print("0. Volver\n")

            op = pedir_entero("Opción", minimo=0, maximo=4, permitir_cancelar=False)
            if op == 0:
                break
            elif op == 1:
                self._mostrar_obras(self.obras.listar_obras())
            elif op == 2:
                self._mostrar_resumen_disponibles(self.prestamos.listar_resumen_disponibles())
            elif op == 3:
                self._mostrar_prestamos_activos_detalle(
                    self.prestamos.listar_prestamos_activos_detalle()
                )
            elif op == 4:
                self._mostrar_multas(self.multas.listar_multas())
            pausar()

    # ==========================================================
    # HELPERS PARA MOSTRAR TABLAS
    # ==========================================================
    def _mostrar_paises(self, datos):
        mostrar_tabla("Países", ["Clave", "Nombre"], [(d["clave"], d["nombre"]) for d in datos])

    def _mostrar_tipos(self, datos):
        mostrar_tabla(
            "Tipos de Obra", ["ID", "Tipo"], [(d["id_tipo"], d["tipo_obra"]) for d in datos]
        )

    def _mostrar_categorias(self, datos):
        mostrar_tabla(
            "Categorías", ["Código", "Género"], [(d["codigo"], d["genero"]) for d in datos]
        )

    def _mostrar_autores(self, datos):
        filas = [
            (d["num_id"], f"{d['nombre_pila']} {d['primer_ap']} {d['segundo_ap'] or ''}".strip())
            for d in datos
        ]
        mostrar_tabla("Autores", ["ID", "Nombre completo"], filas)

    def _mostrar_editoriales(self, datos):
        filas = [
            (d["id_editorial"], d["nombre"], f"{d['pais']} - {d['nombre_pais']}") for d in datos
        ]
        mostrar_tabla("Editoriales", ["ID", "Nombre", "País"], filas)

    def _mostrar_proveedores(self, datos):
        filas = [(d["RFC"], d["nombre_empresa"], d["telefonos"]) for d in datos]
        mostrar_tabla("Proveedores", ["RFC", "Empresa", "Teléfonos"], filas)

    def _mostrar_localizaciones(self, datos):
        filas = [
            (d["id_localizacion"], d["seccion"], d["pasillo"], d["estante"]) for d in datos
        ]
        mostrar_tabla("Localizaciones", ["ID", "Sección", "Pasillo", "Estante"], filas)

    def _mostrar_usuarios(self, datos):
        filas = [
            (
                d["id_usuario"],
                f"{d['nombre_pila']} {d['primer_ap']} {d['segundo_ap'] or ''}".strip(),
                f"{d['dir_calle']} #{d['dir_numero']}, {d['dir_colonia']}",
                d["telefonos"],
            )
            for d in datos
        ]
        mostrar_tabla("Usuarios", ["ID", "Nombre completo", "Dirección", "Teléfonos"], filas)

    def _mostrar_obras(self, datos):
        filas = [
            (d["isbn"], d["titulo"], d["anio"], d["tipo_obra"], d["genero"], d["total_ejemplares"])
            for d in datos
        ]
        mostrar_tabla(
            "Obras", ["ISBN", "Título", "Año", "Tipo", "Categoría", "Ejemplares"], filas
        )

    def _mostrar_resumen_disponibles(self, datos):
        filas = [(d["isbn"], d["titulo"], d["disponibles"]) for d in datos]
        mostrar_tabla(
            "Obras con Ejemplares Disponibles",
            ["ISBN", "Título", "Disponibles"],
            filas,
        )

    def _mostrar_prestamos_activos_resumen(self, datos):
        filas = [
            (
                d["folio"],
                d["fecha_salida"],
                d["fecha_limite"],
                d["usuario"],
                d["pendientes"],
                d["empleado"],
            )
            for d in datos
        ]
        mostrar_tabla(
            "Préstamos Activos (Resumen)",
            ["Folio", "Salida", "Límite", "Usuario", "Pendientes", "Empleado"],
            filas,
        )

    def _mostrar_prestamos_activos_detalle(self, datos):
        filas = [
            (
                d["folio"],
                d["usuario"],
                d["fecha_salida"],
                d["fecha_limite"],
                d["obra"],
                d["titulo"],
                d["ejemplar"],
            )
            for d in datos
        ]
        mostrar_tabla(
            "Préstamos Activos (Detalle de Ejemplares)",
            ["Folio", "Usuario", "Salida", "Límite", "ISBN", "Título", "Ej. #"],
            filas,
        )

    def _mostrar_multas(self, datos):
        filas = [
            (
                d["id_multa"],
                d["prestamo"],
                d["usuario"],
                d["obra"],
                d["ejemplar"],
                d["dias_retraso"],
                f"${d['monto_dia']}",
                f"${d['total']}",
                d["estado"],
            )
            for d in datos
        ]
        mostrar_tabla(
            "Multas",
            ["Multa #", "Folio", "Usuario", "ISBN", "Ej. #", "Días", "Monto/Día", "Total", "Estado"],
            filas,
        )


if __name__ == "__main__":
    app = AplicacionBiblioteca()
    app.ejecutar()