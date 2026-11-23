"""Clases gestoras con lógica de negocio, anti-duplicados y consultas SQL para las 20 tablas."""

from decimal import Decimal
from mysql.connector import Error
from conexion import ConexionDB
from modelos import Empleado

# Tarifa fija diaria por retraso en devolución (pueden ajustarla aquí si lo requieren)
TARIFA_MULTA_DIA = Decimal("15.00")


class GestorBase:
    """Clase base para compartir la conexión Singleton entre todos los gestores."""

    def __init__(self):
        self.db = ConexionDB()


class GestorAuth(GestorBase):
    """Gestiona el inicio de sesión de empleados en texto plano."""

    def iniciar_sesion(self, nombre_user, contrasena):
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT id_empleado, nombre_pila, primer_ap, segundo_ap, nombre_user, `contraseña`
                FROM empleado
                WHERE nombre_user = %s AND `contraseña` = %s
            """
            cursor.execute(sql, (nombre_user, contrasena))
            fila = cursor.fetchone()
            if not fila:
                return None

            return Empleado(
                id_empleado=fila["id_empleado"],
                nombre_pila=fila["nombre_pila"],
                primer_ap=fila["primer_ap"],
                segundo_ap=fila["segundo_ap"],
                nombre_user=fila["nombre_user"],
                contrasena=fila["contraseña"],
            )
        finally:
            cursor.close()


class GestorCatalogos(GestorBase):
    """Altas, listados y validadores de existencia / duplicados para todos los catálogos."""

    # --- PAISES ---
    def listar_paises(self):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT clave, nombre FROM pais ORDER BY clave")
            return cursor.fetchall()
        finally:
            cursor.close()

    def existe_pais(self, clave):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT 1 FROM pais WHERE UPPER(clave) = UPPER(%s)", (clave.strip(),))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    def existe_pais_nombre(self, nombre):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "SELECT 1 FROM pais WHERE LOWER(TRIM(nombre)) = LOWER(%s)",
                (nombre.strip(),),
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    def crear_pais(self, pais):
        if self.existe_pais(pais.clave):
            raise ValueError(f"Ya existe un país con la clave '{pais.clave}'.")
        if self.existe_pais_nombre(pais.nombre):
            raise ValueError(f"Ya existe un país registrado con el nombre '{pais.nombre}'.")

        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "INSERT INTO pais (clave, nombre) VALUES (%s, %s)",
                (pais.clave, pais.nombre),
            )
            self.db.confirmar()
        except Error:
            self.db.revertir()
            raise
        finally:
            cursor.close()

    # --- TIPOS DE OBRA ---
    def listar_tipos(self):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT id_tipo, tipo_obra FROM tipo ORDER BY id_tipo")
            return cursor.fetchall()
        finally:
            cursor.close()

    def existe_tipo(self, id_tipo):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT 1 FROM tipo WHERE id_tipo = %s", (id_tipo,))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    def existe_tipo_nombre(self, tipo_obra):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "SELECT 1 FROM tipo WHERE LOWER(TRIM(tipo_obra)) = LOWER(%s)",
                (tipo_obra.strip(),),
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    def crear_tipo(self, tipo):
        if self.existe_tipo_nombre(tipo.tipo_obra):
            raise ValueError(f"Ya existe un tipo de obra registrado como '{tipo.tipo_obra}'.")

        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("INSERT INTO tipo (tipo_obra) VALUES (%s)", (tipo.tipo_obra,))
            nuevo_id = cursor.lastrowid
            self.db.confirmar()
            return nuevo_id
        except Error:
            self.db.revertir()
            raise
        finally:
            cursor.close()

    # --- CATEGORIAS ---
    def listar_categorias(self):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT codigo, genero FROM categoria ORDER BY codigo")
            return cursor.fetchall()
        finally:
            cursor.close()

    def existe_categoria(self, codigo):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "SELECT 1 FROM categoria WHERE UPPER(codigo) = UPPER(%s)",
                (codigo.strip(),),
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    def existe_categoria_genero(self, genero):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "SELECT 1 FROM categoria WHERE LOWER(TRIM(genero)) = LOWER(%s)",
                (genero.strip(),),
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    def crear_categoria(self, categoria):
        if self.existe_categoria(categoria.codigo):
            raise ValueError(f"Ya existe una categoría con el código '{categoria.codigo}'.")
        if self.existe_categoria_genero(categoria.genero):
            raise ValueError(f"Ya existe una categoría registrada con el género '{categoria.genero}'.")

        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "INSERT INTO categoria (codigo, genero) VALUES (%s, %s)",
                (categoria.codigo, categoria.genero),
            )
            self.db.confirmar()
        except Error:
            self.db.revertir()
            raise
        finally:
            cursor.close()

    # --- AUTORES ---
    def listar_autores(self):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "SELECT num_id, nombre_pila, primer_ap, segundo_ap FROM autor ORDER BY num_id"
            )
            return cursor.fetchall()
        finally:
            cursor.close()

    def existe_autor(self, num_id):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT 1 FROM autor WHERE num_id = %s", (num_id,))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    def existe_autor_nombre(self, nombre_pila, primer_ap, segundo_ap=None):
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT 1 FROM autor
                WHERE LOWER(TRIM(nombre_pila)) = LOWER(%s)
                  AND LOWER(TRIM(primer_ap)) = LOWER(%s)
                  AND LOWER(TRIM(COALESCE(segundo_ap, ''))) = LOWER(%s)
            """
            cursor.execute(
                sql,
                (nombre_pila.strip(), primer_ap.strip(), (segundo_ap or "").strip()),
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    def crear_autor(self, autor):
        if self.existe_autor_nombre(autor.nombre_pila, autor.primer_ap, autor.segundo_ap):
            raise ValueError(f"Ya existe un autor registrado como '{autor.nombre_completo}'.")

        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "INSERT INTO autor (nombre_pila, primer_ap, segundo_ap) VALUES (%s, %s, %s)",
                (autor.nombre_pila, autor.primer_ap, autor.segundo_ap),
            )
            nuevo_id = cursor.lastrowid
            self.db.confirmar()
            return nuevo_id
        except Error:
            self.db.revertir()
            raise
        finally:
            cursor.close()

    # --- EDITORIALES ---
    def listar_editoriales(self):
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT e.id_editorial, e.nombre, e.pais, p.nombre AS nombre_pais
                FROM editorial e
                INNER JOIN pais p ON e.pais = p.clave
                ORDER BY e.id_editorial
            """
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()

    def existe_editorial(self, id_editorial):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT 1 FROM editorial WHERE id_editorial = %s", (id_editorial,))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    def existe_editorial_nombre(self, nombre, pais):
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT 1 FROM editorial
                WHERE LOWER(TRIM(nombre)) = LOWER(%s)
                  AND UPPER(pais) = UPPER(%s)
            """
            cursor.execute(sql, (nombre.strip(), pais.strip()))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    def crear_editorial(self, editorial):
        if self.existe_editorial_nombre(editorial.nombre, editorial.pais):
            raise ValueError(
                f"Ya existe la editorial '{editorial.nombre}' registrada en el país '{editorial.pais}'."
            )

        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "INSERT INTO editorial (nombre, pais) VALUES (%s, %s)",
                (editorial.nombre, editorial.pais),
            )
            nuevo_id = cursor.lastrowid
            self.db.confirmar()
            return nuevo_id
        except Error:
            self.db.revertir()
            raise
        finally:
            cursor.close()

    # --- PROVEEDORES Y TELEFONOS ---
    def listar_proveedores(self):
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT pr.RFC, pr.nombre_empresa,
                       GROUP_CONCAT(tp.telefono SEPARATOR ', ') AS telefonos
                FROM proveedor pr
                LEFT JOIN telefono_proveedor tp ON pr.RFC = tp.proveedor
                GROUP BY pr.RFC, pr.nombre_empresa
                ORDER BY pr.RFC
            """
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()

    def existe_proveedor(self, rfc):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT 1 FROM proveedor WHERE UPPER(RFC) = UPPER(%s)", (rfc.strip(),))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    def existe_telefono_proveedor(self, rfc, telefono):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                """
                SELECT 1 FROM telefono_proveedor
                WHERE UPPER(proveedor) = UPPER(%s) AND TRIM(telefono) = %s
                """,
                (rfc.strip(), telefono.strip()),
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    def crear_proveedor(self, proveedor):
        if self.existe_proveedor(proveedor.rfc):
            raise ValueError(f"Ya existe un proveedor registrado con el RFC '{proveedor.rfc}'.")
        if not proveedor.telefonos:
            raise ValueError("Debes registrar al menos un teléfono para el proveedor.")

        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "INSERT INTO proveedor (RFC, nombre_empresa) VALUES (%s, %s)",
                (proveedor.rfc, proveedor.nombre_empresa),
            )
            for tel in dict.fromkeys(t.strip() for t in proveedor.telefonos):
                cursor.execute(
                    "INSERT INTO telefono_proveedor (telefono, proveedor) VALUES (%s, %s)",
                    (tel, proveedor.rfc),
                )
            self.db.confirmar()
        except Error:
            self.db.revertir()
            raise
        finally:
            cursor.close()

    def agregar_telefono_proveedor(self, rfc, telefono):
        if self.existe_telefono_proveedor(rfc, telefono):
            raise ValueError("Ese teléfono ya está registrado para este proveedor.")

        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "INSERT INTO telefono_proveedor (telefono, proveedor) VALUES (%s, %s)",
                (telefono.strip(), rfc.upper()),
            )
            self.db.confirmar()
        except Error:
            self.db.revertir()
            raise
        finally:
            cursor.close()

    # --- LOCALIZACIONES ---
    def listar_localizaciones(self):
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT id_localizacion, seccion, pasillo, estante
                FROM localizacion
                ORDER BY id_localizacion
            """
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()

    def existe_localizacion(self, id_localizacion):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "SELECT 1 FROM localizacion WHERE id_localizacion = %s",
                (id_localizacion,),
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    def existe_localizacion_datos(self, seccion, pasillo, estante):
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT 1 FROM localizacion
                WHERE LOWER(TRIM(seccion)) = LOWER(%s)
                  AND pasillo = %s
                  AND estante = %s
            """
            cursor.execute(sql, (seccion.strip(), pasillo, estante))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    def crear_localizacion(self, loc):
        if self.existe_localizacion_datos(loc.seccion, loc.pasillo, loc.estante):
            raise ValueError(
                f"Ya existe la localización '{loc.seccion}' (Pasillo {loc.pasillo}, Estante {loc.estante})."
            )

        cursor = self.db.obtener_cursor()
        try:
            sql = """
                INSERT INTO localizacion (estante, seccion, pasillo)
                VALUES (%s, %s, %s)
            """
            cursor.execute(sql, (loc.estante, loc.seccion, loc.pasillo))
            nuevo_id = cursor.lastrowid
            self.db.confirmar()
            return nuevo_id
        except Error:
            self.db.revertir()
            raise
        finally:
            cursor.close()

    # --- USUARIOS Y TELEFONOS ---
    def listar_usuarios(self):
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT u.id_usuario, u.nombre_pila, u.primer_ap, u.segundo_ap,
                       u.dir_calle, u.dir_numero, u.dir_colonia,
                       GROUP_CONCAT(tu.num_tel SEPARATOR ', ') AS telefonos
                FROM usuario u
                LEFT JOIN telefono_usuario tu ON u.id_usuario = tu.usuario
                GROUP BY u.id_usuario, u.nombre_pila, u.primer_ap, u.segundo_ap,
                         u.dir_calle, u.dir_numero, u.dir_colonia
                ORDER BY u.id_usuario
            """
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()

    def existe_usuario(self, id_usuario):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT 1 FROM usuario WHERE id_usuario = %s", (id_usuario,))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    def existe_usuario_datos(
        self, nombre_pila, primer_ap, segundo_ap, dir_calle, dir_numero, dir_colonia
    ):
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT 1 FROM usuario
                WHERE LOWER(TRIM(nombre_pila)) = LOWER(%s)
                  AND LOWER(TRIM(primer_ap)) = LOWER(%s)
                  AND LOWER(TRIM(COALESCE(segundo_ap, ''))) = LOWER(%s)
                  AND LOWER(TRIM(dir_calle)) = LOWER(%s)
                  AND LOWER(TRIM(dir_numero)) = LOWER(%s)
                  AND LOWER(TRIM(dir_colonia)) = LOWER(%s)
            """
            cursor.execute(
                sql,
                (
                    nombre_pila.strip(),
                    primer_ap.strip(),
                    (segundo_ap or "").strip(),
                    dir_calle.strip(),
                    dir_numero.strip(),
                    dir_colonia.strip(),
                ),
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    def existe_telefono_usuario(self, id_usuario, num_tel):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "SELECT 1 FROM telefono_usuario WHERE usuario = %s AND TRIM(num_tel) = %s",
                (id_usuario, num_tel.strip()),
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    def crear_usuario(self, usuario):
        if self.existe_usuario_datos(
            usuario.nombre_pila,
            usuario.primer_ap,
            usuario.segundo_ap,
            usuario.dir_calle,
            usuario.dir_numero,
            usuario.dir_colonia,
        ):
            raise ValueError("Ya existe un usuario registrado con ese mismo nombre y dirección.")
        if not usuario.telefonos:
            raise ValueError("Debes registrar al menos un teléfono para el usuario.")

        cursor = self.db.obtener_cursor()
        try:
            sql = """
                INSERT INTO usuario
                (nombre_pila, primer_ap, segundo_ap, dir_calle, dir_numero, dir_colonia)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                sql,
                (
                    usuario.nombre_pila,
                    usuario.primer_ap,
                    usuario.segundo_ap,
                    usuario.dir_calle,
                    usuario.dir_numero,
                    usuario.dir_colonia,
                ),
            )
            nuevo_id = cursor.lastrowid

            for tel in dict.fromkeys(t.strip() for t in usuario.telefonos):
                cursor.execute(
                    "INSERT INTO telefono_usuario (num_tel, usuario) VALUES (%s, %s)",
                    (tel, nuevo_id),
                )

            self.db.confirmar()
            return nuevo_id
        except Error:
            self.db.revertir()
            raise
        finally:
            cursor.close()

    def agregar_telefono_usuario(self, id_usuario, num_tel):
        if self.existe_telefono_usuario(id_usuario, num_tel):
            raise ValueError("Ese teléfono ya está registrado para este usuario.")

        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "INSERT INTO telefono_usuario (num_tel, usuario) VALUES (%s, %s)",
                (num_tel.strip(), id_usuario),
            )
            self.db.confirmar()
        except Error:
            self.db.revertir()
            raise
        finally:
            cursor.close()

    # --- EMPLEADOS ---
    def listar_empleados(self):
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT id_empleado, nombre_pila, primer_ap, segundo_ap, nombre_user
                FROM empleado
                ORDER BY id_empleado
            """
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()

    def existe_empleado_user(self, nombre_user):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "SELECT 1 FROM empleado WHERE LOWER(TRIM(nombre_user)) = LOWER(%s)",
                (nombre_user.strip(),),
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    def crear_empleado(self, empleado):
        if self.existe_empleado_user(empleado.nombre_user):
            raise ValueError(f"Ya existe un empleado con el usuario '{empleado.nombre_user}'.")

        cursor = self.db.obtener_cursor()
        try:
            sql = """
                INSERT INTO empleado
                (nombre_pila, primer_ap, segundo_ap, nombre_user, `contraseña`)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(
                sql,
                (
                    empleado.nombre_pila,
                    empleado.primer_ap,
                    empleado.segundo_ap,
                    empleado.nombre_user,
                    empleado.contrasena,
                ),
            )
            nuevo_id = cursor.lastrowid
            self.db.confirmar()
            return nuevo_id
        except Error:
            self.db.revertir()
            raise
        finally:
            cursor.close()


