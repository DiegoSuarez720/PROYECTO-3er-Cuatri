# En este archivo se ven las consultas SQL de devoluciones (opcion 4 del menu).
#
# INDICE (opcion del menu -> metodo):
#   [OPCION 4 -> 1]  ->  listar_prestamos_activos_resumen()
#   [OPCION 4 -> 1]  ->  listar_ejemplares_pendientes_prestamo()
#   [OPCION 4 -> 1]  ->  registrar_devolucion()
#   [OPCION 4 -> 2]  ->  listar_fechas_devoluciones()
#   [OPCION 4 -> 2]  ->  consultar_devoluciones_por_fecha()

from datetime import date
from decimal import Decimal
from mysql.connector import Error

from nucleo.conexion import GestorBase
from prestamos_y_multas.multas_sql import TARIFA_MULTA_DIA


class GestorDevoluciones(GestorBase):
    # Esta clase guarda y consulta devoluciones (si hay retraso crea la multa).

    # Ayuda: trae las devoluciones como un conjunto de (obra, ejemplar, prestamo)
    def _obtener_devueltos(self, cursor):
        cursor.execute("SELECT obra, ejemplar, prestamo FROM devolucion")
        return set((f["obra"], f["ejemplar"], f["prestamo"]) for f in cursor.fetchall())

    # [OPCION 4 -> 1]
    def listar_prestamos_activos_resumen(self):
        # Prestamos que tienen al menos un ejemplar sin devolver
        cursor = self.db.obtener_cursor()
        try:
            devueltos = self._obtener_devueltos(cursor)

            sql = """
                SELECT pres.folio, pres.fecha_salida, pres.fecha_limite,
                       CONCAT(us.nombre_pila, ' ', us.primer_ap, ' ', IFNULL(us.segundo_ap, '')) AS usuario,
                       CONCAT(emp.nombre_pila, ' ', emp.primer_ap, ' ', IFNULL(emp.segundo_ap, '')) AS empleado,
                       presej.obra, presej.ejemplar
                FROM prestamo AS pres
                INNER JOIN usuario AS us ON pres.usuario = us.id_usuario
                INNER JOIN empleado AS emp ON pres.empleado = emp.id_empleado
                INNER JOIN prestamo_ejemplar AS presej ON pres.folio = presej.prestamo
                ORDER BY pres.folio
            """
            cursor.execute(sql)

            prestamos = {}
            for fila in cursor.fetchall():
                folio = fila["folio"]
                if (fila["obra"], fila["ejemplar"], folio) in devueltos:
                    continue
                if folio not in prestamos:
                    prestamos[folio] = {
                        "folio": folio,
                        "fecha_salida": fila["fecha_salida"],
                        "fecha_limite": fila["fecha_limite"],
                        "usuario": fila["usuario"].strip(),
                        "empleado": fila["empleado"].strip(),
                        "pendientes": 0,
                    }
                prestamos[folio]["pendientes"] += 1
            return list(prestamos.values())
        finally:
            cursor.close()

    # [OPCION 4 -> 1]
    def listar_ejemplares_pendientes_prestamo(self, folio):
        # Ejemplares de un folio que todavia no se devuelven
        cursor = self.db.obtener_cursor()
        try:
            devueltos = self._obtener_devueltos(cursor)

            sql = """
                SELECT presej.prestamo, presej.obra, ob.titulo, presej.ejemplar,
                       pres.fecha_salida, pres.fecha_limite
                FROM prestamo_ejemplar AS presej
                INNER JOIN prestamo AS pres ON presej.prestamo = pres.folio
                INNER JOIN obra AS ob ON presej.obra = ob.isbn
                WHERE presej.prestamo = %s
                ORDER BY presej.obra, presej.ejemplar
            """
            cursor.execute(sql, (folio,))
            return [
                f
                for f in cursor.fetchall()
                if (f["obra"], f["ejemplar"], f["prestamo"]) not in devueltos
            ]
        finally:
            cursor.close()

    # [OPCION 4 -> 1]
    def registrar_devolucion(
        self, folio, isbn, num_ejemplar, fecha_devolucion, id_empleado, monto_dia=TARIFA_MULTA_DIA
    ):
        # Guarda la devolucion revisando fechas y crea la multa si hubo retraso
        if fecha_devolucion > date.today():
            raise ValueError("La fecha de devolución no puede ser futura.")

        cursor = self.db.obtener_cursor()
        try:
            sql_check = """
                SELECT pres.fecha_salida, pres.fecha_limite
                FROM prestamo_ejemplar AS presej
                INNER JOIN prestamo AS pres ON presej.prestamo = pres.folio
                WHERE presej.prestamo = %s AND presej.obra = %s AND presej.ejemplar = %s
            """
            cursor.execute(sql_check, (folio, isbn, num_ejemplar))
            fila = cursor.fetchone()

            if not fila:
                raise ValueError("No se encontró ese ejemplar dentro del préstamo indicado.")

            # Revisa si ese ejemplar ya tiene una devolucion
            cursor.execute(
                "SELECT id_devolucion FROM devolucion WHERE prestamo = %s AND obra = %s AND ejemplar = %s",
                (folio, isbn, num_ejemplar),
            )
            if cursor.fetchone() is not None:
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

    # [OPCION 4 -> 2]
    def listar_fechas_devoluciones(self):
        # Fechas con devoluciones, separando a tiempo y con retraso
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT dev.fecha_devolucion, pres.fecha_limite
                FROM devolucion AS dev
                INNER JOIN prestamo AS pres ON dev.prestamo = pres.folio
                ORDER BY dev.fecha_devolucion DESC
            """
            cursor.execute(sql)

            fechas = {}
            for fila in cursor.fetchall():
                fecha = fila["fecha_devolucion"]
                if fecha not in fechas:
                    fechas[fecha] = {
                        "fecha_devolucion": fecha,
                        "total": 0,
                        "a_tiempo": 0,
                        "con_retraso": 0,
                    }
                fechas[fecha]["total"] += 1
                if fecha <= fila["fecha_limite"]:
                    fechas[fecha]["a_tiempo"] += 1
                else:
                    fechas[fecha]["con_retraso"] += 1
            return list(fechas.values())
        finally:
            cursor.close()

    # [OPCION 4 -> 2]
    def consultar_devoluciones_por_fecha(self, fecha, filtro="a_tiempo"):
        # Devoluciones de una fecha ('a_tiempo', 'retraso' o 'todas')
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT dev.fecha_devolucion,
                       pres.folio,
                       pres.fecha_salida,
                       pres.fecha_limite,
                       ob.isbn,
                       dev.ejemplar,
                       ob.titulo,
                       ob.subtitulo
                FROM devolucion AS dev
                INNER JOIN prestamo AS pres ON dev.prestamo = pres.folio
                INNER JOIN obra AS ob ON dev.obra = ob.isbn
                WHERE dev.fecha_devolucion = %s
            """
            if filtro == "a_tiempo":
                sql += " AND dev.fecha_devolucion <= pres.fecha_limite"
            elif filtro == "retraso":
                sql += " AND dev.fecha_devolucion > pres.fecha_limite"
            sql += " ORDER BY pres.folio, dev.ejemplar"
            cursor.execute(sql, (fecha,))
            return cursor.fetchall()
        finally:
            cursor.close()
