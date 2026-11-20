"""Clases gestoras con lógica de negocio y consultas SQL parametrizadas para las 19 tablas."""

from mysql.connector import Error
from conexion import ConexionDB
from modelos import Empleado


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
    """Altas y listados de los catálogos auxiliares."""

    # --- PAISES ---
    def listar_paises(self):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT clave, nombre FROM pais ORDER BY clave")
            return cursor.fetchall()
        finally:
            cursor.close()

    def crear_pais(self, pais):
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

    def crear_tipo(self, tipo):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "INSERT INTO tipo (tipo_obra) VALUES (%s)",
                (tipo.tipo_obra,),
            )
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

    def crear_categoria(self, categoria):
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
            sql = """
                SELECT num_id, nombre_pila, primer_ap, segundo_ap
                FROM autor
                ORDER BY num_id
            """
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()

    def crear_autor(self, autor):
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                INSERT INTO autor (nombre_pila, primer_ap, segundo_ap)
                VALUES (%s, %s, %s)
            """
            cursor.execute(sql, (autor.nombre_pila, autor.primer_ap, autor.segundo_ap))
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

    def crear_editorial(self, editorial):
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

    def crear_proveedor(self, proveedor):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "INSERT INTO proveedor (RFC, nombre_empresa) VALUES (%s, %s)",
                (proveedor.rfc, proveedor.nombre_empresa),
            )
            for tel in proveedor.telefonos:
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
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "INSERT INTO telefono_proveedor (telefono, proveedor) VALUES (%s, %s)",
                (telefono, rfc.upper()),
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

    def crear_localizacion(self, loc):
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

    def crear_usuario(self, usuario):
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

            for tel in usuario.telefonos:
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
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "INSERT INTO telefono_usuario (num_tel, usuario) VALUES (%s, %s)",
                (num_tel, id_usuario),
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

    def crear_empleado(self, empleado):
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
    """Registro 1 (Obra completa + abastecimiento + ejemplares) y Registro 2 (Localización)."""

    def listar_obras(self):
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT o.isbn, o.titulo, o.subtitulo, o.`año_publicacion` AS anio,
                       t.tipo_obra, c.genero,
                       COUNT(e.ejemplar) AS total_ejemplares
                FROM obra o
                INNER JOIN tipo t ON o.tipo = t.id_tipo
                INNER JOIN categoria c ON o.categoria = c.codigo
                LEFT JOIN ejemplar e ON o.isbn = e.obra
                GROUP BY o.isbn, o.titulo, o.subtitulo, o.`año_publicacion`,
                         t.tipo_obra, c.genero
                ORDER BY o.titulo
            """
            cursor.execute(sql)
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
        """Obtiene el primer id_localizacion disponible (por defecto la localización base)."""
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT MIN(id_localizacion) AS id_loc FROM localizacion")
            fila = cursor.fetchone()
            if not fila or fila["id_loc"] is None:
                raise ValueError(
                    "No existe ninguna localización en la base de datos. "
                    "Registra primero una localización (o inserta la base 'Sin asignar')."
                )
            return fila["id_loc"]
        finally:
            cursor.close()

    def registrar_obra_completa(
        self, obra, rfc_proveedor, fecha_adquisicion, cantidad, id_localizacion=None
    ):
        """Registro 1: Inserta obra, autores, editoriales, abastecimiento y N ejemplares."""
        if not obra.autores:
            raise ValueError("Debes asociar al menos un autor a la obra.")
        if not obra.editoriales:
            raise ValueError("Debes asociar al menos una editorial a la obra.")
        if cantidad <= 0:
            raise ValueError("La cantidad de ejemplares debe ser mayor a 0.")

        loc_final = id_localizacion if id_localizacion is not None else self.obtener_localizacion_base()
        cursor = self.db.obtener_cursor()
        try:
            # 1. Insertar la obra
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

            # 2. Asociar autores (sin duplicados)
            for id_autor in dict.fromkeys(obra.autores):
                cursor.execute(
                    "INSERT INTO autor_obra (autor, obra) VALUES (%s, %s)",
                    (id_autor, obra.isbn),
                )

            # 3. Asociar editoriales (sin duplicados)
            for id_ed in dict.fromkeys(obra.editoriales):
                cursor.execute(
                    "INSERT INTO obra_editorial (editorial, obra) VALUES (%s, %s)",
                    (id_ed, obra.isbn),
                )

            # 4. Registrar abastecimiento
            sql_abast = """
                INSERT INTO abastecimiento_obra (proveedor, obra, fecha_adquisicion, cantidad)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql_abast, (rfc_proveedor.upper(), obra.isbn, fecha_adquisicion, cantidad))

            # 5. Generar N ejemplares consecutivos (1..cantidad)
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
        """Agrega más ejemplares a una obra ya existente acumulando abastecimiento si se repite proveedor."""
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor a 0.")

        loc_final = id_localizacion if id_localizacion is not None else self.obtener_localizacion_base()
        rfc = rfc_proveedor.upper()
        cursor = self.db.obtener_cursor()
        try:
            # Revisar si (proveedor, obra) ya existe por la PK compuesta
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
                               SELECT 1 FROM prestamo_ejemplar pe
                               WHERE pe.obra = e.obra
                                 AND pe.ejemplar = e.ejemplar
                                 AND pe.fecha_devolucion IS NULL
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
        """Registro 2: Actualiza la localización de un ejemplar específico."""
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
        """Registro 2 (lote): Asigna la misma localización a todos los ejemplares de una obra."""
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
    """Registro 3 (Préstamo de ejemplares) y Registro 4 (Devolución de ejemplares)."""

    def listar_ejemplares_disponibles(self, isbn=None):
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT e.obra, o.titulo, e.ejemplar,
                       l.seccion, l.pasillo, l.estante
                FROM ejemplar e
                INNER JOIN obra o ON e.obra = o.isbn
                INNER JOIN localizacion l ON e.localizacion = l.id_localizacion
                WHERE NOT EXISTS (
                    SELECT 1 FROM prestamo_ejemplar pe
                    WHERE pe.obra = e.obra
                      AND pe.ejemplar = e.ejemplar
                      AND pe.fecha_devolucion IS NULL
                )
            """
            params = []
            if isbn:
                sql += " AND e.obra = %s"
                params.append(isbn)
            sql += " ORDER BY o.titulo, e.ejemplar"
            cursor.execute(sql, tuple(params))
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

            cursor.execute(
                """
                SELECT 1 FROM prestamo_ejemplar
                WHERE obra = %s AND ejemplar = %s AND fecha_devolucion IS NULL
                """,
                (isbn, num_ejemplar),
            )
            return cursor.fetchone() is None
        finally:
            cursor.close()

    def registrar_prestamo(self, prestamo):
        """Registro 3: Crea el préstamo y asocia los ejemplares disponibles."""
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
                INSERT INTO prestamo_ejemplar (obra, ejemplar, prestamo, fecha_devolucion)
                VALUES (%s, %s, %s, NULL)
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

    def listar_prestamos_activos(self, id_usuario=None):
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT p.folio, p.fecha_salida, p.fecha_limite,
                       u.id_usuario,
                       CONCAT_WS(' ', u.nombre_pila, u.primer_ap, u.segundo_ap) AS usuario,
                       CONCAT_WS(' ', e.nombre_pila, e.primer_ap, e.segundo_ap) AS empleado,
                       COUNT(pe.ejemplar) AS pendientes
                FROM prestamo p
                INNER JOIN usuario u ON p.usuario = u.id_usuario
                INNER JOIN empleado e ON p.empleado = e.id_empleado
                INNER JOIN prestamo_ejemplar pe ON p.folio = pe.prestamo
                WHERE pe.fecha_devolucion IS NULL
            """
            params = []
            if id_usuario is not None:
                sql += " AND p.usuario = %s"
                params.append(id_usuario)

            sql += """
                GROUP BY p.folio, p.fecha_salida, p.fecha_limite, u.id_usuario,
                         u.nombre_pila, u.primer_ap, u.segundo_ap,
                         e.nombre_pila, e.primer_ap, e.segundo_ap
                ORDER BY p.folio
            """
            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
        finally:
            cursor.close()

    def listar_ejemplares_pendientes_prestamo(self, folio):
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT pe.prestamo, pe.obra, o.titulo, pe.ejemplar,
                       p.fecha_salida, p.fecha_limite
                FROM prestamo_ejemplar pe
                INNER JOIN prestamo p ON pe.prestamo = p.folio
                INNER JOIN obra o ON pe.obra = o.isbn
                WHERE pe.prestamo = %s AND pe.fecha_devolucion IS NULL
                ORDER BY pe.obra, pe.ejemplar
            """
            cursor.execute(sql, (folio,))
            return cursor.fetchall()
        finally:
            cursor.close()

    def registrar_devolucion(self, folio, isbn, num_ejemplar, fecha_devolucion):
        """Registro 4: Guarda fecha_devolucion y calcula si hubo retraso."""
        cursor = self.db.obtener_cursor()
        try:
            sql_check = """
                SELECT p.fecha_salida, p.fecha_limite, pe.fecha_devolucion
                FROM prestamo_ejemplar pe
                INNER JOIN prestamo p ON pe.prestamo = p.folio
                WHERE pe.prestamo = %s AND pe.obra = %s AND pe.ejemplar = %s
            """
            cursor.execute(sql_check, (folio, isbn, num_ejemplar))
            fila = cursor.fetchone()

            if not fila:
                raise ValueError("No se encontró ese ejemplar dentro del préstamo indicado.")
            if fila["fecha_devolucion"] is not None:
                raise ValueError("Ese ejemplar ya fue devuelto anteriormente.")
            if fecha_devolucion < fila["fecha_salida"]:
                raise ValueError("La fecha de devolución no puede ser anterior a la fecha de salida.")

            cursor.execute(
                """
                UPDATE prestamo_ejemplar
                SET fecha_devolucion = %s
                WHERE prestamo = %s AND obra = %s AND ejemplar = %s
                """,
                (fecha_devolucion, folio, isbn, num_ejemplar),
            )
            self.db.confirmar()

            diferencia = (fecha_devolucion - fila["fecha_limite"]).days
            return {
                "fecha_limite": fila["fecha_limite"],
                "dias_retraso": diferencia if diferencia > 0 else 0,
                "con_retraso": diferencia > 0,
            }
        except Error:
            self.db.revertir()
            raise
        finally:
            cursor.close()