class GestorObras(GestorBase):
    """Obras, abastecimiento, ejemplares, localizaciones y ficha completa de obra."""

    def listar_obras(self):
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT o.isbn, o.titulo, o.subtitulo, o.`año_publicacion` AS anio,
                       t.tipo_obra, c.genero,
                       COUNT(DISTINCT e.ejemplar) AS total_ejemplares,
                       COUNT(DISTINCT ao.autor) AS total_autores
                FROM obra o
                INNER JOIN tipo t ON o.tipo = t.id_tipo
                INNER JOIN categoria c ON o.categoria = c.codigo
                LEFT JOIN ejemplar e ON o.isbn = e.obra
                LEFT JOIN autor_obra ao ON o.isbn = ao.obra
                GROUP BY o.isbn, o.titulo, o.subtitulo, o.`año_publicacion`,
                         t.tipo_obra, c.genero
                ORDER BY o.titulo
            """
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()

    def consultar_obra_completa(self, isbn):
        """Obtiene toda la información de una obra (ISBN, título, subtítulo, tipo, año, editorial, país y autores)."""
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT o.isbn,
                       o.titulo,
                       o.subtitulo,
                       t.tipo_obra,
                       o.`año_publicacion` AS anio_publicacion,
                       c.genero,
                       o.num_paginas,
                       ed.nombre AS editorial,
                       pa.nombre AS pais,
                       CONCAT_WS(' ', a.nombre_pila, a.primer_ap, a.segundo_ap) AS autor
                FROM obra AS o
                INNER JOIN tipo AS t ON o.tipo = t.id_tipo
                INNER JOIN categoria AS c ON o.categoria = c.codigo
                INNER JOIN obra_editorial AS oe ON oe.obra = o.isbn
                INNER JOIN editorial AS ed ON oe.editorial = ed.id_editorial
                INNER JOIN pais AS pa ON ed.pais = pa.clave
                INNER JOIN autor_obra AS ao ON ao.obra = o.isbn
                INNER JOIN autor AS a ON ao.autor = a.num_id
                WHERE o.isbn = %s
                ORDER BY autor, ed.nombre
            """
            cursor.execute(sql, (isbn,))
            return cursor.fetchall()
        finally:
            cursor.close()

    def existe_obra(self, isbn):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT 1 FROM obra WHERE isbn = %s", (isbn,))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    def obtener_localizacion_base(self):
        """Obtiene el primer id_localizacion disponible (por defecto 'Sin asignar / Recepcion')."""
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT MIN(id_localizacion) AS id_loc FROM localizacion")
            fila = cursor.fetchone()
            if not fila or fila["id_loc"] is None:
                raise ValueError(
                    "No existe ninguna localización en la base de datos. "
                    "Registra primero una localización en Catálogos auxiliares."
                )
            return fila["id_loc"]
        finally:
            cursor.close()

    def registrar_obra_completa(
        self, obra, rfc_proveedor, fecha_adquisicion, cantidad, id_localizacion=None
    ):
        """Inserta obra, autores, editoriales, abastecimiento y N ejemplares."""
        if not obra.autores:
            raise ValueError("Debes asociar al menos un autor a la obra.")
        if not obra.editoriales:
            raise ValueError("Debes asociar al menos una editorial a la obra.")
        if cantidad <= 0:
            raise ValueError("La cantidad de ejemplares debe ser mayor a 0.")

        loc_final = id_localizacion if id_localizacion is not None else self.obtener_localizacion_base()
        cursor = self.db.obtener_cursor()
        try:
            sql_obra = """
                INSERT INTO obra
                (isbn, titulo, subtitulo, `año_publicacion`, num_paginas, tipo, categoria)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                sql_obra,
                (
                    obra.isbn,
                    obra.titulo,
                    obra.subtitulo,
                    obra.anio_publicacion,
                    obra.num_paginas,
                    obra.tipo,
                    obra.categoria,
                ),
            )

            for id_autor in dict.fromkeys(obra.autores):
                cursor.execute(
                    "INSERT INTO autor_obra (autor, obra) VALUES (%s, %s)",
                    (id_autor, obra.isbn),
                )

            for id_ed in dict.fromkeys(obra.editoriales):
                cursor.execute(
                    "INSERT INTO obra_editorial (editorial, obra) VALUES (%s, %s)",
                    (id_ed, obra.isbn),
                )

            cursor.execute(
                """
                INSERT INTO abastecimiento_obra (proveedor, obra, fecha_adquisicion, cantidad)
                VALUES (%s, %s, %s, %s)
                """,
                (rfc_proveedor.upper(), obra.isbn, fecha_adquisicion, cantidad),
            )

            for num_ej in range(1, cantidad + 1):
                cursor.execute(
                    "INSERT INTO ejemplar (obra, ejemplar, localizacion) VALUES (%s, %s, %s)",
                    (obra.isbn, num_ej, loc_final),
                )

            self.db.confirmar()
            return (1, cantidad)
        except Error:
            self.db.revertir()
            raise
        finally:
            cursor.close()

    def abastecer_obra_existente(
        self, isbn, rfc_proveedor, fecha_adquisicion, cantidad, id_localizacion=None
    ):
        """Agrega más ejemplares a una obra existente acumulando abastecimiento si se repite proveedor."""
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor a 0.")

        loc_final = id_localizacion if id_localizacion is not None else self.obtener_localizacion_base()
        rfc = rfc_proveedor.upper()
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "SELECT cantidad FROM abastecimiento_obra WHERE proveedor = %s AND obra = %s",
                (rfc, isbn),
            )
            existente = cursor.fetchone()

            if existente:
                cursor.execute(
                    """
                    UPDATE abastecimiento_obra
                    SET cantidad = cantidad + %s, fecha_adquisicion = %s
                    WHERE proveedor = %s AND obra = %s
                    """,
                    (cantidad, fecha_adquisicion, rfc, isbn),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO abastecimiento_obra (proveedor, obra, fecha_adquisicion, cantidad)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (rfc, isbn, fecha_adquisicion, cantidad),
                )

            cursor.execute(
                "SELECT COALESCE(MAX(ejemplar), 0) AS ultimo FROM ejemplar WHERE obra = %s",
                (isbn,),
            )
            ultimo = cursor.fetchone()["ultimo"]
            inicio = ultimo + 1
            fin = ultimo + cantidad

            for num_ej in range(inicio, fin + 1):
                cursor.execute(
                    "INSERT INTO ejemplar (obra, ejemplar, localizacion) VALUES (%s, %s, %s)",
                    (isbn, num_ej, loc_final),
                )

            self.db.confirmar()
            return (inicio, fin)
        except Error:
            self.db.revertir()
            raise
        finally:
            cursor.close()

    def listar_ejemplares_obra(self, isbn):
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT e.obra, e.ejemplar, e.localizacion,
                       l.seccion, l.pasillo, l.estante,
                       CASE
                           WHEN EXISTS (
                               SELECT 1
                               FROM prestamo_ejemplar pe
                               LEFT JOIN devolucion d
                                 ON d.obra = pe.obra
                                AND d.ejemplar = pe.ejemplar
                                AND d.prestamo = pe.prestamo
                               WHERE pe.obra = e.obra
                                 AND pe.ejemplar = e.ejemplar
                                 AND d.id_devolucion IS NULL
                           ) THEN 'Prestado'
                           ELSE 'Disponible'
                       END AS estado
                FROM ejemplar e
                INNER JOIN localizacion l ON e.localizacion = l.id_localizacion
                WHERE e.obra = %s
                ORDER BY e.ejemplar
            """
            cursor.execute(sql, (isbn,))
            return cursor.fetchall()
        finally:
            cursor.close()

    def asignar_localizacion_ejemplar(self, isbn, num_ejemplar, id_localizacion):
        """Actualiza la localización de un ejemplar específico."""
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "UPDATE ejemplar SET localizacion = %s WHERE obra = %s AND ejemplar = %s",
                (id_localizacion, isbn, num_ejemplar),
            )
            afectados = cursor.rowcount
            self.db.confirmar()
            return afectados
        except Error:
            self.db.revertir()
            raise
        finally:
            cursor.close()

    def asignar_localizacion_todos(self, isbn, id_localizacion):
        """Asigna la misma localización a todos los ejemplares de una obra."""
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "UPDATE ejemplar SET localizacion = %s WHERE obra = %s",
                (id_localizacion, isbn),
            )
            afectados = cursor.rowcount
            self.db.confirmar()
            return afectados
        except Error:
            self.db.revertir()
            raise
        finally:
            cursor.close()


