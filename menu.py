"""Archivo principal con los menús en terminal (CLI) para Registros y Catálogos."""

from datetime import timedelta
from decimal import Decimal
from mysql.connector import Error

from conexion import ConexionDB
from modelos import (
    Autor,
    Categoria,
    Editorial,
    Empleado,
    Localizacion,
    Multa,
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
)
from utilidades import (
    confirmar,
    consola,
    limpiar_pantalla,
    mostrar_aviso,
    mostrar_error,
    mostrar_exito,
    mostrar_tabla,
    mostrar_titulo,
    pausar,
    pedir_decimal,
    pedir_entero,
    pedir_fecha,
    pedir_texto,
)


class AplicacionBiblioteca:
    """Controla el flujo de menús de terminal para los 5 registros y catálogos."""

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
            consola.print("\n[cyan]Conexión cerrada. ¡Hasta luego![/cyan]")

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
            usuario = pedir_texto("Usuario", max_len=30)
            if usuario.lower() == "salir":
                return False

            contrasena = pedir_texto("Contraseña", max_len=50)
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
            consola.print(
                "[bold]1.[/bold] Registro 1: Obra completa / Abastecer ejemplares\n"
                "[bold]2.[/bold] Registro 2: Asignar localización a ejemplares\n"
                "[bold]3.[/bold] Registro 3: Préstamo de ejemplares\n"
                "[bold]4.[/bold] Registro 4: Devolución de ejemplares\n"
                "[bold]5.[/bold] Registro 5: Multas por devolución tardía\n"
                "[bold]6.[/bold] Catálogos auxiliares (Autores, Usuarios, Proveedores, etc.)\n"
                "[bold]7.[/bold] Listados rápidos de apoyo\n"
                "[bold]0.[/bold] Cerrar sesión\n"
            )
            opcion = pedir_entero("Selecciona una opción", minimo=0, maximo=7)

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
        limpiar_pantalla()
        mostrar_titulo(
            "REGISTRO 1: OBRA COMPLETA Y ABASTECIMIENTO",
            "Registra una obra nueva o agrega más ejemplares a una existente",
        )
        consola.print(
            "[bold]1.[/bold] Registrar obra nueva (con autores, editorial, proveedor y ejemplares)\n"
            "[bold]2.[/bold] Abastecer más ejemplares a una obra ya registrada\n"
            "[bold]0.[/bold] Volver\n"
        )
        op = pedir_entero("Opción", minimo=0, maximo=2)
        if op == 0:
            return
        if op == 2:
            self._abastecer_existente()
            return

        # Validar catálogos previos obligatorios
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

        try:
            isbn = pedir_texto("ISBN (máx. 17 caracteres)", max_len=17)
            if self.obras.existe_obra(isbn):
                mostrar_aviso("Ese ISBN ya existe. Usa la opción 2 para abastecer más ejemplares.")
                pausar()
                return

            titulo = pedir_texto("Título (máx. 50 caracteres)", max_len=50)
            subtitulo = pedir_texto("Subtítulo (máx. 100 caracteres)", max_len=100, obligatorio=False)
            anio = pedir_entero("Año de publicación (4 dígitos)", minimo=1000, maximo=2100)
            paginas = pedir_entero("Número de páginas", minimo=1)

            self._mostrar_tipos(tipos)
            id_tipo = pedir_entero("ID del tipo de obra", minimo=1)

            self._mostrar_categorias(categorias)
            cod_categoria = pedir_texto("Código de categoría", max_len=5).upper()

            # Selección de autores (1 o más)
            self._mostrar_autores(autores)
            ids_autores = []
            while True:
                id_autor = pedir_entero("ID del autor a asociar", minimo=1)
                if id_autor not in ids_autores:
                    ids_autores.append(id_autor)
                if not confirmar("¿Agregar otro autor a esta obra?"):
                    break

            # Selección de editoriales (1 o más)
            self._mostrar_editoriales(editoriales)
            ids_editoriales = []
            while True:
                id_ed = pedir_entero("ID de la editorial a asociar", minimo=1)
                if id_ed not in ids_editoriales:
                    ids_editoriales.append(id_ed)
                if not confirmar("¿Agregar otra editorial a esta obra?"):
                    break

            # Abastecimiento
            self._mostrar_proveedores(proveedores)
            rfc_prov = pedir_texto("RFC del proveedor", max_len=13).upper()
            fecha_adq = pedir_fecha("Fecha de adquisición")
            cantidad = pedir_entero("Cantidad de ejemplares recibidos", minimo=1)

            id_loc = None
            if confirmar("¿Deseas asignar una localización específica desde ahora? (No = Sin asignar)"):
                self._mostrar_localizaciones(localizaciones)
                id_loc = pedir_entero("ID de localización", minimo=1)

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
        except (ValueError, Error) as e:
            mostrar_error(f"No se pudo registrar la obra: {e}")

        pausar()

    def _abastecer_existente(self):
        obras = self.obras.listar_obras()
        proveedores = self.catalogos.listar_proveedores()
        if not obras or not proveedores:
            mostrar_aviso("Necesitas al menos una obra y un proveedor registrados.")
            pausar()
            return

        self._mostrar_obras(obras)
        isbn = pedir_texto("ISBN de la obra a abastecer", max_len=17)
        if not self.obras.existe_obra(isbn):
            mostrar_error("No se encontró ninguna obra con ese ISBN.")
            pausar()
            return

        self._mostrar_proveedores(proveedores)
        rfc_prov = pedir_texto("RFC del proveedor", max_len=13).upper()
        fecha_adq = pedir_fecha("Fecha de adquisición")
        cantidad = pedir_entero("Cantidad de nuevos ejemplares", minimo=1)

        id_loc = None
        if confirmar("¿Asignar una localización específica a estos ejemplares?"):
            locs = self.catalogos.listar_localizaciones()
            self._mostrar_localizaciones(locs)
            id_loc = pedir_entero("ID de localización", minimo=1)

        try:
            inicio, fin = self.obras.abastecer_obra_existente(
                isbn, rfc_prov, fecha_adq, cantidad, id_localizacion=id_loc
            )
            mostrar_exito(f"Abastecimiento guardado. Nuevos ejemplares generados: #{inicio} al #{fin}.")
        except (ValueError, Error) as e:
            mostrar_error(f"No se pudo registrar el abastecimiento: {e}")

        pausar()

    # ==========================================================
    # REGISTRO 2: ASIGNAR LOCALIZACIÓN A EJEMPLARES
    # ==========================================================
    def flujo_asignar_localizacion(self):
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

        self._mostrar_obras(obras)
        isbn = pedir_texto("ISBN de la obra", max_len=17)
        ejemplares = self.obras.listar_ejemplares_obra(isbn)
        if not ejemplares:
            mostrar_aviso("Esa obra no existe o no tiene ejemplares registrados.")
            pausar()
            return

        filas = [
            (e["ejemplar"], e["localizacion"], e["seccion"], e["pasillo"], e["estante"], e["estado"])
            for e in ejemplares
        ]
        mostrar_tabla(
            f"Ejemplares de {isbn}",
            ["Ejemplar #", "ID Loc.", "Sección", "Pasillo", "Estante", "Estado"],
            filas,
        )

        self._mostrar_localizaciones(locs)
        id_loc = pedir_entero("Nuevo ID de localización", minimo=1)

        try:
            if confirmar("¿Aplicar esta localización a TODOS los ejemplares de esta obra?"):
                afectados = self.obras.asignar_localizacion_todos(isbn, id_loc)
                mostrar_exito(f"Se actualizaron {afectados} ejemplares a la localización #{id_loc}.")
            else:
                num_ej = pedir_entero("Número de ejemplar específico", minimo=1)
                afectados = self.obras.asignar_localizacion_ejemplar(isbn, num_ej, id_loc)
                if afectados:
                    mostrar_exito(f"Ejemplar #{num_ej} actualizado a la localización #{id_loc}.")
                else:
                    mostrar_aviso("No se encontró ese número de ejemplar para el ISBN indicado.")
        except Error as e:
            mostrar_error(f"Error al actualizar localización: {e}")

        pausar()

    # ==========================================================
    # REGISTRO 3: PRÉSTAMO DE EJEMPLARES
    # ==========================================================
    def flujo_registrar_prestamo(self):
        limpiar_pantalla()
        mostrar_titulo("REGISTRO 3: PRÉSTAMO DE EJEMPLARES")

        usuarios = self.catalogos.listar_usuarios()
        disponibles = self.prestamos.listar_ejemplares_disponibles()
        if not usuarios:
            mostrar_aviso("Registra primero al menos un usuario en Catálogos auxiliares.")
            pausar()
            return
        if not disponibles:
            mostrar_aviso("No hay ejemplares disponibles para préstamo.")
            pausar()
            return

        self._mostrar_usuarios(usuarios)
        id_usuario = pedir_entero("ID del usuario que solicita el préstamo", minimo=1)

        fecha_salida = pedir_fecha("Fecha de salida del préstamo")
        sugerida = fecha_salida + timedelta(days=7)
        consola.print(f"[dim]Sugerencia de fecha límite (+7 días): {sugerida}[/dim]")
        fecha_limite = pedir_fecha("Fecha límite de devolución", permitir_hoy=False)

        self._mostrar_disponibles(disponibles)
        seleccionados = []
        while True:
            isbn = pedir_texto("ISBN del ejemplar a prestar", max_len=17)
            num_ej = pedir_entero("Número de ejemplar", minimo=1)

            if (isbn, num_ej) in seleccionados:
                mostrar_aviso("Ese ejemplar ya fue agregado a este préstamo.")
            elif not self.prestamos.ejemplar_disponible(isbn, num_ej):
                mostrar_error("Ese ejemplar no existe o ya se encuentra prestado.")
            else:
                seleccionados.append((isbn, num_ej))
                mostrar_exito(f"Agregado: {isbn} - Ejemplar #{num_ej}")

            if not confirmar("¿Agregar otro ejemplar a este mismo préstamo?"):
                break

        if not seleccionados:
            mostrar_aviso("Préstamo cancelado (no se seleccionaron ejemplares).")
            pausar()
            return

        try:
            prestamo = Prestamo(
                fecha_salida=fecha_salida,
                fecha_limite=fecha_limite,
                empleado=self.empleado_activo.id_empleado,
                usuario=id_usuario,
                ejemplares=seleccionados,
            )
            folio = self.prestamos.registrar_prestamo(prestamo)
            mostrar_exito(
                f"Préstamo registrado correctamente con Folio #{folio} "
                f"({len(seleccionados)} ejemplar(es))."
            )
        except (ValueError, Error) as e:
            mostrar_error(f"No se pudo registrar el préstamo: {e}")

        pausar()

    # ==========================================================
    # REGISTRO 4: DEVOLUCIÓN DE EJEMPLARES
    # ==========================================================
    def flujo_registrar_devolucion(self):
        limpiar_pantalla()
        mostrar_titulo(
            "REGISTRO 4: DEVOLUCIÓN DE EJEMPLARES",
            f"Gestionado por: {self.empleado_activo.nombre_completo}",
        )

        activos = self.prestamos.listar_prestamos_activos()
        if not activos:
            mostrar_aviso("No hay préstamos activos con devoluciones pendientes.")
            pausar()
            return

        self._mostrar_prestamos_activos(activos)
        folio = pedir_entero("Folio del préstamo a devolver", minimo=1)

        pendientes = self.prestamos.listar_ejemplares_pendientes_prestamo(folio)
        if not pendientes:
            mostrar_aviso("Ese folio no existe o ya no tiene ejemplares pendientes.")
            pausar()
            return

        filas = [
            (p["obra"], p["titulo"], p["ejemplar"], p["fecha_salida"], p["fecha_limite"])
            for p in pendientes
        ]
        mostrar_tabla(
            f"Ejemplares pendientes del Préstamo #{folio}",
            ["ISBN", "Título", "Ejemplar #", "Fecha Salida", "Fecha Límite"],
            filas,
        )

        isbn = pedir_texto("ISBN del ejemplar devuelto", max_len=17)
        num_ej = pedir_entero("Número de ejemplar devuelto", minimo=1)
        fecha_dev = pedir_fecha("Fecha real de devolución")

        try:
            resultado = self.prestamos.registrar_devolucion(folio, isbn, num_ej, fecha_dev)
            if resultado["con_retraso"]:
                dias = resultado["dias_retraso"]
                mostrar_aviso(
                    f"Devolución registrada CON RETRASO de {dias} día(s) "
                    f"(fecha límite: {resultado['fecha_limite']})."
                )
                if confirmar("¿Deseas generar la multa por retraso en este momento?"):
                    self._crear_multa_directa(folio, dias)
            else:
                mostrar_exito("Devolución registrada a tiempo sin recargos.")
        except (ValueError, Error) as e:
            mostrar_error(f"No se pudo registrar la devolución: {e}")

        pausar()

    # ==========================================================
    # REGISTRO 5: MULTAS POR DEVOLUCIÓN TARDÍA
    # ==========================================================
    def flujo_multas(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo("REGISTRO 5: MULTAS POR DEVOLUCIÓN TARDÍA")
            consola.print(
                "[bold]1.[/bold] Registrar multa a partir de devoluciones tardías\n"
                "[bold]2.[/bold] Marcar una multa pendiente como 'Pagada'\n"
                "[bold]3.[/bold] Ver todas las multas registradas\n"
                "[bold]0.[/bold] Volver\n"
            )
            op = pedir_entero("Opción", minimo=0, maximo=3)

            if op == 0:
                break
            elif op == 1:
                tardias = self.multas.listar_devoluciones_tardias()
                if not tardias:
                    mostrar_aviso("No hay devoluciones tardías registradas.")
                    pausar()
                    continue

                filas = [
                    (
                        t["folio"],
                        t["usuario"],
                        t["obra"],
                        t["ejemplar"],
                        t["fecha_limite"],
                        t["fecha_devolucion"],
                        t["dias_retraso"],
                        t["multas_registradas"],
                    )
                    for t in tardias
                ]
                mostrar_tabla(
                    "Devoluciones tardías detectadas",
                    ["Folio", "Usuario", "ISBN", "Ej. #", "Límite", "Devolución", "Días", "Multas"],
                    filas,
                )
                folio = pedir_entero("Folio del préstamo a multar", minimo=1)
                dias = pedir_entero("Días de retraso", minimo=1)
                self._crear_multa_directa(folio, dias)
                pausar()
            elif op == 2:
                pendientes = self.multas.listar_multas(solo_pendientes=True)
                if not pendientes:
                    mostrar_aviso("No hay multas pendientes de pago.")
                    pausar()
                    continue

                self._mostrar_multas(pendientes)
                num_multa = pedir_entero("Número de multa", minimo=1)
                folio = pedir_entero("Folio del préstamo asociado", minimo=1)
                try:
                    afectados = self.multas.marcar_pagada(num_multa, folio)
                    if afectados:
                        mostrar_exito(f"Multa #{num_multa} marcada como 'Pagada'.")
                    else:
                        mostrar_aviso("No se encontró esa combinación de multa y préstamo.")
                except Error as e:
                    mostrar_error(f"Error al actualizar la multa: {e}")
                pausar()
            elif op == 3:
                self._mostrar_multas(self.multas.listar_multas())
                pausar()

    def _crear_multa_directa(self, folio, dias_retraso):
        monto_dia = pedir_decimal("Monto por día de retraso ($)", minimo=Decimal("0.01"))
        estado = "Pagada" if confirmar("¿El usuario liquida la multa ahora mismo?") else "Pendiente"
        try:
            multa = Multa(
                prestamo=folio,
                monto_dia=monto_dia,
                dias_retraso=dias_retraso,
                estado=estado,
            )
            num_multa = self.multas.registrar_multa(multa)
            mostrar_exito(
                f"Multa #{num_multa} registrada | {dias_retraso} día(s) x ${monto_dia} = "
                f"${multa.total} [{estado}]."
            )
        except (ValueError, Error) as e:
            mostrar_error(f"No se pudo registrar la multa: {e}")

    # ==========================================================
    # CATÁLOGOS AUXILIARES
    # ==========================================================
    def menu_catalogos(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo("CATÁLOGOS AUXILIARES")
            consola.print(
                "[bold]1.[/bold] Países\n"
                "[bold]2.[/bold] Tipos de obra\n"
                "[bold]3.[/bold] Categorías / Géneros\n"
                "[bold]4.[/bold] Autores\n"
                "[bold]5.[/bold] Editoriales\n"
                "[bold]6.[/bold] Proveedores y teléfonos\n"
                "[bold]7.[/bold] Localizaciones (Sección / Pasillo / Estante)\n"
                "[bold]8.[/bold] Usuarios y teléfonos\n"
                "[bold]9.[/bold] Empleados\n"
                "[bold]0.[/bold] Volver al menú principal\n"
            )
            op = pedir_entero("Selecciona un catálogo", minimo=0, maximo=9)

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
        limpiar_pantalla()
        mostrar_titulo("CATÁLOGO DE PAÍSES")
        self._mostrar_paises(self.catalogos.listar_paises())
        if confirmar("¿Registrar un nuevo país?"):
            try:
                clave = pedir_texto("Clave de país (ej. MEX, ESP, USA; máx. 5)", max_len=5)
                nombre = pedir_texto("Nombre del país", max_len=50)
                self.catalogos.crear_pais(Pais(clave, nombre))
                mostrar_exito("País registrado.")
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
        pausar()

    def _catalogo_tipos(self):
        limpiar_pantalla()
        mostrar_titulo("CATÁLOGO DE TIPOS DE OBRA")
        self._mostrar_tipos(self.catalogos.listar_tipos())
        if confirmar("¿Registrar un nuevo tipo de obra?"):
            try:
                nombre = pedir_texto("Tipo de obra (ej. Libro, Revista, Tesis)", max_len=50)
                nuevo_id = self.catalogos.crear_tipo(TipoObra(nombre))
                mostrar_exito(f"Tipo de obra registrado con ID #{nuevo_id}.")
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
        pausar()

    def _catalogo_categorias(self):
        limpiar_pantalla()
        mostrar_titulo("CATÁLOGO DE CATEGORÍAS")
        self._mostrar_categorias(self.catalogos.listar_categorias())
        if confirmar("¿Registrar una nueva categoría?"):
            try:
                codigo = pedir_texto("Código de categoría (ej. FIC, INF, HIS; máx. 5)", max_len=5)
                genero = pedir_texto("Género / descripción (máx. 30)", max_len=30)
                self.catalogos.crear_categoria(Categoria(codigo, genero))
                mostrar_exito("Categoría registrada.")
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
        pausar()

    def _catalogo_autores(self):
        limpiar_pantalla()
        mostrar_titulo("CATÁLOGO DE AUTORES")
        self._mostrar_autores(self.catalogos.listar_autores())
        if confirmar("¿Registrar un nuevo autor?"):
            try:
                nombre = pedir_texto("Nombre de pila", max_len=50)
                ap1 = pedir_texto("Primer apellido", max_len=50)
                ap2 = pedir_texto("Segundo apellido", max_len=50, obligatorio=False)
                nuevo_id = self.catalogos.crear_autor(Autor(nombre, ap1, ap2))
                mostrar_exito(f"Autor registrado con ID #{nuevo_id}.")
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
        pausar()

    def _catalogo_editoriales(self):
        limpiar_pantalla()
        mostrar_titulo("CATÁLOGO DE EDITORIALES")
        self._mostrar_editoriales(self.catalogos.listar_editoriales())
        if confirmar("¿Registrar una nueva editorial?"):
            paises = self.catalogos.listar_paises()
            if not paises:
                mostrar_aviso("Primero registra al menos un país.")
                pausar()
                return
            self._mostrar_paises(paises)
            try:
                nombre = pedir_texto("Nombre de la editorial", max_len=50)
                clave_pais = pedir_texto("Clave del país", max_len=5)
                nuevo_id = self.catalogos.crear_editorial(Editorial(nombre, clave_pais))
                mostrar_exito(f"Editorial registrada con ID #{nuevo_id}.")
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
        pausar()

    def _catalogo_proveedores(self):
        limpiar_pantalla()
        mostrar_titulo("CATÁLOGO DE PROVEEDORES")
        self._mostrar_proveedores(self.catalogos.listar_proveedores())
        consola.print(
            "[bold]1.[/bold] Registrar nuevo proveedor\n"
            "[bold]2.[/bold] Agregar teléfono a proveedor existente\n"
            "[bold]0.[/bold] Volver\n"
        )
        op = pedir_entero("Opción", minimo=0, maximo=2)
        if op == 1:
            try:
                rfc = pedir_texto("RFC del proveedor (máx. 13)", max_len=13)
                empresa = pedir_texto("Nombre de la empresa", max_len=50)
                telefonos = []
                while confirmar("¿Agregar un teléfono para este proveedor?"):
                    telefonos.append(pedir_texto("Teléfono (máx. 20)", max_len=20))
                self.catalogos.crear_proveedor(Proveedor(rfc, empresa, telefonos))
                mostrar_exito("Proveedor registrado.")
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
        elif op == 2:
            try:
                rfc = pedir_texto("RFC del proveedor", max_len=13)
                tel = pedir_texto("Nuevo teléfono (máx. 20)", max_len=20)
                self.catalogos.agregar_telefono_proveedor(rfc, tel)
                mostrar_exito("Teléfono agregado al proveedor.")
            except Error as e:
                mostrar_error(f"Error: {e}")
        pausar()

    def _catalogo_localizaciones(self):
        limpiar_pantalla()
        mostrar_titulo("CATÁLOGO DE LOCALIZACIONES")
        self._mostrar_localizaciones(self.catalogos.listar_localizaciones())
        if confirmar("¿Registrar una nueva localización?"):
            try:
                seccion = pedir_texto("Sección (ej. Literatura, Ingeniería)", max_len=50)
                pasillo = pedir_entero("Número de pasillo", minimo=0)
                estante = pedir_entero("Número de estante", minimo=0)
                nuevo_id = self.catalogos.crear_localizacion(
                    Localizacion(estante, seccion, pasillo)
                )
                mostrar_exito(f"Localización registrada con ID #{nuevo_id}.")
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
        pausar()

    def _catalogo_usuarios(self):
        limpiar_pantalla()
        mostrar_titulo("CATÁLOGO DE USUARIOS")
        self._mostrar_usuarios(self.catalogos.listar_usuarios())
        consola.print(
            "[bold]1.[/bold] Registrar nuevo usuario\n"
            "[bold]2.[/bold] Agregar teléfono a usuario existente\n"
            "[bold]0.[/bold] Volver\n"
        )
        op = pedir_entero("Opción", minimo=0, maximo=2)
        if op == 1:
            try:
                nombre = pedir_texto("Nombre de pila", max_len=50)
                ap1 = pedir_texto("Primer apellido", max_len=50)
                ap2 = pedir_texto("Segundo apellido", max_len=50, obligatorio=False)
                calle = pedir_texto("Calle (máx. 30)", max_len=30)
                numero = pedir_texto("Número exterior/interior (máx. 10)", max_len=10)
                colonia = pedir_texto("Colonia (máx. 50)", max_len=50)
                telefonos = []
                while confirmar("¿Agregar un teléfono para este usuario?"):
                    telefonos.append(pedir_texto("Teléfono (máx. 20)", max_len=20))

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
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
        elif op == 2:
            try:
                id_usr = pedir_entero("ID del usuario", minimo=1)
                tel = pedir_texto("Nuevo teléfono (máx. 20)", max_len=20)
                self.catalogos.agregar_telefono_usuario(id_usr, tel)
                mostrar_exito("Teléfono agregado al usuario.")
            except Error as e:
                mostrar_error(f"Error: {e}")
        pausar()

    def _catalogo_empleados(self):
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

        if confirmar("¿Registrar un nuevo empleado?"):
            try:
                nombre = pedir_texto("Nombre de pila", max_len=50)
                ap1 = pedir_texto("Primer apellido", max_len=50)
                ap2 = pedir_texto("Segundo apellido", max_len=50, obligatorio=False)
                user = pedir_texto("Nombre de usuario (único, máx. 30)", max_len=30)
                pwd = pedir_texto("Contraseña (máx. 50)", max_len=50)
                nuevo_id = self.catalogos.crear_empleado(
                    Empleado(nombre, ap1, user, pwd, segundo_ap=ap2)
                )
                mostrar_exito(f"Empleado registrado con ID #{nuevo_id}.")
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
        pausar()

    # ==========================================================
    # LISTADOS RÁPIDOS DE APOYO
    # ==========================================================
    def menu_listados_apoyo(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo("LISTADOS RÁPIDOS DE APOYO")
            consola.print(
                "[bold]1.[/bold] Obras registradas\n"
                "[bold]2.[/bold] Ejemplares disponibles para préstamo\n"
                "[bold]3.[/bold] Préstamos activos (pendientes de devolución)\n"
                "[bold]4.[/bold] Multas registradas\n"
                "[bold]0.[/bold] Volver\n"
            )
            op = pedir_entero("Opción", minimo=0, maximo=4)
            if op == 0:
                break
            elif op == 1:
                self._mostrar_obras(self.obras.listar_obras())
            elif op == 2:
                self._mostrar_disponibles(self.prestamos.listar_ejemplares_disponibles())
            elif op == 3:
                self._mostrar_prestamos_activos(self.prestamos.listar_prestamos_activos())
            elif op == 4:
                self._mostrar_multas(self.multas.listar_multas())
            pausar()

    # ==========================================================
    # HELPERS PARA MOSTRAR TABLAS
    # ==========================================================
    def _mostrar_paises(self, datos):
        mostrar_tabla("Países", ["Clave", "Nombre"], [(d["clave"], d["nombre"]) for d in datos])

    def _mostrar_tipos(self, datos):
        mostrar_tabla("Tipos de Obra", ["ID", "Tipo"], [(d["id_tipo"], d["tipo_obra"]) for d in datos])

    def _mostrar_categorias(self, datos):
        mostrar_tabla("Categorías", ["Código", "Género"], [(d["codigo"], d["genero"]) for d in datos])

    def _mostrar_autores(self, datos):
        filas = [
            (d["num_id"], f"{d['nombre_pila']} {d['primer_ap']} {d['segundo_ap'] or ''}".strip())
            for d in datos
        ]
        mostrar_tabla("Autores", ["ID", "Nombre completo"], filas)

    def _mostrar_editoriales(self, datos):
        filas = [(d["id_editorial"], d["nombre"], f"{d['pais']} - {d['nombre_pais']}") for d in datos]
        mostrar_tabla("Editoriales", ["ID", "Nombre", "País"], filas)

    def _mostrar_proveedores(self, datos):
        filas = [(d["RFC"], d["nombre_empresa"], d["telefonos"]) for d in datos]
        mostrar_tabla("Proveedores", ["RFC", "Empresa", "Teléfonos"], filas)

    def _mostrar_localizaciones(self, datos):
        filas = [(d["id_localizacion"], d["seccion"], d["pasillo"], d["estante"]) for d in datos]
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
        mostrar_tabla("Obras", ["ISBN", "Título", "Año", "Tipo", "Categoría", "Ejemplares"], filas)

    def _mostrar_disponibles(self, datos):
        filas = [
            (d["obra"], d["titulo"], d["ejemplar"], f"{d['seccion']} (P:{d['pasillo']} E:{d['estante']})")
            for d in datos
        ]
        mostrar_tabla("Ejemplares Disponibles", ["ISBN", "Título", "Ejemplar #", "Ubicación"], filas)

    def _mostrar_prestamos_activos(self, datos):
        filas = [
            (d["folio"], d["fecha_salida"], d["fecha_limite"], d["usuario"], d["pendientes"], d["empleado"])
            for d in datos
        ]
        mostrar_tabla(
            "Préstamos Activos",
            ["Folio", "Salida", "Límite", "Usuario", "Pendientes", "Empleado"],
            filas,
        )

    def _mostrar_multas(self, datos):
        filas = [
            (d["multa"], d["prestamo"], d["usuario"], d["dias_retraso"], f"${d['monto_dia']}", f"${d['total']}", d["estado"])
            for d in datos
        ]
        mostrar_tabla(
            "Multas",
            ["Multa #", "Préstamo", "Usuario", "Días", "Monto/Día", "Total", "Estado"],
            filas,
        )


if __name__ == "__main__":
    app = AplicacionBiblioteca()
    app.ejecutar() 