class GestorMultas(GestorBase):
    """Registro 5: Generación y cobro de multas por devoluciones tardías."""

    def listar_devoluciones_tardias(self):
        """Muestra entregas donde fecha_devolucion > fecha_limite para facilitar el alta de multas."""
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT p.folio,
                       CONCAT_WS(' ', u.nombre_pila, u.primer_ap, u.segundo_ap) AS usuario,
                       pe.obra, o.titulo, pe.ejemplar,
                       p.fecha_limite, pe.fecha_devolucion,
                       DATEDIFF(pe.fecha_devolucion, p.fecha_limite) AS dias_retraso,
                       (SELECT COUNT(*) FROM multa m WHERE m.prestamo = p.folio) AS multas_registradas
                FROM prestamo_ejemplar pe
                INNER JOIN prestamo p ON pe.prestamo = p.folio
                INNER JOIN usuario u ON p.usuario = u.id_usuario
                INNER JOIN obra o ON pe.obra = o.isbn
                WHERE pe.fecha_devolucion IS NOT NULL
                  AND pe.fecha_devolucion > p.fecha_limite
                ORDER BY p.folio, pe.obra, pe.ejemplar
            """
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()

    def registrar_multa(self, multa):
        """Registro 5: Inserta una multa con estado explícito ('Pendiente' por defecto)."""
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                INSERT INTO multa (prestamo, estado, monto_dia, dias_retraso, total)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(
                sql,
                (
                    multa.prestamo,
                    multa.estado,
                    multa.monto_dia,
                    multa.dias_retraso,
                    multa.total,
                ),
            )
            num_multa = cursor.lastrowid
            self.db.confirmar()
            return num_multa
        except Error:
            self.db.revertir()
            raise
        finally:
            cursor.close()

    def listar_multas(self, solo_pendientes=False):
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT m.multa, m.prestamo,
                       CONCAT_WS(' ', u.nombre_pila, u.primer_ap, u.segundo_ap) AS usuario,
                       m.dias_retraso, m.monto_dia, m.total, m.estado
                FROM multa m
                INNER JOIN prestamo p ON m.prestamo = p.folio
                INNER JOIN usuario u ON p.usuario = u.id_usuario
            """
            if solo_pendientes:
                sql += " WHERE m.estado = 'Pendiente'"
            sql += " ORDER BY m.multa"
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()

    def marcar_pagada(self, num_multa, folio_prestamo):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "UPDATE multa SET estado = 'Pagada' WHERE multa = %s AND prestamo = %s",
                (num_multa, folio_prestamo),
            )
            afectados = cursor.rowcount
            self.db.confirmar()
            return afectados
        except Error:
            self.db.revertir()
            raise
        finally:
            cursor.close()