class GestorPrestamos(GestorBase):
    """Préstamos, devoluciones y consultas de historial por folio y por fecha."""

    def listar_resumen_disponibles(self):
        """Muestra por cada obra únicamente la cantidad de ejemplares actualmente DISPONIBLES."""
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT o.isbn, o.titulo, COUNT(e.ejemplar) AS disponibles
                FROM ejemplar e
                INNER JOIN obra o ON e.obra = o.isbn
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM prestamo_ejemplar pe
                    LEFT JOIN devolucion d
                      ON d.obra = pe.obra
                     AND d.ejemplar = pe.ejemplar
                     AND d.prestamo = pe.prestamo
                    WHERE pe.obra = e.obra
                      AND pe.ejemplar = e.ejemplar
                      AND d.id_devolucion IS NULL
                )
                GROUP BY o.isbn, o.titulo
                HAVING COUNT(e.ejemplar) > 0
                ORDER BY o.titulo
            """
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()

    def obtener_ejemplares_disponibles_por_isbn(self, isbn):
        """Devuelve la lista de ejemplares disponibles (con su ubicación) para un ISBN específico."""
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT e.obra, o.titulo, e.ejemplar,
                       l.seccion, l.pasillo, l.estante
                FROM ejemplar e
                INNER JOIN obra o ON e.obra = o.isbn
                INNER JOIN localizacion l ON e.localizacion = l.id_localizacion
                WHERE e.obra = %s
                  AND NOT EXISTS (
                      SELECT 1
                      FROM prestamo_ejemplar pe
                      LEFT JOIN devolucion d
                        ON d.obra = pe.obra
                       AND d.ejemplar = pe.ejemplar
                       AND d.prestamo = pe.prestamo
                      WHERE pe.obra = e.obra
                        AND pe.ejemplar = e.ejemplar
                        AND d.id_devolucion IS NULL
                  )
                ORDER BY e.ejemplar
            """
            cursor.execute(sql, (isbn,))
            return cursor.fetchall()
        finally:
            cursor.close()

    def ejemplar_disponible(self, isbn, num_ejemplar):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "SELECT 1 FROM ejemplar WHERE obra = %s AND ejemplar = %s",
                (isbn, num_ejemplar),
            )
            if cursor.fetchone() is None:
                return False

            sql = """
                SELECT 1
                FROM prestamo_ejemplar pe
                LEFT JOIN devolucion d
                  ON d.obra = pe.obra
                 AND d.ejemplar = pe.ejemplar
                 AND d.prestamo = pe.prestamo
                WHERE pe.obra = %s
                  AND pe.ejemplar = %s
                  AND d.id_devolucion IS NULL
            """
            cursor.execute(sql, (isbn, num_ejemplar))
            return cursor.fetchone() is None
        finally:
            cursor.close()

    def registrar_prestamo(self, prestamo):
        """Crea el préstamo (fecha_limite = +14 días) y vincula los ejemplares."""
        if not prestamo.ejemplares:
            raise ValueError("Debes incluir al menos un ejemplar en el préstamo.")

        unicos = list(dict.fromkeys(prestamo.ejemplares))
        for isbn, num_ej in unicos:
            if not self.ejemplar_disponible(isbn, num_ej):
                raise ValueError(
                    f"El ejemplar #{num_ej} de la obra '{isbn}' no existe o ya está prestado."
                )

        cursor = self.db.obtener_cursor()
        try:
            sql_p = """
                INSERT INTO prestamo (fecha_salida, fecha_limite, empleado, usuario)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(
                sql_p,
                (
                    prestamo.fecha_salida,
                    prestamo.fecha_limite,
                    prestamo.empleado,
                    prestamo.usuario,
                ),
            )
            folio = cursor.lastrowid

            sql_pe = """
                INSERT INTO prestamo_ejemplar (obra, ejemplar, prestamo)
                VALUES (%s, %s, %s)
            """
            for isbn, num_ej in unicos:
                cursor.execute(sql_pe, (isbn, num_ej, folio))

            self.db.confirmar()
            return folio
        except Error:
            self.db.revertir()
            raise
        finally:
            cursor.close()

    def listar_todos_prestamos(self):
        """Lista todos los préstamos (activos y finalizados) con total de ejemplares y pendientes."""
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT p.folio, p.fecha_salida, p.fecha_limite,
                       CONCAT_WS(' ', u.nombre_pila, u.primer_ap, u.segundo_ap) AS usuario,
                       COUNT(pe.ejemplar) AS total_ejemplares,
                       SUM(CASE WHEN d.id_devolucion IS NULL THEN 1 ELSE 0 END) AS pendientes
                FROM prestamo p
                INNER JOIN usuario u ON p.usuario = u.id_usuario
                INNER JOIN prestamo_ejemplar pe ON p.folio = pe.prestamo
                LEFT JOIN devolucion d
                  ON d.obra = pe.obra
                 AND d.ejemplar = pe.ejemplar
                 AND d.prestamo = pe.prestamo
                GROUP BY p.folio, p.fecha_salida, p.fecha_limite,
                         u.nombre_pila, u.primer_ap, u.segundo_ap
                ORDER BY p.folio
            """
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()

    def consultar_detalle_prestamo(self, folio):
        """Obtiene la información completa de un préstamo y todos sus ejemplares (devueltos o pendientes)."""
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT p.folio,
                       p.fecha_salida,
                       p.fecha_limite,
                       CONCAT_WS(' ', u.nombre_pila, u.primer_ap, u.segundo_ap) AS usuario,
                       o.isbn,
                       o.titulo,
                       o.subtitulo,
                       pe.ejemplar,
                       d.fecha_devolucion
                FROM prestamo AS p
                INNER JOIN usuario AS u ON p.usuario = u.id_usuario
                INNER JOIN prestamo_ejemplar AS pe ON pe.prestamo = p.folio
                INNER JOIN obra AS o ON pe.obra = o.isbn
                LEFT JOIN devolucion AS d
                  ON d.obra = pe.obra
                 AND d.ejemplar = pe.ejemplar
                 AND d.prestamo = pe.prestamo
                WHERE p.folio = %s
                ORDER BY o.titulo, pe.ejemplar
            """
            cursor.execute(sql, (folio,))
            return cursor.fetchall()
        finally:
            cursor.close()

    def consultar_prestamos_por_fecha(self, fecha):
        """Lista los préstamos realizados en una fecha específica con cantidad de ejemplares y empleado."""
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT p.fecha_salida,
                       p.folio,
                       CONCAT_WS(' ', u.nombre_pila, u.primer_ap, u.segundo_ap) AS usuario,
                       COUNT(pe.ejemplar) AS cantidad_ejemplares,
                       p.fecha_limite,
                       CONCAT_WS(' ', e.nombre_pila, e.primer_ap, e.segundo_ap) AS empleado
                FROM prestamo AS p
                INNER JOIN usuario AS u ON p.usuario = u.id_usuario
                INNER JOIN empleado AS e ON p.empleado = e.id_empleado
                INNER JOIN prestamo_ejemplar AS pe ON pe.prestamo = p.folio
                WHERE p.fecha_salida = %s
                GROUP BY p.fecha_salida,
                         p.folio,
                         u.nombre_pila, u.primer_ap, u.segundo_ap,
                         p.fecha_limite,
                         e.nombre_pila, e.primer_ap, e.segundo_ap
                ORDER BY p.folio
            """
            cursor.execute(sql, (fecha,))
            return cursor.fetchall()
        finally:
            cursor.close()

    def consultar_devoluciones_por_fecha(self, fecha, solo_a_tiempo=True):
        """Lista las devoluciones registradas en una fecha (todas o únicamente entregadas a tiempo)."""
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT d.fecha_devolucion,
                       p.folio,
                       p.fecha_salida,
                       p.fecha_limite,
                       o.isbn,
                       d.ejemplar,
                       o.titulo,
                       o.subtitulo
                FROM devolucion AS d
                INNER JOIN prestamo AS p ON d.prestamo = p.folio
                INNER JOIN obra AS o ON d.obra = o.isbn
                WHERE d.fecha_devolucion = %s
            """
            if solo_a_tiempo:
                sql += " AND d.fecha_devolucion <= p.fecha_limite"
            sql += " ORDER BY p.folio, d.ejemplar"
            cursor.execute(sql, (fecha,))
            return cursor.fetchall()
        finally:
            cursor.close()

    def listar_prestamos_activos_resumen(self):
        """Resumen de préstamos con al menos un ejemplar pendiente de devolución."""
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT p.folio, p.fecha_salida, p.fecha_limite,
                       CONCAT_WS(' ', u.nombre_pila, u.primer_ap, u.segundo_ap) AS usuario,
                       CONCAT_WS(' ', e.nombre_pila, e.primer_ap, e.segundo_ap) AS empleado,
                       COUNT(pe.ejemplar) AS pendientes
                FROM prestamo p
                INNER JOIN usuario u ON p.usuario = u.id_usuario
                INNER JOIN empleado e ON p.empleado = e.id_empleado
                INNER JOIN prestamo_ejemplar pe ON p.folio = pe.prestamo
                LEFT JOIN devolucion d
                  ON d.obra = pe.obra
                 AND d.ejemplar = pe.ejemplar
                 AND d.prestamo = pe.prestamo
                WHERE d.id_devolucion IS NULL
                GROUP BY p.folio, p.fecha_salida, p.fecha_limite,
                         u.nombre_pila, u.primer_ap, u.segundo_ap,
                         e.nombre_pila, e.primer_ap, e.segundo_ap
                ORDER BY p.folio
            """
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()

    def listar_prestamos_activos_detalle(self):
        """Detalle completo de cada ejemplar actualmente prestado."""
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT p.folio, p.fecha_salida, p.fecha_limite,
                       CONCAT_WS(' ', u.nombre_pila, u.primer_ap, u.segundo_ap) AS usuario,
                       pe.obra, o.titulo, pe.ejemplar,
                       CONCAT_WS(' ', e.nombre_pila, e.primer_ap, e.segundo_ap) AS empleado
                FROM prestamo p
                INNER JOIN usuario u ON p.usuario = u.id_usuario
                INNER JOIN empleado e ON p.empleado = e.id_empleado
                INNER JOIN prestamo_ejemplar pe ON p.folio = pe.prestamo
                INNER JOIN obra o ON pe.obra = o.isbn
                LEFT JOIN devolucion d
                  ON d.obra = pe.obra
                 AND d.ejemplar = pe.ejemplar
                 AND d.prestamo = pe.prestamo
                WHERE d.id_devolucion IS NULL
                ORDER BY p.folio, o.titulo, pe.ejemplar
            """
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()

    def listar_ejemplares_pendientes_prestamo(self, folio):
        """Lista los ejemplares aún no devueltos de un folio específico."""
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT pe.prestamo, pe.obra, o.titulo, pe.ejemplar,
                       p.fecha_salida, p.fecha_limite
                FROM prestamo_ejemplar pe
                INNER JOIN prestamo p ON pe.prestamo = p.folio
                INNER JOIN obra o ON pe.obra = o.isbn
                LEFT JOIN devolucion d
                  ON d.obra = pe.obra
                 AND d.ejemplar = pe.ejemplar
                 AND d.prestamo = pe.prestamo
                WHERE pe.prestamo = %s AND d.id_devolucion IS NULL
                ORDER BY pe.obra, pe.ejemplar
            """
            cursor.execute(sql, (folio,))
            return cursor.fetchall()
        finally:
            cursor.close()

    def registrar_devolucion(
        self, folio, isbn, num_ejemplar, fecha_devolucion, id_empleado, monto_dia=TARIFA_MULTA_DIA
    ):
        """Inserta en devolucion y genera automáticamente la multa si hubo retraso."""
        cursor = self.db.obtener_cursor()
        try:
            sql_check = """
                SELECT p.fecha_salida, p.fecha_limite, d.id_devolucion
                FROM prestamo_ejemplar pe
                INNER JOIN prestamo p ON pe.prestamo = p.folio
                LEFT JOIN devolucion d
                  ON d.obra = pe.obra
                 AND d.ejemplar = pe.ejemplar
                 AND d.prestamo = pe.prestamo
                WHERE pe.prestamo = %s AND pe.obra = %s AND pe.ejemplar = %s
            """
            cursor.execute(sql_check, (folio, isbn, num_ejemplar))
            fila = cursor.fetchone()

            if not fila:
                raise ValueError("No se encontró ese ejemplar dentro del préstamo indicado.")
            if fila["id_devolucion"] is not None:
                raise ValueError("Ese ejemplar ya fue devuelto anteriormente.")
            if fecha_devolucion < fila["fecha_salida"]:
                raise ValueError("La fecha de devolución no puede ser anterior a la fecha de salida.")

            sql_dev = """
                INSERT INTO devolucion (fecha_devolucion, empleado, obra, ejemplar, prestamo)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql_dev, (fecha_devolucion, id_empleado, isbn, num_ejemplar, folio))
            id_devolucion = cursor.lastrowid

            diferencia = (fecha_devolucion - fila["fecha_limite"]).days
            id_multa = None
            total_multa = Decimal("0.00")

            if diferencia > 0:
                tarifa = Decimal(str(monto_dia)).quantize(Decimal("0.01"))
                total_multa = (tarifa * diferencia).quantize(Decimal("0.01"))
                sql_multa = """
                    INSERT INTO multa (devolucion, estado, monto_dia, dias_retraso, total)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(
                    sql_multa,
                    (id_devolucion, "Pendiente", tarifa, diferencia, total_multa),
                )
                id_multa = cursor.lastrowid

            self.db.confirmar()
            return {
                "id_devolucion": id_devolucion,
                "fecha_limite": fila["fecha_limite"],
                "dias_retraso": diferencia if diferencia > 0 else 0,
                "con_retraso": diferencia > 0,
                "id_multa": id_multa,
                "monto_dia": Decimal(str(monto_dia)).quantize(Decimal("0.01")),
                "total": total_multa,
            }
        except Error:
            self.db.revertir()
            raise
        finally:
            cursor.close()


