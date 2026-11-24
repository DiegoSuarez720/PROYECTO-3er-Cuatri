"""Menú de catálogos auxiliares (Opción 6) y helpers de selección o alta al vuelo reutilizables."""

from mysql.connector import Error

from nucleo.modelos import (
    Autor,
    Categoria,
    Editorial,
    Empleado,
    Localizacion,
    Pais,
    Proveedor,
    TipoObra,
    Usuario,
)
from nucleo.utilidades import (
    confirmar,
    limpiar_pantalla,
    mostrar_aviso,
    mostrar_ayuda_cancelar,
    mostrar_error,
    mostrar_exito,
    mostrar_tabla,
    mostrar_titulo,
    normalizar_telefono,
    OperacionCancelada,
    PasoAnterior,
    pausar,
    pedir_entero,
    pedir_texto,
    validar_clave_pais,
    validar_codigo_categoria,
    validar_contrasena,
    validar_nombre_persona,
    validar_nombre_usuario,
    validar_numero_domicilio,
    validar_rfc,
    validar_solo_letras,
    validar_telefono,
    validar_texto_descriptivo,
)
from nucleo.vistas import (
    confirmar_continuar,
    mostrar_autores,
    mostrar_categorias,
    mostrar_editoriales,
    mostrar_localizaciones,
    mostrar_paises,
    mostrar_proveedores,
    mostrar_tipos,
    mostrar_usuarios,
)


def capturar_telefonos(entidad, telefonos_actuales=None):
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


