# En este archivo se ven las consultas SQL de multas (opcion 5 del menu;
# tambien se usan en las opciones 3 y 7).
#
# INDICE (opcion del menu -> metodo):
#   [OPCION 3 -> 1]  ->  contar_multas_pendientes_usuario()
#   [OPCION 5 -> 1]  ->  generar_multas_automaticas()
#   [OPCION 5 -> 2 | OPCION 5 -> 3 | OPCION 7 -> 4]  ->  listar_multas()
#   [OPCION 5 -> 3]  ->  consultar_detalle_multa()
#   [OPCION 5 -> 2]  ->  obtener_multa()
#   [OPCION 5 -> 2]  ->  marcar_pagada()

from decimal import Decimal
from mysql.connector import Error

from nucleo.conexion import GestorBase

# IMPORTANTE
# Cobro fijo por cada dia de retraso
TARIFA_MULTA_DIA = Decimal("15.00")


class GestorMultas(GestorBase):
    # Esta clase crea multas, las consulta y las marca como pagadas.

    # [OPCION 3 -> 1]
    def contar_multas_pendientes_usuario(self, id_usuario):
        # Regresa (cantidad, monto_total) de multas pendientes de un usuario
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT COUNT(*) AS cantidad, IFNULL(SUM(mul.total), 0) AS total
                FROM multa AS mul
                INNER JOIN devolucion AS dev ON mul.devolucion = dev.id_devolucion
                INNER JOIN prestamo AS pres ON dev.prestamo = pres.folio
                WHERE pres.usuario = %s AND mul.estado = 'Pendiente'
            """
            cursor.execute(sql, (id_usuario,))
            fila = cursor.fetchone()
            return (fila["cantidad"], fila["total"]) if fila else (0, Decimal("0.00"))
        finally:
            cursor.close()

    # [OPCION 5 -> 1]
    def generar_multas_automaticas(self, monto_dia=TARIFA_MULTA_DIA):
        # Crea las multas que faltan para devoluciones con retraso
        cursor = self.db.obtener_cursor()
        try:
            # Devoluciones hechas despues de la fecha limite
            sql_tarde = """
                SELECT dev.id_devolucion, dev.prestamo, dev.obra, dev.ejemplar,
                       dev.fecha_devolucion, pres.fecha_limite
                FROM devolucion AS dev
                INNER JOIN prestamo AS pres ON dev.prestamo = pres.folio
                WHERE dev.fecha_devolucion > pres.fecha_limite
                ORDER BY dev.id_devolucion
            """
            cursor.execute(sql_tarde)
            tardias = cursor.fetchall()

            # Devoluciones que ya tienen multa
            cursor.execute("SELECT devolucion FROM multa")
            con_multa = set(f["devolucion"] for f in cursor.fetchall())

            pendientes = [d for d in tardias if d["id_devolucion"] not in con_multa]

            creadas = []
            tarifa = Decimal(str(monto_dia)).quantize(Decimal("0.01"))
            for item in pendientes:
                dias = (item["fecha_devolucion"] - item["fecha_limite"]).days
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

    # [OPCION 5 -> 2 | OPCION 5 -> 3 | OPCION 7 -> 4]
    def listar_multas(self, solo_pendientes=False):
        # Lista de multas con un resumen corto
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT mul.multa AS id_multa,
                       dev.prestamo,
                       pres.fecha_salida,
                       CONCAT(us.nombre_pila, ' ', us.primer_ap, ' ', IFNULL(us.segundo_ap, '')) AS usuario,
                       dev.obra,
                       ob.titulo,
                       ob.subtitulo,
                       dev.ejemplar,
                       pres.fecha_limite,
                       dev.fecha_devolucion,
                       mul.dias_retraso,
                       mul.monto_dia,
                       mul.total,
                       mul.estado
                FROM multa AS mul
                INNER JOIN devolucion AS dev ON mul.devolucion = dev.id_devolucion
                INNER JOIN prestamo AS pres ON dev.prestamo = pres.folio
                INNER JOIN usuario AS us ON pres.usuario = us.id_usuario
                INNER JOIN obra AS ob ON dev.obra = ob.isbn
            """
            if solo_pendientes:
                sql += " WHERE mul.estado = 'Pendiente'"
            sql += " ORDER BY mul.multa"
            cursor.execute(sql)
            filas = cursor.fetchall()
            for fila in filas:
                fila["usuario"] = fila["usuario"].strip()
            return filas
        finally:
            cursor.close()

    # [OPCION 5 -> 3]
    def consultar_detalle_multa(self, id_multa):
        # Datos completos de una multa (con su estado)
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT mul.multa AS id_multa,
                       pres.folio AS prestamo,
                       pres.fecha_salida,
                       CONCAT(us.nombre_pila, ' ', us.primer_ap, ' ', IFNULL(us.segundo_ap, '')) AS usuario,
                       ob.isbn,
                       ob.titulo,
                       ob.subtitulo,
                       dev.ejemplar,
                       pres.fecha_limite,
                       dev.fecha_devolucion,
                       mul.dias_retraso,
                       mul.monto_dia,
                       mul.total,
                       mul.estado
                FROM multa AS mul
                INNER JOIN devolucion AS dev ON mul.devolucion = dev.id_devolucion
                INNER JOIN prestamo AS pres ON dev.prestamo = pres.folio
                INNER JOIN usuario AS us ON pres.usuario = us.id_usuario
                INNER JOIN obra AS ob ON dev.obra = ob.isbn
                WHERE mul.multa = %s
            """
            cursor.execute(sql, (id_multa,))
            fila = cursor.fetchone()
            if fila:
                fila["usuario"] = fila["usuario"].strip()
            return fila
        finally:
            cursor.close()

    # [OPCION 5 -> 2]
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

    # [OPCION 5 -> 2]
    def marcar_pagada(self, id_multa):
        # Cambia una multa pendiente a 'Pagada' usando solo su numero de multa
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
