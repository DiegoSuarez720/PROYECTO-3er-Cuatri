"""Consultas SQL de multas (Opción 5; también alimenta Opciones 3 y 7).

ÍNDICE (opción del menú -> método):
  [OPCIÓN 3 -> 1]  ->  contar_multas_pendientes_usuario()
  [OPCIÓN 5 -> 1]  ->  generar_multas_automaticas()
  [OPCIÓN 5 -> 2 | OPCIÓN 5 -> 3 | OPCIÓN 7 -> 4]  ->  listar_multas()
  [OPCIÓN 5 -> 3]  ->  consultar_detalle_multa()
  [OPCIÓN 5 -> 2]  ->  obtener_multa()
  [OPCIÓN 5 -> 2]  ->  marcar_pagada()
"""

from decimal import Decimal
from mysql.connector import Error

from nucleo.conexion import GestorBase


# Tarifa fija diaria por retraso en devolución
TARIFA_MULTA_DIA = Decimal("15.00")


class GestorMultas(GestorBase):
    """Sincronización automática, consulta detallada y pago de multas (entidad débil: columna multa)."""

    # [OPCIÓN 3 -> 1]
    def contar_multas_pendientes_usuario(self, id_usuario):
        """Devuelve (cantidad, monto_total) de multas pendientes de un usuario."""
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT COUNT(*) AS cantidad, COALESCE(SUM(m.total), 0) AS total
                FROM multa AS m
                INNER JOIN devolucion AS d ON m.devolucion = d.id_devolucion
                INNER JOIN prestamo AS p ON d.prestamo = p.folio
                WHERE p.usuario = %s AND m.estado = 'Pendiente'
            """
            cursor.execute(sql, (id_usuario,))
            fila = cursor.fetchone()
            return (fila["cantidad"], fila["total"]) if fila else (0, Decimal("0.00"))
        finally:
            cursor.close()

    # [OPCIÓN 5 -> 1]
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

    # [OPCIÓN 5 -> 2 | OPCIÓN 5 -> 3 | OPCIÓN 7 -> 4]
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

    # [OPCIÓN 5 -> 3]
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

    # [OPCIÓN 5 -> 2]
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

    # [OPCIÓN 5 -> 2]
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