class GestorMultas(GestorBase):
    """Sincronización automática, consulta detallada y pago de multas (entidad débil: columna multa)."""

    def generar_multas_automaticas(self, monto_dia=TARIFA_MULTA_DIA):
        """Genera automáticamente multas faltantes para devoluciones tardías sin multa."""
        cursor = self.db.obtener_cursor()
        try:
            sql_pend = """
                SELECT d.id_devolucion, d.prestamo, d.obra, d.ejemplar,
                       DATEDIFF(d.fecha_devolucion, p.fecha_limite) AS dias_retraso
                FROM devolucion d
                INNER JOIN prestamo p ON d.prestamo = p.folio
                LEFT JOIN multa m ON m.devolucion = d.id_devolucion
                WHERE d.fecha_devolucion > p.fecha_limite
                  AND m.multa IS NULL
                ORDER BY d.id_devolucion
            """
            cursor.execute(sql_pend)
            pendientes = cursor.fetchall()

            creadas = []
            tarifa = Decimal(str(monto_dia)).quantize(Decimal("0.01"))
            for item in pendientes:
                dias = item["dias_retraso"]
                total = (tarifa * dias).quantize(Decimal("0.01"))
                cursor.execute(
                    """
                    INSERT INTO multa (devolucion, estado, monto_dia, dias_retraso, total)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (item["id_devolucion"], "Pendiente", tarifa, dias, total),
                )
                creadas.append(
                    {
                        "id_multa": cursor.lastrowid,
                        "prestamo": item["prestamo"],
                        "obra": item["obra"],
                        "ejemplar": item["ejemplar"],
                        "dias_retraso": dias,
                        "total": total,
                    }
                )

            self.db.confirmar()
            return creadas
        except Error:
            self.db.revertir()
            raise
        finally:
            cursor.close()

    def listar_multas(self, solo_pendientes=False):
        """Lista el historial de multas con resumen compacto."""
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT m.multa AS id_multa,
                       d.prestamo,
                       p.fecha_salida,
                       CONCAT_WS(' ', u.nombre_pila, u.primer_ap, u.segundo_ap) AS usuario,
                       d.obra,
                       o.titulo,
                       o.subtitulo,
                       d.ejemplar,
                       p.fecha_limite,
                       d.fecha_devolucion,
                       m.dias_retraso,
                       m.monto_dia,
                       m.total,
                       m.estado
                FROM multa AS m
                INNER JOIN devolucion AS d ON m.devolucion = d.id_devolucion
                INNER JOIN prestamo AS p ON d.prestamo = p.folio
                INNER JOIN usuario AS u ON p.usuario = u.id_usuario
                INNER JOIN obra AS o ON d.obra = o.isbn
            """
            if solo_pendientes:
                sql += " WHERE m.estado = 'Pendiente'"
            sql += " ORDER BY m.multa"
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()

    def consultar_detalle_multa(self, id_multa):
        """Obtiene los 13 datos completos de una multa generada (más su estado)."""
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT m.multa AS id_multa,
                       p.folio AS prestamo,
                       p.fecha_salida,
                       CONCAT_WS(' ', u.nombre_pila, u.primer_ap, u.segundo_ap) AS usuario,
                       o.isbn,
                       o.titulo,
                       o.subtitulo,
                       d.ejemplar,
                       p.fecha_limite,
                       d.fecha_devolucion,
                       m.dias_retraso,
                       m.monto_dia,
                       m.total,
                       m.estado
                FROM multa AS m
                INNER JOIN devolucion AS d ON m.devolucion = d.id_devolucion
                INNER JOIN prestamo AS p ON d.prestamo = p.folio
                INNER JOIN usuario AS u ON p.usuario = u.id_usuario
                INNER JOIN obra AS o ON d.obra = o.isbn
                WHERE m.multa = %s
            """
            cursor.execute(sql, (id_multa,))
            return cursor.fetchone()
        finally:
            cursor.close()

    def obtener_multa(self, id_multa):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "SELECT multa AS id_multa, devolucion, estado, total FROM multa WHERE multa = %s",
                (id_multa,),
            )
            return cursor.fetchone()
        finally:
            cursor.close()

    def marcar_pagada(self, id_multa):
        """Marca una multa pendiente como 'Pagada' usando únicamente su número de multa."""
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "UPDATE multa SET estado = 'Pagada' WHERE multa = %s AND estado = 'Pendiente'",
                (id_multa,),
            )
            afectados = cursor.rowcount
            self.db.confirmar()
            return afectados
        except Error:
            self.db.revertir()
            raise
        finally:
            cursor.close()