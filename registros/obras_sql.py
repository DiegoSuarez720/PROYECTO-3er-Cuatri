"""Consultas SQL de obras, ejemplares y localización (Opciones 1 y 2; también alimenta 3 y 7).

ÍNDICE (opción del menú -> método):
  [OPCIÓN 1 -> 2 | OPCIÓN 1 -> 3 | OPCIÓN 2 | OPCIÓN 7 -> 1]  ->  listar_obras()
  [OPCIÓN 1 -> 2]  ->  obtener_obra()
  [OPCIÓN 3 -> 1]  ->  obtener_fecha_primera_adquisicion()
  [OPCIÓN 1 -> 3]  ->  consultar_obra_completa()
  [OPCIÓN 1 -> 1 | OPCIÓN 3 -> 1]  ->  existe_obra()
  [OPCIÓN 1 -> 1 | OPCIÓN 1 -> 2]  ->  obtener_localizacion_base()
  [OPCIÓN 1 -> 1]  ->  registrar_obra_completa()
  [OPCIÓN 1 -> 2]  ->  abastecer_obra_existente()
  [OPCIÓN 2]  ->  listar_ejemplares_obra()
  [OPCIÓN 2]  ->  asignar_localizacion_ejemplar()
  [OPCIÓN 2]  ->  asignar_localizacion_todos()
"""

from datetime import date
from mysql.connector import Error

from nucleo.conexion import GestorBase
from nucleo.utilidades import formatear_fecha


class GestorObras(GestorBase):
    """Obras, abastecimiento, ejemplares, localizaciones y ficha completa de obra."""

    # [OPCIÓN 1 -> 2 | OPCIÓN 1 -> 3 | OPCIÓN 2 | OPCIÓN 7 -> 1]
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

    # [OPCIÓN 1 -> 2]
    def obtener_obra(self, isbn):
        """Obtiene datos básicos de una obra (incluyendo su año de publicación)."""
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "SELECT isbn, titulo, `año_publicacion` AS anio FROM obra WHERE isbn = %s",
                (isbn,),
            )
            return cursor.fetchone()
        finally:
            cursor.close()

    # [OPCIÓN 3 -> 1]
    def obtener_fecha_primera_adquisicion(self, isbn):
        """Devuelve la fecha más antigua en que se adquirió la obra."""
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "SELECT MIN(fecha_adquisicion) AS primera_fecha FROM abastecimiento_obra WHERE obra = %s",
                (isbn,),
            )
            fila = cursor.fetchone()
            return fila["primera_fecha"] if fila else None
        finally:
            cursor.close()

    # [OPCIÓN 1 -> 3]
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

    # [OPCIÓN 1 -> 1 | OPCIÓN 3 -> 1]
    def existe_obra(self, isbn):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT 1 FROM obra WHERE isbn = %s", (isbn,))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    # [OPCIÓN 1 -> 1 | OPCIÓN 1 -> 2]
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

    # [OPCIÓN 1 -> 1]
    def registrar_obra_completa(
        self, obra, rfc_proveedor, fecha_adquisicion, cantidad, id_localizacion=None
    ):
        """Inserta obra, autores, editoriales, abastecimiento y N ejemplares validando fechas y rangos."""
        hoy = date.today()
        if obra.anio_publicacion < 1450 or obra.anio_publicacion > hoy.year:
            raise ValueError(f"El año de publicación debe estar entre 1450 y {hoy.year}.")
        if obra.num_paginas <= 0 or obra.num_paginas > 10000:
            raise ValueError("El número de páginas debe estar entre 1 y 10,000.")
        if fecha_adquisicion > hoy:
            raise ValueError("La fecha de adquisición no puede ser futura.")
        if fecha_adquisicion.year < obra.anio_publicacion:
            raise ValueError(
                f"La fecha de adquisición ({formatear_fecha(fecha_adquisicion)}) no puede ser "
                f"anterior al año de publicación ({obra.anio_publicacion})."
            )
        if not obra.autores:
            raise ValueError("Debes asociar al menos un autor a la obra.")
        if not obra.editoriales:
            raise ValueError("Debes asociar al menos una editorial a la obra.")
        if cantidad <= 0 or cantidad > 500:
            raise ValueError("La cantidad de ejemplares debe estar entre 1 y 500.")

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

    # [OPCIÓN 1 -> 2]
    def abastecer_obra_existente(
        self, isbn, rfc_proveedor, fecha_adquisicion, cantidad, id_localizacion=None
    ):
        """Agrega más ejemplares a una obra existente validando fecha contra publicación y hoy."""
        hoy = date.today()
        if cantidad <= 0 or cantidad > 500:
            raise ValueError("La cantidad debe estar entre 1 y 500 ejemplares.")
        if fecha_adquisicion > hoy:
            raise ValueError("La fecha de adquisición no puede ser futura.")

        obra_bd = self.obtener_obra(isbn)
        if not obra_bd:
            raise ValueError("La obra especificada no existe.")
        if fecha_adquisicion.year < obra_bd["anio"]:
            raise ValueError(
                f"La fecha de adquisición no puede ser anterior al año de publicación ({obra_bd['anio']})."
            )

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

    # [OPCIÓN 2]
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

    # [OPCIÓN 2]
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

    # [OPCIÓN 2]
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
