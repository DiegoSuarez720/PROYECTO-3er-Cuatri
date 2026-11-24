"""Consultas SQL de préstamos (Opción 3; también alimenta Opción 7).

ÍNDICE (opción del menú -> método):
  [OPCIÓN 3 -> 1 | OPCIÓN 7 -> 2]  ->  listar_resumen_disponibles()
  [OPCIÓN 3 -> 1]  ->  obtener_ejemplares_disponibles_por_isbn()
  [OPCIÓN 3 -> 1]  ->  ejemplar_disponible()
  [OPCIÓN 3 -> 1]  ->  registrar_prestamo()
  [OPCIÓN 3 -> 2]  ->  listar_todos_prestamos()
  [OPCIÓN 3 -> 2]  ->  consultar_detalle_prestamo()
  [OPCIÓN 3 -> 3]  ->  listar_fechas_prestamos()
  [OPCIÓN 3 -> 3]  ->  consultar_prestamos_por_fecha()
  [OPCIÓN 7 -> 3]  ->  listar_prestamos_activos_detalle()
"""

from datetime import date, timedelta
from mysql.connector import Error

from nucleo.conexion import GestorBase
from nucleo.utilidades import formatear_fecha


class GestorPrestamos(GestorBase):
    """Préstamos, devoluciones y consultas de historial por folio y por fecha."""

    # [OPCIÓN 3 -> 1 | OPCIÓN 7 -> 2]
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

    # [OPCIÓN 3 -> 1]
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

    # [OPCIÓN 3 -> 1]
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

    # [OPCIÓN 3 -> 1]
    def registrar_prestamo(self, prestamo):
        """Crea el préstamo (fecha_limite = +14 días) validando fechas y disponibilidad."""
        hoy = date.today()
        if prestamo.fecha_salida > hoy:
            raise ValueError("La fecha de salida del préstamo no puede ser futura.")
        if prestamo.fecha_salida < hoy - timedelta(days=365):
            raise ValueError("La fecha de salida no puede tener más de 1 año de antigüedad.")
        if not prestamo.ejemplares:
            raise ValueError("Debes incluir al menos un ejemplar en el préstamo.")

        unicos = list(dict.fromkeys(prestamo.ejemplares))
        cursor_check = self.db.obtener_cursor()
        try:
            for isbn, num_ej in unicos:
                if not self.ejemplar_disponible(isbn, num_ej):
                    raise ValueError(
                        f"El ejemplar #{num_ej} de la obra '{isbn}' no existe o ya está prestado."
                    )
                cursor_check.execute(
                    "SELECT MIN(fecha_adquisicion) AS fecha_adq FROM abastecimiento_obra WHERE obra = %s",
                    (isbn,),
                )
                fila_adq = cursor_check.fetchone()
                if fila_adq and fila_adq["fecha_adq"] and prestamo.fecha_salida < fila_adq["fecha_adq"]:
                    raise ValueError(
                        f"La obra '{isbn}' se adquirió el {formatear_fecha(fila_adq['fecha_adq'])}; "
                        f"no puede prestarse con fecha anterior ({formatear_fecha(prestamo.fecha_salida)})."
                    )
        finally:
            cursor_check.close()

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

    # [OPCIÓN 3 -> 2]
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

    # [OPCIÓN 3 -> 2]
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

    # [OPCIÓN 3 -> 3]
    def listar_fechas_prestamos(self):
        """Lista las fechas en las que existen préstamos registrados y su conteo."""
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT p.fecha_salida,
                       COUNT(DISTINCT p.folio) AS total_prestamos,
                       COUNT(pe.ejemplar) AS total_ejemplares
                FROM prestamo AS p
                INNER JOIN prestamo_ejemplar AS pe ON pe.prestamo = p.folio
                GROUP BY p.fecha_salida
                ORDER BY p.fecha_salida DESC
            """
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()

    # [OPCIÓN 3 -> 3]
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

    # [OPCIÓN 7 -> 3]
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