def capturar_lista_asociada(
    etiqueta_otro, etiqueta_plural, fn_seleccionar, ids_actuales=None
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


def crear_pais_rapido(catalogos):
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
                if catalogos.existe_pais(val):
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
                if catalogos.existe_pais_nombre(val):
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
        catalogos.crear_pais(Pais(clave, nombre))
        mostrar_exito(f"País '{nombre}' ({clave}) guardado en la base de datos.")
        return clave
    except (ValueError, Error) as e:
        mostrar_error(f"Error al guardar país: {e}")
        return None


def seleccionar_o_crear_pais(catalogos):
    while True:
        paises = catalogos.listar_paises()
        if not paises:
            mostrar_aviso("No hay países registrados. Registra uno nuevo para la editorial:")
            clave = crear_pais_rapido(catalogos)
            if clave is not None:
                return clave
            raise PasoAnterior()

        mostrar_paises(paises)
        entrada = pedir_texto(
            "Clave del país (escribe 'nuevo' para registrar uno, o 'atras' para volver)",
            max_len=20,
        )
        if entrada.lower() in ("nuevo", "nueva"):
            clave = crear_pais_rapido(catalogos)
            if clave is not None:
                return clave
            continue

        clave = entrada.upper()
        if not catalogos.existe_pais(clave):
            mostrar_error("Esa clave de país no existe. Elige una de la tabla o escribe 'nuevo'.")
            continue
        return clave


def crear_tipo_rapido(catalogos):
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

        if catalogos.existe_tipo_nombre(nombre):
            mostrar_error(f"Ya existe un tipo de obra registrado como '{nombre}'.")
            continue

        try:
            nuevo_id = catalogos.crear_tipo(TipoObra(nombre))
            mostrar_exito(f"Tipo de obra '{nombre}' guardado con ID #{nuevo_id}.")
            return nuevo_id
        except (ValueError, Error) as e:
            mostrar_error(f"Error al guardar tipo de obra: {e}")
            return None


def seleccionar_o_crear_tipo(catalogos):
    while True:
        tipos = catalogos.listar_tipos()
        if not tipos:
            mostrar_aviso("No hay tipos de obra registrados. Registra uno nuevo:")
            nuevo_id = crear_tipo_rapido(catalogos)
            if nuevo_id is not None:
                return nuevo_id
            raise PasoAnterior()

        mostrar_tipos(tipos)
        entrada = pedir_texto(
            "ID del tipo de obra (escribe 'nuevo' para registrar uno, o 'atras' para volver)",
            max_len=20,
        )
        if entrada.lower() in ("nuevo", "nueva"):
            nuevo_id = crear_tipo_rapido(catalogos)
            if nuevo_id is not None:
                return nuevo_id
            continue

        try:
            id_tipo = int(entrada)
        except ValueError:
            mostrar_error("Ingresa un ID numérico válido o escribe 'nuevo'.")
            continue

        if id_tipo <= 0 or not catalogos.existe_tipo(id_tipo):
            mostrar_error("Ese ID de tipo de obra no existe.")
            continue
        return id_tipo


def crear_categoria_rapida(catalogos):
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
                if catalogos.existe_categoria(val):
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
                if catalogos.existe_categoria_genero(val):
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
        catalogos.crear_categoria(Categoria(codigo, genero))
        mostrar_exito(f"Categoría '{genero}' ({codigo}) guardada en la base de datos.")
        return codigo
    except (ValueError, Error) as e:
        mostrar_error(f"Error al guardar categoría: {e}")
        return None


def seleccionar_o_crear_categoria(catalogos):
    while True:
        categorias = catalogos.listar_categorias()
        if not categorias:
            mostrar_aviso("No hay categorías registradas. Registra una nueva:")
            cod = crear_categoria_rapida(catalogos)
            if cod is not None:
                return cod
            raise PasoAnterior()

        mostrar_categorias(categorias)
        entrada = pedir_texto(
            "Código de categoría (escribe 'nuevo' para registrar una, o 'atras' para volver)",
            max_len=20,
        )
        if entrada.lower() in ("nuevo", "nueva"):
            cod = crear_categoria_rapida(catalogos)
            if cod is not None:
                return cod
            continue

        cod = entrada.upper()
        if not catalogos.existe_categoria(cod):
            mostrar_error("Ese código de categoría no existe. Elige uno de la tabla o escribe 'nuevo'.")
            continue
        return cod


def crear_autor_rapido(catalogos):
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
                if catalogos.existe_autor_nombre(nombre, ap1, ap2):
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
        nuevo_id = catalogos.crear_autor(autor)
        mostrar_exito(f"Autor '{autor.nombre_completo}' guardado con ID #{nuevo_id}.")
        return nuevo_id
    except (ValueError, Error) as e:
        mostrar_error(f"Error al guardar autor: {e}")
        return None


def seleccionar_o_crear_autor(catalogos):
    while True:
        autores = catalogos.listar_autores()
        if not autores:
            mostrar_aviso("No hay autores registrados. Registra un autor nuevo:")
            nuevo_id = crear_autor_rapido(catalogos)
            if nuevo_id is not None:
                return nuevo_id
            raise PasoAnterior()

        mostrar_autores(autores)
        entrada = pedir_texto(
            "ID del autor a asociar (escribe 'nuevo' para registrar uno, o 'atras' para volver)",
            max_len=20,
        )
        if entrada.lower() in ("nuevo", "nueva"):
            nuevo_id = crear_autor_rapido(catalogos)
            if nuevo_id is not None:
                return nuevo_id
            continue

        try:
            id_autor = int(entrada)
        except ValueError:
            mostrar_error("Ingresa un ID numérico válido o escribe 'nuevo'.")
            continue

        if id_autor <= 0 or not catalogos.existe_autor(id_autor):
            mostrar_error("Ese ID de autor no existe.")
            continue
        return id_autor


def crear_editorial_rapida(catalogos):
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
                clave_pais = seleccionar_o_crear_pais(catalogos)
                if catalogos.existe_editorial_nombre(nombre, clave_pais):
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
        nuevo_id = catalogos.crear_editorial(Editorial(nombre, clave_pais))
        mostrar_exito(f"Editorial '{nombre}' ({clave_pais}) guardada con ID #{nuevo_id}.")
        return nuevo_id
    except (ValueError, Error) as e:
        mostrar_error(f"Error al guardar editorial: {e}")
        return None


def seleccionar_o_crear_editorial(catalogos):
    while True:
        editoriales = catalogos.listar_editoriales()
        if not editoriales:
            mostrar_aviso("No hay editoriales registradas. Registra una editorial nueva:")
            nuevo_id = crear_editorial_rapida(catalogos)
            if nuevo_id is not None:
                return nuevo_id
            raise PasoAnterior()

        mostrar_editoriales(editoriales)
        entrada = pedir_texto(
            "ID de la editorial a asociar (escribe 'nuevo' para registrar una, o 'atras' para volver)",
            max_len=20,
        )
        if entrada.lower() in ("nuevo", "nueva"):
            nuevo_id = crear_editorial_rapida(catalogos)
            if nuevo_id is not None:
                return nuevo_id
            continue

        try:
            id_ed = int(entrada)
        except ValueError:
            mostrar_error("Ingresa un ID numérico válido o escribe 'nuevo'.")
            continue

        if id_ed <= 0 or not catalogos.existe_editorial(id_ed):
            mostrar_error("Ese ID de editorial no existe.")
            continue
        return id_ed


def crear_proveedor_rapido(catalogos):
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
                if catalogos.existe_proveedor(val):
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
                telefonos = capturar_telefonos("este proveedor", telefonos)
                paso = 3
        except PasoAnterior:
            if paso == 0:
                mostrar_aviso("Regresando a la selección de proveedores...")
                return None
            paso -= 1
            mostrar_aviso("Regresando al campo anterior...")

    try:
        catalogos.crear_proveedor(Proveedor(rfc, empresa, telefonos))
        mostrar_exito(f"Proveedor '{empresa}' ({rfc}) guardado en la base de datos.")
        return rfc
    except (ValueError, Error) as e:
        mostrar_error(f"Error al guardar proveedor: {e}")
        return None


def seleccionar_o_crear_proveedor(catalogos):
    while True:
        proveedores = catalogos.listar_proveedores()
        if not proveedores:
            mostrar_aviso("No hay proveedores registrados. Registra un proveedor nuevo:")
            rfc = crear_proveedor_rapido(catalogos)
            if rfc is not None:
                return rfc
            raise PasoAnterior()

        mostrar_proveedores(proveedores)
        entrada = pedir_texto(
            "RFC del proveedor (escribe 'nuevo' para registrar uno, o 'atras' para volver)",
            max_len=20,
        )
        if entrada.lower() in ("nuevo", "nueva"):
            rfc = crear_proveedor_rapido(catalogos)
            if rfc is not None:
                return rfc
            continue

        rfc = entrada.upper()
        if not catalogos.existe_proveedor(rfc):
            mostrar_error("Ese RFC de proveedor no existe. Elige uno de la tabla o escribe 'nuevo'.")
            continue
        return rfc


def crear_localizacion_rapida(catalogos):
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
                if catalogos.existe_localizacion_datos(seccion, pasillo, estante):
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
        nuevo_id = catalogos.crear_localizacion(Localizacion(estante, seccion, pasillo))
        mostrar_exito(
            f"Localización '{seccion}' (Pasillo {pasillo}, Estante {estante}) "
            f"guardada con ID #{nuevo_id}."
        )
        return nuevo_id
    except (ValueError, Error) as e:
        mostrar_error(f"Error al guardar localización: {e}")
        return None


def seleccionar_o_crear_localizacion(catalogos, permitir_sin_asignar=False):
    while True:
        locs = catalogos.listar_localizaciones()
        if not locs:
            mostrar_aviso("No hay localizaciones registradas. Registra una nueva:")
            nuevo_id = crear_localizacion_rapida(catalogos)
            if nuevo_id is not None:
                return nuevo_id
            raise PasoAnterior()

        mostrar_localizaciones(locs)
        if permitir_sin_asignar:
            etiqueta = "ID de localización (0 = Sin asignar, 'nuevo' = registrar, 'atras' = volver)"
        else:
            etiqueta = "ID de localización (escribe 'nuevo' para registrar una, o 'atras' para volver)"

        entrada = pedir_texto(etiqueta, max_len=20)
        if entrada.lower() in ("nuevo", "nueva"):
            nuevo_id = crear_localizacion_rapida(catalogos)
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

        if id_loc <= 0 or not catalogos.existe_localizacion(id_loc):
            mostrar_error("Ese ID de localización no existe.")
            continue
        return id_loc


def crear_usuario_rapido(catalogos):
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
                if catalogos.existe_usuario_datos(
                    nombre, ap1, ap2, calle, numero, colonia
                ):
                    mostrar_error(
                        "Ya existe un usuario registrado con ese mismo nombre y dirección."
                    )
                    paso = 0
                    continue
                paso = 6
            elif paso == 6:
                telefonos = capturar_telefonos("este usuario", telefonos)
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
        nuevo_id = catalogos.crear_usuario(usr)
        mostrar_exito(
            f"Usuario '{usr.nombre_completo}' guardado en la base de datos con ID #{nuevo_id}."
        )
        return nuevo_id
    except (ValueError, Error) as e:
        mostrar_error(f"Error al guardar usuario: {e}")
        return None


def seleccionar_o_crear_usuario(catalogos):
    while True:
        usuarios = catalogos.listar_usuarios()
        if not usuarios:
            mostrar_aviso(
                "No hay usuarios registrados. Registra un usuario nuevo para el préstamo:"
            )
            nuevo_id = crear_usuario_rapido(catalogos)
            if nuevo_id is not None:
                return nuevo_id
            raise PasoAnterior()

        mostrar_usuarios(usuarios)
        entrada = pedir_texto(
            "ID del usuario (escribe 'nuevo' para registrar uno, o 'atras' para volver)",
            max_len=20,
        )
        if entrada.lower() in ("nuevo", "nueva"):
            nuevo_id = crear_usuario_rapido(catalogos)
            if nuevo_id is not None:
                return nuevo_id
            continue

        try:
            id_usuario = int(entrada)
        except ValueError:
            mostrar_error("Ingresa un ID numérico válido o escribe 'nuevo'.")
            continue

        if id_usuario <= 0 or not catalogos.existe_usuario(id_usuario):
            mostrar_error(
                "No existe ningún usuario con ese ID. Elige uno de la tabla o escribe 'nuevo'."
            )
            continue
        return id_usuario


class MenuCatalogos:
    """Opción 6: catálogos auxiliares (países, tipos, categorías, autores, editoriales, proveedores, localizaciones, usuarios, empleados)."""

    def __init__(self, catalogos):
        self.catalogos = catalogos

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
            mostrar_paises(self.catalogos.listar_paises())
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
                if not confirmar_continuar("¿Deseas registrar OTRO país?"):
                    return
            except (OperacionCancelada, PasoAnterior):
                mostrar_aviso("Regresando al menú de catálogos...")
                return
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
                if not confirmar_continuar("¿Deseas intentar registrar otro país?"):
                    return

    def _catalogo_tipos(self):
        primera_vez = True
        while True:
            limpiar_pantalla()
            mostrar_titulo("CATÁLOGO DE TIPOS DE OBRA")
            mostrar_tipos(self.catalogos.listar_tipos())
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
                if not confirmar_continuar("¿Deseas registrar OTRO tipo de obra?"):
                    return
            except (OperacionCancelada, PasoAnterior):
                mostrar_aviso("Regresando al menú de catálogos...")
                return
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
                if not confirmar_continuar("¿Deseas intentar registrar otro tipo de obra?"):
                    return

    def _catalogo_categorias(self):
        primera_vez = True
        while True:
            limpiar_pantalla()
            mostrar_titulo("CATÁLOGO DE CATEGORÍAS")
            mostrar_categorias(self.catalogos.listar_categorias())
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
                if not confirmar_continuar("¿Deseas registrar OTRA categoría?"):
                    return
            except (OperacionCancelada, PasoAnterior):
                mostrar_aviso("Regresando al menú de catálogos...")
                return
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
                if not confirmar_continuar("¿Deseas intentar registrar otra categoría?"):
                    return

    def _catalogo_autores(self):
        primera_vez = True
        while True:
            limpiar_pantalla()
            mostrar_titulo("CATÁLOGO DE AUTORES")
            mostrar_autores(self.catalogos.listar_autores())
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
                if not confirmar_continuar("¿Deseas registrar OTRO autor?"):
                    return
            except (OperacionCancelada, PasoAnterior):
                mostrar_aviso("Regresando al menú de catálogos...")
                return
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
                if not confirmar_continuar("¿Deseas intentar registrar otro autor?"):
                    return

    def _catalogo_editoriales(self):
        primera_vez = True
        while True:
            limpiar_pantalla()
            mostrar_titulo("CATÁLOGO DE EDITORIALES")
            mostrar_editoriales(self.catalogos.listar_editoriales())
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
                            clave_pais = seleccionar_o_crear_pais(self.catalogos)
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
                if not confirmar_continuar("¿Deseas registrar OTRA editorial?"):
                    return
            except (OperacionCancelada, PasoAnterior):
                mostrar_aviso("Regresando al menú de catálogos...")
                return
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
                if not confirmar_continuar("¿Deseas intentar registrar otra editorial?"):
                    return

    def _catalogo_proveedores(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo("CATÁLOGO DE PROVEEDORES")
            mostrar_proveedores(self.catalogos.listar_proveedores())
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
            mostrar_proveedores(self.catalogos.listar_proveedores())
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
                            telefonos = capturar_telefonos("este proveedor", telefonos)
                            paso = 3
                    except PasoAnterior:
                        if paso == 0:
                            mostrar_aviso("Regresando al menú de proveedores...")
                            return
                        paso -= 1
                        mostrar_aviso("Regresando al campo anterior...")

                self.catalogos.crear_proveedor(Proveedor(rfc, empresa, telefonos))
                mostrar_exito("Proveedor registrado correctamente.")
                if not confirmar_continuar("¿Deseas registrar OTRO proveedor?"):
                    return
            except OperacionCancelada:
                mostrar_aviso("Operación cancelada. Regresando al menú...")
                pausar()
                return
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
                if not confirmar_continuar("¿Deseas intentar registrar otro proveedor?"):
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
            mostrar_proveedores(proveedores)
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
                if not confirmar_continuar(
                    "¿Deseas agregar OTRO teléfono a un proveedor?"
                ):
                    return
            except OperacionCancelada:
                mostrar_aviso("Operación cancelada. Regresando al menú...")
                pausar()
                return
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
                if not confirmar_continuar("¿Deseas intentar de nuevo?"):
                    return

    def _catalogo_localizaciones(self):
        primera_vez = True
        while True:
            limpiar_pantalla()
            mostrar_titulo("CATÁLOGO DE LOCALIZACIONES")
            mostrar_localizaciones(self.catalogos.listar_localizaciones())
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
                if not confirmar_continuar("¿Deseas registrar OTRA localización?"):
                    return
            except (OperacionCancelada, PasoAnterior):
                mostrar_aviso("Regresando al menú de catálogos...")
                return
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
                if not confirmar_continuar("¿Deseas intentar registrar otra localización?"):
                    return

    def _catalogo_usuarios(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo("CATÁLOGO DE USUARIOS")
            mostrar_usuarios(self.catalogos.listar_usuarios())
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
            mostrar_usuarios(self.catalogos.listar_usuarios())
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
                            telefonos = capturar_telefonos("este usuario", telefonos)
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
                if not confirmar_continuar("¿Deseas registrar OTRO usuario?"):
                    return
            except OperacionCancelada:
                mostrar_aviso("Operación cancelada. Regresando al menú...")
                pausar()
                return
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
                if not confirmar_continuar("¿Deseas intentar registrar otro usuario?"):
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
            mostrar_usuarios(usuarios)
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
                if not confirmar_continuar("¿Deseas agregar OTRO teléfono a un usuario?"):
                    return
            except OperacionCancelada:
                mostrar_aviso("Operación cancelada. Regresando al menú...")
                pausar()
                return
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
                if not confirmar_continuar("¿Deseas intentar de nuevo?"):
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
                if not confirmar_continuar("¿Deseas registrar OTRO empleado?"):
                    return
            except (OperacionCancelada, PasoAnterior):
                mostrar_aviso("Regresando al menú de catálogos...")
                return
            except (ValueError, Error) as e:
                mostrar_error(f"Error: {e}")
                if not confirmar_continuar("¿Deseas intentar registrar otro empleado?"):
                    return
