"""Archivo principal con los menús en terminal (CLI estándar), validaciones estrictas y navegación paso a paso."""

from datetime import date, timedelta
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
    PasoAnterior,
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
    normalizar_telefono,
    pausar,
    pedir_entero,
    pedir_fecha,
    pedir_texto,
    validar_clave_pais,
    validar_codigo_categoria,
    validar_contrasena,
    validar_isbn,
    validar_nombre_persona,
    validar_nombre_usuario,
    validar_numero_domicilio,
    validar_rfc,
    validar_solo_letras,
    validar_telefono,
    validar_texto_descriptivo,
    validar_titulo,
)


class AplicacionBiblioteca:
    """Controla el flujo de menús en terminal para operaciones, consultas y catálogos."""

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
    # UTILIDADES INTERNAS DE NAVEGACIÓN
    # ==========================================================
    def _confirmar_continuar(self, etiqueta):
        """Pregunta si desea continuar; 'atras'/'cancelar' regresan al menú."""
        try:
            return confirmar(etiqueta)
        except (OperacionCancelada, PasoAnterior):
            return False

    def _capturar_telefonos(self, entidad, telefonos_actuales=None):
        """Captura al menos un teléfono válido con retroceso paso a paso y sin duplicados."""
        telefonos = list(telefonos_actuales) if telefonos_actuales else []
        while True:
            if not telefonos:
                tel = pedir_texto(
                    f"Teléfono principal de {entidad} (10-15 dígitos, ej. 664-123-4567)",
                    max_len=20,
                    validador=validar_telefono,
                )
                telefonos.append(tel)
            try:
                agregar_otro = confirmar(f"¿Deseas agregar OTRO teléfono para {entidad}?")
            except PasoAnterior:
                quitado = telefonos.pop()
                mostrar_aviso(f"Regresando al paso anterior (se quitó el teléfono '{quitado}').")
                continue

            if not agregar_otro:
                return telefonos

            try:
                tel = pedir_texto(
                    "Teléfono adicional (10-15 dígitos)",
                    max_len=20,
                    validador=validar_telefono,
                )
            except PasoAnterior:
                mostrar_aviso("Regresando a la confirmación de teléfonos...")
                continue

            digitos_nuevos = normalizar_telefono(tel)
            if any(normalizar_telefono(t) == digitos_nuevos for t in telefonos):
                mostrar_aviso("Ese número de teléfono ya fue agregado a la lista.")
            else:
                telefonos.append(tel)

    def _capturar_lista_asociada(
        self, etiqueta_otro, etiqueta_plural, fn_seleccionar, ids_actuales=None
    ):
        """Captura 1 o más IDs (autores o editoriales) permitiendo retroceder paso a paso."""
        ids = list(ids_actuales) if ids_actuales else []
        if ids:
            print(f"\n{etiqueta_plural.capitalize()} seleccionados actualmente: {ids}")

        while True:
            if not ids:
                nuevo_id = fn_seleccionar()
                ids.append(nuevo_id)
            try:
                agregar_otro = confirmar(f"¿Deseas agregar {etiqueta_otro} a esta obra?")
            except PasoAnterior:
                quitado = ids.pop()
                mostrar_aviso(
                    f"Regresando al paso anterior (se quitó el ID #{quitado} de {etiqueta_plural})."
                )
                continue

            if not agregar_otro:
                return ids

            try:
                nuevo_id = fn_seleccionar()
            except PasoAnterior:
                mostrar_aviso(f"Regresando a la confirmación de {etiqueta_plural}...")
                continue

            if nuevo_id in ids:
                mostrar_aviso("Ese registro ya fue agregado a esta obra.")
            else:
                ids.append(nuevo_id)

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
            usuario = pedir_texto(
                "Usuario", max_len=30, permitir_cancelar=False, permitir_atras=False
            )
            if usuario.lower() in ("salir", "cancelar"):
                return False

            try:
                contrasena = pedir_texto(
                    "Contraseña (escribe 'atras' para cambiar de usuario)", max_len=50
                )
            except (OperacionCancelada, PasoAnterior):
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
                "MENÚ PRINCIPAL - SISTEMA BIBLIOTECARIO",
                f"Empleado en sesión: {self.empleado_activo.nombre_completo} (@{self.empleado_activo.nombre_user})",
            )
            print("1. Obras y abastecimiento")
            print("2. Asignar localización a ejemplares")
            print("3. Préstamos de ejemplares")
            print("4. Devoluciones de ejemplares")
            print("5. Multas por devolución tardía")
            print("6. Catálogos auxiliares (Autores, Usuarios, Proveedores, etc.)")
            print("7. Listados rápidos de apoyo")
            print("0. Cerrar sesión\n")

            opcion = pedir_entero(
                "Selecciona una opción",
                minimo=0,
                maximo=7,
                permitir_cancelar=False,
                permitir_atras=False,
            )

            if opcion == 1:
                self.flujo_obras()
            elif opcion == 2:
                self.flujo_asignar_localizacion()
            elif opcion == 3:
                self.flujo_prestamos()
            elif opcion == 4:
                self.flujo_devoluciones()
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
    # HELPERS DE SELECCIÓN O ALTA AL VUELO (CON VALIDACIONES Y RETROCESO)
    # ==========================================================
    def _crear_pais_rapido(self):
        print("\n--- Nuevo País (escribe 'atras' para volver a la lista) ---")
        clave = None
        nombre = None
        paso = 0

        while paso < 2:
            try:
                if paso == 0:
                    val = pedir_texto(
                        "Clave de país (2-5 letras, ej. MEX, ESP, USA)",
                        max_len=5,
                        validador=validar_clave_pais,
                    ).upper()
                    if self.catalogos.existe_pais(val):
                        mostrar_error(f"Ya existe un país registrado con la clave '{val}'.")
                        continue
                    clave = val
                    paso = 1
                elif paso == 1:
                    val = pedir_texto(
                        "Nombre del país",
                        max_len=50,
                        validador=validar_solo_letras,
                    )
                    if self.catalogos.existe_pais_nombre(val):
                        mostrar_error(f"Ya existe un país registrado con el nombre '{val}'.")
                        continue
                    nombre = val
                    paso = 2
            except PasoAnterior:
                if paso == 0:
                    mostrar_aviso("Regresando a la selección de países...")
                    return None
                paso -= 1
                mostrar_aviso("Regresando al campo anterior...")

        try:
            self.catalogos.crear_pais(Pais(clave, nombre))
            mostrar_exito(f"País '{nombre}' ({clave}) guardado en la base de datos.")
            return clave
        except (ValueError, Error) as e:
            mostrar_error(f"Error al guardar país: {e}")
            return None

    def _seleccionar_o_crear_pais(self):
        while True:
            paises = self.catalogos.listar_paises()
            if not paises:
                mostrar_aviso("No hay países registrados. Registra uno nuevo para la editorial:")
                clave = self._crear_pais_rapido()
                if clave is not None:
                    return clave
                raise PasoAnterior()

            self._mostrar_paises(paises)
            entrada = pedir_texto(
                "Clave del país (escribe 'nuevo' para registrar uno, o 'atras' para volver)",
                max_len=20,
            )
            if entrada.lower() in ("nuevo", "nueva"):
                clave = self._crear_pais_rapido()
                if clave is not None:
                    return clave
                continue

            clave = entrada.upper()
            if not self.catalogos.existe_pais(clave):
                mostrar_error("Esa clave de país no existe. Elige una de la tabla o escribe 'nuevo'.")
                continue
            return clave

    def _crear_tipo_rapido(self):
        print("\n--- Nuevo Tipo de Obra (escribe 'atras' para volver a la lista) ---")
        while True:
            try:
                nombre = pedir_texto(
                    "Tipo de obra (ej. Libro, Revista, Tesis)",
                    max_len=50,
                    validador=validar_solo_letras,
                )
            except PasoAnterior:
                mostrar_aviso("Regresando a la selección de tipos de obra...")
                return None

            if self.catalogos.existe_tipo_nombre(nombre):
                mostrar_error(f"Ya existe un tipo de obra registrado como '{nombre}'.")
                continue

            try:
                nuevo_id = self.catalogos.crear_tipo(TipoObra(nombre))
                mostrar_exito(f"Tipo de obra '{nombre}' guardado con ID #{nuevo_id}.")
                return nuevo_id
            except (ValueError, Error) as e:
                mostrar_error(f"Error al guardar tipo de obra: {e}")
                return None

    def _seleccionar_o_crear_tipo(self):
        while True:
            tipos = self.catalogos.listar_tipos()
            if not tipos:
                mostrar_aviso("No hay tipos de obra registrados. Registra uno nuevo:")
                nuevo_id = self._crear_tipo_rapido()
                if nuevo_id is not None:
                    return nuevo_id
                raise PasoAnterior()

            self._mostrar_tipos(tipos)
            entrada = pedir_texto(
                "ID del tipo de obra (escribe 'nuevo' para registrar uno, o 'atras' para volver)",
                max_len=20,
            )
            if entrada.lower() in ("nuevo", "nueva"):
                nuevo_id = self._crear_tipo_rapido()
                if nuevo_id is not None:
                    return nuevo_id
                continue

            try:
                id_tipo = int(entrada)
            except ValueError:
                mostrar_error("Ingresa un ID numérico válido o escribe 'nuevo'.")
                continue

            if id_tipo <= 0 or not self.catalogos.existe_tipo(id_tipo):
                mostrar_error("Ese ID de tipo de obra no existe.")
                continue
            return id_tipo

    def _crear_categoria_rapida(self):
        print("\n--- Nueva Categoría / Género (escribe 'atras' para volver a la lista) ---")
        codigo = None
        genero = None
        paso = 0

        while paso < 2:
            try:
                if paso == 0:
                    val = pedir_texto(
                        "Código de categoría (2-5 letras/números, ej. 005, FIC)",
                        max_len=5,
                        validador=validar_codigo_categoria,
                    ).upper()
                    if self.catalogos.existe_categoria(val):
                        mostrar_error(f"Ya existe una categoría con el código '{val}'.")
                        continue
                    codigo = val
                    paso = 1
                elif paso == 1:
                    val = pedir_texto(
                        "Género / descripción (máx. 30)",
                        max_len=30,
                        validador=validar_solo_letras,
                    )
                    if self.catalogos.existe_categoria_genero(val):
                        mostrar_error(f"Ya existe una categoría registrada con el género '{val}'.")
                        continue
                    genero = val
                    paso = 2
            except PasoAnterior:
                if paso == 0:
                    mostrar_aviso("Regresando a la selección de categorías...")
                    return None
                paso -= 1
                mostrar_aviso("Regresando al campo anterior...")

        try:
            self.catalogos.crear_categoria(Categoria(codigo, genero))
            mostrar_exito(f"Categoría '{genero}' ({codigo}) guardada en la base de datos.")
            return codigo
        except (ValueError, Error) as e:
            mostrar_error(f"Error al guardar categoría: {e}")
            return None

    def _seleccionar_o_crear_categoria(self):
        while True:
            categorias = self.catalogos.listar_categorias()
            if not categorias:
                mostrar_aviso("No hay categorías registradas. Registra una nueva:")
                cod = self._crear_categoria_rapida()
                if cod is not None:
                    return cod
                raise PasoAnterior()

            self._mostrar_categorias(categorias)
            entrada = pedir_texto(
                "Código de categoría (escribe 'nuevo' para registrar una, o 'atras' para volver)",
                max_len=20,
            )
            if entrada.lower() in ("nuevo", "nueva"):
                cod = self._crear_categoria_rapida()
                if cod is not None:
                    return cod
                continue

            cod = entrada.upper()
            if not self.catalogos.existe_categoria(cod):
                mostrar_error("Ese código de categoría no existe. Elige uno de la tabla o escribe 'nuevo'.")
                continue
            return cod

    def _crear_autor_rapido(self):
        print("\n--- Nuevo Autor (escribe 'atras' para volver al paso anterior) ---")
        nombre = None
        ap1 = None
        ap2 = None
        paso = 0

        while paso < 3:
            try:
                if paso == 0:
                    nombre = pedir_texto(
                        "Nombre de pila del autor",
                        max_len=50,
                        validador=validar_nombre_persona,
                    )
                    paso = 1
                elif paso == 1:
                    ap1 = pedir_texto(
                        "Primer apellido del autor",
                        max_len=50,
                        validador=validar_nombre_persona,
                    )
                    paso = 2
                elif paso == 2:
                    ap2 = pedir_texto(
                        "Segundo apellido del autor",
                        max_len=50,
                        obligatorio=False,
                        validador=validar_nombre_persona,
                    )
                    if self.catalogos.existe_autor_nombre(nombre, ap1, ap2):
                        mostrar_error("Ya existe un autor registrado con ese mismo nombre completo.")
                        paso = 0
                        continue
                    paso = 3
            except PasoAnterior:
                if paso == 0:
                    mostrar_aviso("Regresando a la selección de autores...")
                    return None
                paso -= 1
                mostrar_aviso("Regresando al campo anterior...")

        try:
            autor = Autor(nombre, ap1, ap2)
            nuevo_id = self.catalogos.crear_autor(autor)
            mostrar_exito(f"Autor '{autor.nombre_completo}' guardado con ID #{nuevo_id}.")
            return nuevo_id
        except (ValueError, Error) as e:
            mostrar_error(f"Error al guardar autor: {e}")
            return None

    def _seleccionar_o_crear_autor(self):
        while True:
            autores = self.catalogos.listar_autores()
            if not autores:
                mostrar_aviso("No hay autores registrados. Registra un autor nuevo:")
                nuevo_id = self._crear_autor_rapido()
                if nuevo_id is not None:
                    return nuevo_id
                raise PasoAnterior()

            self._mostrar_autores(autores)
            entrada = pedir_texto(
                "ID del autor a asociar (escribe 'nuevo' para registrar uno, o 'atras' para volver)",
                max_len=20,
            )
            if entrada.lower() in ("nuevo", "nueva"):
                nuevo_id = self._crear_autor_rapido()
                if nuevo_id is not None:
                    return nuevo_id
                continue

            try:
                id_autor = int(entrada)
            except ValueError:
                mostrar_error("Ingresa un ID numérico válido o escribe 'nuevo'.")
                continue

            if id_autor <= 0 or not self.catalogos.existe_autor(id_autor):
                mostrar_error("Ese ID de autor no existe.")
                continue
            return id_autor

    def _crear_editorial_rapida(self):
        print("\n--- Nueva Editorial (escribe 'atras' para volver al paso anterior) ---")
        nombre = None
        clave_pais = None
        paso = 0

        while paso < 2:
            try:
                if paso == 0:
                    nombre = pedir_texto(
                        "Nombre de la editorial",
                        max_len=50,
                        validador=validar_texto_descriptivo,
                    )
                    paso = 1
                elif paso == 1:
                    clave_pais = self._seleccionar_o_crear_pais()
                    if self.catalogos.existe_editorial_nombre(nombre, clave_pais):
                        mostrar_error(
                            f"Ya existe la editorial '{nombre}' registrada en el país '{clave_pais}'."
                        )
                        paso = 0
                        continue
                    paso = 2
            except PasoAnterior:
                if paso == 0:
                    mostrar_aviso("Regresando a la selección de editoriales...")
                    return None
                paso -= 1
                mostrar_aviso("Regresando al campo anterior...")

        try:
            nuevo_id = self.catalogos.crear_editorial(Editorial(nombre, clave_pais))
            mostrar_exito(f"Editorial '{nombre}' ({clave_pais}) guardada con ID #{nuevo_id}.")
            return nuevo_id
        except (ValueError, Error) as e:
            mostrar_error(f"Error al guardar editorial: {e}")
            return None

    def _seleccionar_o_crear_editorial(self):
        while True:
            editoriales = self.catalogos.listar_editoriales()
            if not editoriales:
                mostrar_aviso("No hay editoriales registradas. Registra una editorial nueva:")
                nuevo_id = self._crear_editorial_rapida()
                if nuevo_id is not None:
                    return nuevo_id
                raise PasoAnterior()

            self._mostrar_editoriales(editoriales)
            entrada = pedir_texto(
                "ID de la editorial a asociar (escribe 'nuevo' para registrar una, o 'atras' para volver)",
                max_len=20,
            )
            if entrada.lower() in ("nuevo", "nueva"):
                nuevo_id = self._crear_editorial_rapida()
                if nuevo_id is not None:
                    return nuevo_id
                continue

            try:
                id_ed = int(entrada)
            except ValueError:
                mostrar_error("Ingresa un ID numérico válido o escribe 'nuevo'.")
                continue

            if id_ed <= 0 or not self.catalogos.existe_editorial(id_ed):
                mostrar_error("Ese ID de editorial no existe.")
                continue
            return id_ed

    def _crear_proveedor_rapido(self):
        print("\n--- Nuevo Proveedor (escribe 'atras' para volver al paso anterior) ---")
        rfc = None
        empresa = None
        telefonos = []
        paso = 0

        while paso < 3:
            try:
                if paso == 0:
                    val = pedir_texto(
                        "RFC del proveedor (12-13 caracteres, ej. DIS890412AB1)",
                        max_len=13,
                        validador=validar_rfc,
                    ).upper()
                    if self.catalogos.existe_proveedor(val):
                        mostrar_error(f"Ya existe un proveedor registrado con el RFC '{val}'.")
                        continue
                    rfc = val
                    paso = 1
                elif paso == 1:
                    empresa = pedir_texto(
                        "Nombre de la empresa",
                        max_len=50,
                        validador=validar_texto_descriptivo,
                    )
                    paso = 2
                elif paso == 2:
                    telefonos = self._capturar_telefonos("este proveedor", telefonos)
                    paso = 3
            except PasoAnterior:
                if paso == 0:
                    mostrar_aviso("Regresando a la selección de proveedores...")
                    return None
                paso -= 1
                mostrar_aviso("Regresando al campo anterior...")

        try:
            self.catalogos.crear_proveedor(Proveedor(rfc, empresa, telefonos))
            mostrar_exito(f"Proveedor '{empresa}' ({rfc}) guardado en la base de datos.")
            return rfc
        except (ValueError, Error) as e:
            mostrar_error(f"Error al guardar proveedor: {e}")
            return None

    def _seleccionar_o_crear_proveedor(self):
        while True:
            proveedores = self.catalogos.listar_proveedores()
            if not proveedores:
                mostrar_aviso("No hay proveedores registrados. Registra un proveedor nuevo:")
                rfc = self._crear_proveedor_rapido()
                if rfc is not None:
                    return rfc
                raise PasoAnterior()

            self._mostrar_proveedores(proveedores)
            entrada = pedir_texto(
                "RFC del proveedor (escribe 'nuevo' para registrar uno, o 'atras' para volver)",
                max_len=20,
            )
            if entrada.lower() in ("nuevo", "nueva"):
                rfc = self._crear_proveedor_rapido()
                if rfc is not None:
                    return rfc
                continue

            rfc = entrada.upper()
            if not self.catalogos.existe_proveedor(rfc):
                mostrar_error("Ese RFC de proveedor no existe. Elige uno de la tabla o escribe 'nuevo'.")
                continue
            return rfc

    def _crear_localizacion_rapida(self):
        print("\n--- Nueva Localización (escribe 'atras' para volver al paso anterior) ---")
        seccion = None
        pasillo = None
        estante = None
        paso = 0

        while paso < 3:
            try:
                if paso == 0:
                    seccion = pedir_texto(
                        "Sección (ej. Literatura, Ingeniería)",
                        max_len=50,
                        validador=validar_texto_descriptivo,
                    )
                    paso = 1
                elif paso == 1:
                    pasillo = pedir_entero("Número de pasillo (1-500)", minimo=1, maximo=500)
                    paso = 2
                elif paso == 2:
                    estante = pedir_entero("Número de estante (1-500)", minimo=1, maximo=500)
                    if self.catalogos.existe_localizacion_datos(seccion, pasillo, estante):
                        mostrar_error(
                            "Ya existe una localización con esa misma sección, pasillo y estante."
                        )
                        paso = 0
                        continue
                    paso = 3
            except PasoAnterior:
                if paso == 0:
                    mostrar_aviso("Regresando a la selección de localizaciones...")
                    return None
                paso -= 1
                mostrar_aviso("Regresando al campo anterior...")

        try:
            nuevo_id = self.catalogos.crear_localizacion(Localizacion(estante, seccion, pasillo))
            mostrar_exito(
                f"Localización '{seccion}' (Pasillo {pasillo}, Estante {estante}) "
                f"guardada con ID #{nuevo_id}."
            )
            return nuevo_id
        except (ValueError, Error) as e:
            mostrar_error(f"Error al guardar localización: {e}")
            return None

    def _seleccionar_o_crear_localizacion(self, permitir_sin_asignar=False):
        while True:
            locs = self.catalogos.listar_localizaciones()
            if not locs:
                mostrar_aviso("No hay localizaciones registradas. Registra una nueva:")
                nuevo_id = self._crear_localizacion_rapida()
                if nuevo_id is not None:
                    return nuevo_id
                raise PasoAnterior()

            self._mostrar_localizaciones(locs)
            if permitir_sin_asignar:
                etiqueta = "ID de localización (0 = Sin asignar, 'nuevo' = registrar, 'atras' = volver)"
            else:
                etiqueta = "ID de localización (escribe 'nuevo' para registrar una, o 'atras' para volver)"

            entrada = pedir_texto(etiqueta, max_len=20)
            if entrada.lower() in ("nuevo", "nueva"):
                nuevo_id = self._crear_localizacion_rapida()
                if nuevo_id is not None:
                    return nuevo_id
                continue
            if entrada == "0" and permitir_sin_asignar:
                return None

            try:
                id_loc = int(entrada)
            except ValueError:
                mostrar_error("Ingresa un ID numérico válido o escribe 'nuevo'.")
                continue

            if id_loc <= 0 or not self.catalogos.existe_localizacion(id_loc):
                mostrar_error("Ese ID de localización no existe.")
                continue
            return id_loc

    def _crear_usuario_rapido(self):
        print("\n--- Nuevo Usuario (escribe 'atras' para volver al paso anterior) ---")
        nombre = None
        ap1 = None
        ap2 = None
        calle = None
        numero = None
        colonia = None
        telefonos = []
        paso = 0

        while paso < 7:
            try:
                if paso == 0:
                    nombre = pedir_texto(
                        "Nombre de pila",
                        max_len=50,
                        validador=validar_nombre_persona,
                    )
                    paso = 1
                elif paso == 1:
                    ap1 = pedir_texto(
                        "Primer apellido",
                        max_len=50,
                        validador=validar_nombre_persona,
                    )
                    paso = 2
                elif paso == 2:
                    ap2 = pedir_texto(
                        "Segundo apellido",
                        max_len=50,
                        obligatorio=False,
                        validador=validar_nombre_persona,
                    )
                    paso = 3
                elif paso == 3:
                    calle = pedir_texto(
                        "Calle (máx. 30)",
                        max_len=30,
                        validador=validar_texto_descriptivo,
                    )
                    paso = 4
                elif paso == 4:
                    numero = pedir_texto(
                        "Número exterior/interior (ej. 412, 10-B o S/N)",
                        max_len=10,
                        validador=validar_numero_domicilio,
                    )
                    paso = 5
                elif paso == 5:
                    colonia = pedir_texto(
                        "Colonia (máx. 50)",
                        max_len=50,
                        validador=validar_texto_descriptivo,
                    )
                    if self.catalogos.existe_usuario_datos(
                        nombre, ap1, ap2, calle, numero, colonia
                    ):
                        mostrar_error(
                            "Ya existe un usuario registrado con ese mismo nombre y dirección."
                        )
                        paso = 0
                        continue
                    paso = 6
                elif paso == 6:
                    telefonos = self._capturar_telefonos("este usuario", telefonos)
                    paso = 7
            except PasoAnterior:
                if paso == 0:
                    mostrar_aviso("Regresando a la selección de usuarios...")
                    return None
                paso -= 1
                mostrar_aviso("Regresando al campo anterior...")

        try:
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
            mostrar_exito(
                f"Usuario '{usr.nombre_completo}' guardado en la base de datos con ID #{nuevo_id}."
            )
            return nuevo_id
        except (ValueError, Error) as e:
            mostrar_error(f"Error al guardar usuario: {e}")
            return None

    def _seleccionar_o_crear_usuario(self):
        while True:
            usuarios = self.catalogos.listar_usuarios()
            if not usuarios:
                mostrar_aviso(
                    "No hay usuarios registrados. Registra un usuario nuevo para el préstamo:"
                )
                nuevo_id = self._crear_usuario_rapido()
                if nuevo_id is not None:
                    return nuevo_id
                raise PasoAnterior()

            self._mostrar_usuarios(usuarios)
            entrada = pedir_texto(
                "ID del usuario (escribe 'nuevo' para registrar uno, o 'atras' para volver)",
                max_len=20,
            )
            if entrada.lower() in ("nuevo", "nueva"):
                nuevo_id = self._crear_usuario_rapido()
                if nuevo_id is not None:
                    return nuevo_id
                continue

            try:
                id_usuario = int(entrada)
            except ValueError:
                mostrar_error("Ingresa un ID numérico válido o escribe 'nuevo'.")
                continue

            if id_usuario <= 0 or not self.catalogos.existe_usuario(id_usuario):
                mostrar_error(
                    "No existe ningún usuario con ese ID. Elige uno de la tabla o escribe 'nuevo'."
                )
                continue
            return id_usuario

    # ==========================================================
    # OPCIÓN 1: OBRAS Y ABASTECIMIENTO (+ CONSULTA COMPLETA DE OBRA)
    # ==========================================================
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
            print("0. Volver\n")

            op = pedir_entero(
                "Opción", minimo=0, maximo=3, permitir_cancelar=False, permitir_atras=False
            )
            if op == 0:
                return
            if op == 1:
                self._registrar_obra_nueva()
            elif op == 2:
                self._abastecer_existente()
            elif op == 3:
                self._consultar_obra_completa()

    def _consultar_obra_completa(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo("CONSULTA DE INFORMACIÓN COMPLETA DE UNA OBRA")

            obras = self.obras.listar_obras()
            if not obras:
                mostrar_aviso("No hay obras registradas en la base de datos.")
                pausar()
                return

            self._mostrar_obras(obras)
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
                if not self._confirmar_continuar("¿Deseas consultar OTRA obra?"):
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
                            id_tipo = self._seleccionar_o_crear_tipo()
                            paso = 6
                        elif paso == 6:
                            cod_categoria = self._seleccionar_o_crear_categoria()
                            paso = 7
                        elif paso == 7:
                            ids_autores = self._capturar_lista_asociada(
                                "OTRO autor",
                                "autores",
                                self._seleccionar_o_crear_autor,
                                ids_autores,
                            )
                            paso = 8
                        elif paso == 8:
                            ids_editoriales = self._capturar_lista_asociada(
                                "OTRA editorial",
                                "editoriales",
                                self._seleccionar_o_crear_editorial,
                                ids_editoriales,
                            )
                            paso = 9
                        elif paso == 9:
                            rfc_prov = self._seleccionar_o_crear_proveedor()
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
                                id_loc = self._seleccionar_o_crear_localizacion(
                                    permitir_sin_asignar=False
                                )
                                paso = 13
                            else:
                                asignar = confirmar(
                                    "¿Deseas asignar una localización específica desde ahora? (No = Sin asignar)"
                                )
                                if asignar:
                                    try:
                                        id_loc = self._seleccionar_o_crear_localizacion(
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
                if not self._confirmar_continuar("¿Deseas registrar OTRA obra nueva?"):
                    return
            except OperacionCancelada:
                mostrar_aviso("Operación cancelada. Regresando al menú...")
                pausar()
                return
            except (ValueError, Error) as e:
                mostrar_error(f"No se pudo registrar la obra: {e}")
                if not self._confirmar_continuar("¿Deseas intentar registrar otra obra?"):
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
                            self._mostrar_obras(obras)
                            val = pedir_texto("ISBN de la obra a abastecer", max_len=17)
                            info = self.obras.obtener_obra(val)
                            if not info:
                                mostrar_error("No se encontró ninguna obra con ese ISBN.")
                                continue
                            isbn = val
                            obra_bd = info
                            paso = 1
                        elif paso == 1:
                            rfc_prov = self._seleccionar_o_crear_proveedor()
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
                                id_loc = self._seleccionar_o_crear_localizacion(
                                    permitir_sin_asignar=False
                                )
                                paso = 5
                            else:
                                asignar = confirmar(
                                    "¿Asignar una localización específica a estos ejemplares?"
                                )
                                if asignar:
                                    try:
                                        id_loc = self._seleccionar_o_crear_localizacion(
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
                if not self._confirmar_continuar("¿Deseas registrar OTRO abastecimiento?"):
                    return
            except OperacionCancelada:
                mostrar_aviso("Operación cancelada. Regresando al menú...")
                pausar()
                return
            except (ValueError, Error) as e:
                mostrar_error(f"No se pudo registrar el abastecimiento: {e}")
                if not self._confirmar_continuar("¿Deseas intentar otro abastecimiento?"):
                    return

    # ==========================================================
    # OPCIÓN 2: ASIGNAR LOCALIZACIÓN A EJEMPLARES
    # ==========================================================
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
                            self._mostrar_obras(obras)
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
                            id_loc = self._seleccionar_o_crear_localizacion(
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

                if not self._confirmar_continuar(
                    "¿Deseas asignar localización a OTRA obra o ejemplar?"
                ):
                    return
            except OperacionCancelada:
                mostrar_aviso("Operación cancelada. Regresando al menú...")
                pausar()
                return
            except Error as e:
                mostrar_error(f"Error al actualizar localización: {e}")
                if not self._confirmar_continuar("¿Deseas intentar otra asignación?"):
                    return

    # ==========================================================
    # OPCIÓN 3: PRÉSTAMOS DE EJEMPLARES (+ DETALLE Y CONSULTA POR FECHA)
    # ==========================================================
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

                if not self._confirmar_continuar("¿Deseas consultar OTRO préstamo?"):
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

                if not self._confirmar_continuar("¿Deseas consultar préstamos de OTRA fecha?"):
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
                            id_usuario = self._seleccionar_o_crear_usuario()
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
                            self._mostrar_resumen_disponibles(resumen_disp)
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
                if not self._confirmar_continuar("¿Deseas registrar OTRO préstamo?"):
                    return
            except OperacionCancelada:
                mostrar_aviso("Préstamo cancelado. Regresando al menú...")
                pausar()
                return
            except (ValueError, Error) as e:
                mostrar_error(f"No se pudo registrar el préstamo: {e}")
                if not self._confirmar_continuar("¿Deseas intentar registrar otro préstamo?"):
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

    # ==========================================================
    # OPCIÓN 4: DEVOLUCIONES DE EJEMPLARES (+ FECHAS Y FILTRO DE 3 OPCIONES)
    # ==========================================================
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

            fechas = self.prestamos.listar_fechas_devoluciones()
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

                registros = self.prestamos.consultar_devoluciones_por_fecha(
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

                if not self._confirmar_continuar("¿Deseas consultar devoluciones de OTRA fecha?"):
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

            activos = self.prestamos.listar_prestamos_activos_resumen()
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
                            self._mostrar_prestamos_activos_resumen(activos)
                            val_folio = pedir_entero("Folio del préstamo a devolver", minimo=1)
                            pends = self.prestamos.listar_ejemplares_pendientes_prestamo(val_folio)
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

                resultado = self.prestamos.registrar_devolucion(
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

                if not self.prestamos.listar_prestamos_activos_resumen():
                    mostrar_aviso("Ya no quedan más préstamos activos pendientes.")
                    pausar()
                    return
                if not self._confirmar_continuar("¿Deseas registrar OTRA devolución?"):
                    return
            except OperacionCancelada:
                mostrar_aviso("Operación cancelada. Regresando al menú...")
                pausar()
                return
            except (ValueError, Error) as e:
                mostrar_error(f"No se pudo registrar la devolución: {e}")
                if not self._confirmar_continuar("¿Deseas intentar otra devolución?"):
                    return

    # ==========================================================
    # OPCIÓN 5: MULTAS POR DEVOLUCIÓN TARDÍA (+ FICHA COMPLETA DE MULTA)
    # ==========================================================
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

            self._mostrar_multas(multas)
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
                if not self._confirmar_continuar("¿Deseas consultar el detalle de OTRA multa?"):
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

            self._mostrar_multas(pendientes)
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
                if not self._confirmar_continuar(
                    "¿Deseas marcar OTRA multa pendiente como 'Pagada'?"
                ):
                    return
            except (OperacionCancelada, PasoAnterior):
                mostrar_aviso("Regresando al menú de multas...")
                return
            except Error as e:
                mostrar_error(f"Error al actualizar la multa: {e}")
                if not self._confirmar_continuar("¿Deseas intentar con otra multa?"):
                    return

    # ==========================================================
    # OPCIÓN 6: CATÁLOGOS AUXILIARES
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
                "Selecciona un catálogo",
                minimo=0,
                maximo=9,
                permitir_cancelar=False,
                permitir_atras=False,
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
                clave = None
                nombre = None
                paso = 0

                while paso < 2:
                    try:
                        if paso == 0:
                            val = pedir_texto(
                                "Clave de país (2-5 letras, ej. MEX, ESP, USA)",
                                max_len=5,
                                validador=validar_clave_pais,
                            ).upper()
                            if self.catalogos.existe_pais(val):
                                mostrar_error(f"Ya existe un país registrado con la clave '{val}'.")
                                continue
                            clave = val
                            paso = 1
                        elif paso == 1:
                            val = pedir_texto(
                                "Nombre del país",
                                max_len=50,
                                validador=validar_solo_letras,
                            )
                            if self.catalogos.existe_pais_nombre(val):
                                mostrar_error(
                                    f"Ya existe un país registrado con el nombre '{val}'."
                                )
                                continue
                            nombre = val
                            paso = 2
                    except PasoAnterior:
                        if paso == 0:
                            mostrar_aviso("Regresando al menú de catálogos...")
                            return
                        paso -= 1
                        mostrar_aviso("Regresando al campo anterior...")

                self.catalogos.crear_pais(Pais(clave, nombre))
                mostrar_exito("País registrado correctamente.")
                if not self._confirmar_continuar("¿Deseas registrar OTRO país?"):
                    return
            except (OperacionCancelada, PasoAnterior):
                mostrar_aviso("Regresando al menú de catálogos...")
                return
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
                if not self._confirmar_continuar("¿Deseas intentar registrar otro país?"):
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
                    nombre = pedir_texto(
                        "Tipo de obra (ej. Libro, Revista, Tesis)",
                        max_len=50,
                        validador=validar_solo_letras,
                    )
                    if self.catalogos.existe_tipo_nombre(nombre):
                        mostrar_error(f"Ya existe un tipo de obra registrado como '{nombre}'.")
                        continue
                    break
                nuevo_id = self.catalogos.crear_tipo(TipoObra(nombre))
                mostrar_exito(f"Tipo de obra registrado con ID #{nuevo_id}.")
                if not self._confirmar_continuar("¿Deseas registrar OTRO tipo de obra?"):
                    return
            except (OperacionCancelada, PasoAnterior):
                mostrar_aviso("Regresando al menú de catálogos...")
                return
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
                if not self._confirmar_continuar("¿Deseas intentar registrar otro tipo de obra?"):
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
                codigo = None
                genero = None
                paso = 0

                while paso < 2:
                    try:
                        if paso == 0:
                            val = pedir_texto(
                                "Código de categoría (2-5 letras/números, ej. 005, FIC)",
                                max_len=5,
                                validador=validar_codigo_categoria,
                            ).upper()
                            if self.catalogos.existe_categoria(val):
                                mostrar_error(f"Ya existe una categoría con el código '{val}'.")
                                continue
                            codigo = val
                            paso = 1
                        elif paso == 1:
                            val = pedir_texto(
                                "Género / descripción (máx. 30)",
                                max_len=30,
                                validador=validar_solo_letras,
                            )
                            if self.catalogos.existe_categoria_genero(val):
                                mostrar_error(
                                    f"Ya existe una categoría registrada con el género '{val}'."
                                )
                                continue
                            genero = val
                            paso = 2
                    except PasoAnterior:
                        if paso == 0:
                            mostrar_aviso("Regresando al menú de catálogos...")
                            return
                        paso -= 1
                        mostrar_aviso("Regresando al campo anterior...")

                self.catalogos.crear_categoria(Categoria(codigo, genero))
                mostrar_exito("Categoría registrada correctamente.")
                if not self._confirmar_continuar("¿Deseas registrar OTRA categoría?"):
                    return
            except (OperacionCancelada, PasoAnterior):
                mostrar_aviso("Regresando al menú de catálogos...")
                return
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
                if not self._confirmar_continuar("¿Deseas intentar registrar otra categoría?"):
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
                nombre = None
                ap1 = None
                ap2 = None
                paso = 0

                while paso < 3:
                    try:
                        if paso == 0:
                            nombre = pedir_texto(
                                "Nombre de pila",
                                max_len=50,
                                validador=validar_nombre_persona,
                            )
                            paso = 1
                        elif paso == 1:
                            ap1 = pedir_texto(
                                "Primer apellido",
                                max_len=50,
                                validador=validar_nombre_persona,
                            )
                            paso = 2
                        elif paso == 2:
                            ap2 = pedir_texto(
                                "Segundo apellido",
                                max_len=50,
                                obligatorio=False,
                                validador=validar_nombre_persona,
                            )
                            if self.catalogos.existe_autor_nombre(nombre, ap1, ap2):
                                mostrar_error(
                                    "Ya existe un autor registrado con ese mismo nombre completo."
                                )
                                paso = 0
                                continue
                            paso = 3
                    except PasoAnterior:
                        if paso == 0:
                            mostrar_aviso("Regresando al menú de catálogos...")
                            return
                        paso -= 1
                        mostrar_aviso("Regresando al campo anterior...")

                nuevo_id = self.catalogos.crear_autor(Autor(nombre, ap1, ap2))
                mostrar_exito(f"Autor registrado con ID #{nuevo_id}.")
                if not self._confirmar_continuar("¿Deseas registrar OTRO autor?"):
                    return
            except (OperacionCancelada, PasoAnterior):
                mostrar_aviso("Regresando al menú de catálogos...")
                return
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
                if not self._confirmar_continuar("¿Deseas intentar registrar otro autor?"):
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

                mostrar_ayuda_cancelar()
                nombre = None
                clave_pais = None
                paso = 0

                while paso < 2:
                    try:
                        if paso == 0:
                            nombre = pedir_texto(
                                "Nombre de la editorial",
                                max_len=50,
                                validador=validar_texto_descriptivo,
                            )
                            paso = 1
                        elif paso == 1:
                            clave_pais = self._seleccionar_o_crear_pais()
                            if self.catalogos.existe_editorial_nombre(nombre, clave_pais):
                                mostrar_error(
                                    f"Ya existe la editorial '{nombre}' registrada en el país '{clave_pais}'."
                                )
                                paso = 0
                                continue
                            paso = 2
                    except PasoAnterior:
                        if paso == 0:
                            mostrar_aviso("Regresando al menú de catálogos...")
                            return
                        paso -= 1
                        mostrar_aviso("Regresando al campo anterior...")

                nuevo_id = self.catalogos.crear_editorial(Editorial(nombre, clave_pais))
                mostrar_exito(f"Editorial registrada con ID #{nuevo_id}.")
                if not self._confirmar_continuar("¿Deseas registrar OTRA editorial?"):
                    return
            except (OperacionCancelada, PasoAnterior):
                mostrar_aviso("Regresando al menú de catálogos...")
                return
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
                if not self._confirmar_continuar("¿Deseas intentar registrar otra editorial?"):
                    return

    def _catalogo_proveedores(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo("CATÁLOGO DE PROVEEDORES")
            self._mostrar_proveedores(self.catalogos.listar_proveedores())
            print("1. Registrar nuevo proveedor")
            print("2. Agregar teléfono a proveedor existente")
            print("0. Volver\n")
            op = pedir_entero(
                "Opción", minimo=0, maximo=2, permitir_cancelar=False, permitir_atras=False
            )
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

            rfc = None
            empresa = None
            telefonos = []
            paso = 0

            try:
                while paso < 3:
                    try:
                        if paso == 0:
                            val = pedir_texto(
                                "RFC del proveedor (12-13 caracteres, ej. DIS890412AB1)",
                                max_len=13,
                                validador=validar_rfc,
                            ).upper()
                            if self.catalogos.existe_proveedor(val):
                                mostrar_error(
                                    f"Ya existe un proveedor registrado con el RFC '{val}'."
                                )
                                continue
                            rfc = val
                            paso = 1
                        elif paso == 1:
                            empresa = pedir_texto(
                                "Nombre de la empresa",
                                max_len=50,
                                validador=validar_texto_descriptivo,
                            )
                            paso = 2
                        elif paso == 2:
                            telefonos = self._capturar_telefonos("este proveedor", telefonos)
                            paso = 3
                    except PasoAnterior:
                        if paso == 0:
                            mostrar_aviso("Regresando al menú de proveedores...")
                            return
                        paso -= 1
                        mostrar_aviso("Regresando al campo anterior...")

                self.catalogos.crear_proveedor(Proveedor(rfc, empresa, telefonos))
                mostrar_exito("Proveedor registrado correctamente.")
                if not self._confirmar_continuar("¿Deseas registrar OTRO proveedor?"):
                    return
            except OperacionCancelada:
                mostrar_aviso("Operación cancelada. Regresando al menú...")
                pausar()
                return
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
                if not self._confirmar_continuar("¿Deseas intentar registrar otro proveedor?"):
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

            rfc = None
            tel = None
            paso = 0

            try:
                while paso < 2:
                    try:
                        if paso == 0:
                            val = pedir_texto("RFC del proveedor", max_len=13).upper()
                            if not self.catalogos.existe_proveedor(val):
                                mostrar_error("No existe ningún proveedor con ese RFC.")
                                continue
                            rfc = val
                            paso = 1
                        elif paso == 1:
                            val_tel = pedir_texto(
                                "Nuevo teléfono (10-15 dígitos)",
                                max_len=20,
                                validador=validar_telefono,
                            )
                            if self.catalogos.existe_telefono_proveedor(rfc, val_tel):
                                mostrar_error(
                                    "Ese teléfono ya está registrado para este proveedor."
                                )
                                continue
                            tel = val_tel
                            paso = 2
                    except PasoAnterior:
                        if paso == 0:
                            mostrar_aviso("Regresando al menú de proveedores...")
                            return
                        paso -= 1
                        mostrar_aviso("Regresando al campo anterior...")

                self.catalogos.agregar_telefono_proveedor(rfc, tel)
                mostrar_exito("Teléfono agregado al proveedor.")
                if not self._confirmar_continuar(
                    "¿Deseas agregar OTRO teléfono a un proveedor?"
                ):
                    return
            except OperacionCancelada:
                mostrar_aviso("Operación cancelada. Regresando al menú...")
                pausar()
                return
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
                if not self._confirmar_continuar("¿Deseas intentar de nuevo?"):
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
                seccion = None
                pasillo = None
                estante = None
                paso = 0

                while paso < 3:
                    try:
                        if paso == 0:
                            seccion = pedir_texto(
                                "Sección (ej. Literatura, Ingeniería)",
                                max_len=50,
                                validador=validar_texto_descriptivo,
                            )
                            paso = 1
                        elif paso == 1:
                            pasillo = pedir_entero("Número de pasillo (1-500)", minimo=1, maximo=500)
                            paso = 2
                        elif paso == 2:
                            estante = pedir_entero("Número de estante (1-500)", minimo=1, maximo=500)
                            if self.catalogos.existe_localizacion_datos(seccion, pasillo, estante):
                                mostrar_error(
                                    "Ya existe una localización con esa misma sección, pasillo y estante."
                                )
                                paso = 0
                                continue
                            paso = 3
                    except PasoAnterior:
                        if paso == 0:
                            mostrar_aviso("Regresando al menú de catálogos...")
                            return
                        paso -= 1
                        mostrar_aviso("Regresando al campo anterior...")

                nuevo_id = self.catalogos.crear_localizacion(
                    Localizacion(estante, seccion, pasillo)
                )
                mostrar_exito(f"Localización registrada con ID #{nuevo_id}.")
                if not self._confirmar_continuar("¿Deseas registrar OTRA localización?"):
                    return
            except (OperacionCancelada, PasoAnterior):
                mostrar_aviso("Regresando al menú de catálogos...")
                return
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
                if not self._confirmar_continuar("¿Deseas intentar registrar otra localización?"):
                    return

    def _catalogo_usuarios(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo("CATÁLOGO DE USUARIOS")
            self._mostrar_usuarios(self.catalogos.listar_usuarios())
            print("1. Registrar nuevo usuario")
            print("2. Agregar teléfono a usuario existente")
            print("0. Volver\n")
            op = pedir_entero(
                "Opción", minimo=0, maximo=2, permitir_cancelar=False, permitir_atras=False
            )
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

            nombre = None
            ap1 = None
            ap2 = None
            calle = None
            numero = None
            colonia = None
            telefonos = []
            paso = 0

            try:
                while paso < 7:
                    try:
                        if paso == 0:
                            nombre = pedir_texto(
                                "Nombre de pila",
                                max_len=50,
                                validador=validar_nombre_persona,
                            )
                            paso = 1
                        elif paso == 1:
                            ap1 = pedir_texto(
                                "Primer apellido",
                                max_len=50,
                                validador=validar_nombre_persona,
                            )
                            paso = 2
                        elif paso == 2:
                            ap2 = pedir_texto(
                                "Segundo apellido",
                                max_len=50,
                                obligatorio=False,
                                validador=validar_nombre_persona,
                            )
                            paso = 3
                        elif paso == 3:
                            calle = pedir_texto(
                                "Calle (máx. 30)",
                                max_len=30,
                                validador=validar_texto_descriptivo,
                            )
                            paso = 4
                        elif paso == 4:
                            numero = pedir_texto(
                                "Número exterior/interior (ej. 412, 10-B o S/N)",
                                max_len=10,
                                validador=validar_numero_domicilio,
                            )
                            paso = 5
                        elif paso == 5:
                            colonia = pedir_texto(
                                "Colonia (máx. 50)",
                                max_len=50,
                                validador=validar_texto_descriptivo,
                            )
                            if self.catalogos.existe_usuario_datos(
                                nombre, ap1, ap2, calle, numero, colonia
                            ):
                                mostrar_error(
                                    "Ya existe un usuario registrado con ese mismo nombre y dirección."
                                )
                                paso = 0
                                continue
                            paso = 6
                        elif paso == 6:
                            telefonos = self._capturar_telefonos("este usuario", telefonos)
                            paso = 7
                    except PasoAnterior:
                        if paso == 0:
                            mostrar_aviso("Regresando al menú de usuarios...")
                            return
                        paso -= 1
                        mostrar_aviso("Regresando al campo anterior...")

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
                if not self._confirmar_continuar("¿Deseas registrar OTRO usuario?"):
                    return
            except OperacionCancelada:
                mostrar_aviso("Operación cancelada. Regresando al menú...")
                pausar()
                return
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
                if not self._confirmar_continuar("¿Deseas intentar registrar otro usuario?"):
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

            id_usr = None
            tel = None
            paso = 0

            try:
                while paso < 2:
                    try:
                        if paso == 0:
                            val_id = pedir_entero("ID del usuario", minimo=1)
                            if not self.catalogos.existe_usuario(val_id):
                                mostrar_error("No existe ningún usuario con ese ID.")
                                continue
                            id_usr = val_id
                            paso = 1
                        elif paso == 1:
                            val_tel = pedir_texto(
                                "Nuevo teléfono (10-15 dígitos)",
                                max_len=20,
                                validador=validar_telefono,
                            )
                            if self.catalogos.existe_telefono_usuario(id_usr, val_tel):
                                mostrar_error("Ese teléfono ya está registrado para este usuario.")
                                continue
                            tel = val_tel
                            paso = 2
                    except PasoAnterior:
                        if paso == 0:
                            mostrar_aviso("Regresando al menú de usuarios...")
                            return
                        paso -= 1
                        mostrar_aviso("Regresando al campo anterior...")

                self.catalogos.agregar_telefono_usuario(id_usr, tel)
                mostrar_exito("Teléfono agregado al usuario.")
                if not self._confirmar_continuar("¿Deseas agregar OTRO teléfono a un usuario?"):
                    return
            except OperacionCancelada:
                mostrar_aviso("Operación cancelada. Regresando al menú...")
                pausar()
                return
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
                if not self._confirmar_continuar("¿Deseas intentar de nuevo?"):
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
                nombre = None
                ap1 = None
                ap2 = None
                user = None
                pwd = None
                paso = 0

                while paso < 5:
                    try:
                        if paso == 0:
                            nombre = pedir_texto(
                                "Nombre de pila",
                                max_len=50,
                                validador=validar_nombre_persona,
                            )
                            paso = 1
                        elif paso == 1:
                            ap1 = pedir_texto(
                                "Primer apellido",
                                max_len=50,
                                validador=validar_nombre_persona,
                            )
                            paso = 2
                        elif paso == 2:
                            ap2 = pedir_texto(
                                "Segundo apellido",
                                max_len=50,
                                obligatorio=False,
                                validador=validar_nombre_persona,
                            )
                            paso = 3
                        elif paso == 3:
                            val_user = pedir_texto(
                                "Nombre de usuario (3-30 caracteres, sin espacios)",
                                max_len=30,
                                validador=validar_nombre_usuario,
                            )
                            if self.catalogos.existe_empleado_user(val_user):
                                mostrar_error(
                                    f"El nombre de usuario '{val_user}' ya está en uso. Elige otro."
                                )
                                continue
                            user = val_user
                            paso = 4
                        elif paso == 4:
                            pwd = pedir_texto(
                                "Contraseña (6-50 caracteres, sin espacios)",
                                max_len=50,
                                validador=validar_contrasena,
                            )
                            paso = 5
                    except PasoAnterior:
                        if paso == 0:
                            mostrar_aviso("Regresando al menú de catálogos...")
                            return
                        paso -= 1
                        mostrar_aviso("Regresando al campo anterior...")

                nuevo_id = self.catalogos.crear_empleado(
                    Empleado(nombre, ap1, user, pwd, segundo_ap=ap2)
                )
                mostrar_exito(f"Empleado registrado con ID #{nuevo_id}.")
                if not self._confirmar_continuar("¿Deseas registrar OTRO empleado?"):
                    return
            except (OperacionCancelada, PasoAnterior):
                mostrar_aviso("Regresando al menú de catálogos...")
                return
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
                if not self._confirmar_continuar("¿Deseas intentar registrar otro empleado?"):
                    return

    # ==========================================================
    # OPCIÓN 7: LISTADOS RÁPIDOS DE APOYO
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

            op = pedir_entero(
                "Opción", minimo=0, maximo=4, permitir_cancelar=False, permitir_atras=False
            )
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
            (
                d["isbn"],
                d["titulo"],
                d["anio"],
                d["tipo_obra"],
                d["genero"],
                d["total_autores"],
                d["total_ejemplares"],
            )
            for d in datos
        ]
        mostrar_tabla(
            "Obras",
            ["ISBN", "Título", "Año", "Tipo", "Categoría", "Autores", "Ejemplares"],
            filas,
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
                f"${d['total']}",
                d["estado"],
            )
            for d in datos
        ]
        mostrar_tabla(
            "Multas",
            ["Multa #", "Folio", "Usuario", "ISBN", "Ej. #", "Días", "Total", "Estado"],
            filas,
        )


if __name__ == "__main__":
    app = AplicacionBiblioteca()
    app.ejecutar()