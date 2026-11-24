"""Consultas SQL de devoluciones (Opción 4).

ÍNDICE (opción del menú -> método):
  [OPCIÓN 4 -> 1]  ->  listar_prestamos_activos_resumen()
  [OPCIÓN 4 -> 1]  ->  listar_ejemplares_pendientes_prestamo()
  [OPCIÓN 4 -> 1]  ->  registrar_devolucion()
  [OPCIÓN 4 -> 2]  ->  listar_fechas_devoluciones()
  [OPCIÓN 4 -> 2]  ->  consultar_devoluciones_por_fecha()
"""

from datetime import date
from decimal import Decimal
from mysql.connector import Error

from nucleo.conexion import GestorBase
from prestamos_y_multas.multas_sql import TARIFA_MULTA_DIA


class GestorDevoluciones(GestorBase):
    """Registro y consulta de devoluciones de ejemplares (genera multa automática si hay retraso)."""

    # [OPCIÓN 4 -> 1]
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

    # [OPCIÓN 4 -> 1]
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

    # [OPCIÓN 4 -> 1]
    def registrar_devolucion(
        self, folio, isbn, num_ejemplar, fecha_devolucion, id_empleado, monto_dia=TARIFA_MULTA_DIA
    ):
        """Inserta en devolucion validando fechas y genera automáticamente multa si hubo retraso."""
        if fecha_devolucion > date.today():
            raise ValueError("La fecha de devolución no puede ser futura.")

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

    # [OPCIÓN 4 -> 2]
    def listar_fechas_devoluciones(self):
        """Lista las fechas en las que existen devoluciones, separando a tiempo y con retraso."""
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT d.fecha_devolucion,
                       COUNT(*) AS total,
                       SUM(CASE WHEN d.fecha_devolucion <= p.fecha_limite THEN 1 ELSE 0 END) AS a_tiempo,
                       SUM(CASE WHEN d.fecha_devolucion > p.fecha_limite THEN 1 ELSE 0 END) AS con_retraso
                FROM devolucion AS d
                INNER JOIN prestamo AS p ON d.prestamo = p.folio
                GROUP BY d.fecha_devolucion
                ORDER BY d.fecha_devolucion DESC
            """
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()

    # [OPCIÓN 4 -> 2]
    def consultar_devoluciones_por_fecha(self, fecha, filtro="a_tiempo"):
        """Lista las devoluciones registradas en una fecha ('a_tiempo', 'retraso' o 'todas')."""
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
            if filtro == "a_tiempo":
                sql += " AND d.fecha_devolucion <= p.fecha_limite"
            elif filtro == "retraso":
                sql += " AND d.fecha_devolucion > p.fecha_limite"
            sql += " ORDER BY p.folio, d.ejemplar"
            cursor.execute(sql, (fecha,))
            return cursor.fetchall()
        finally:
            cursor.close()
