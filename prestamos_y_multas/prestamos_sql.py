# En este archivo se ven las consultas SQL de prestamos (opcion 3 del menu;
# tambien se usan en la opcion 7).
#
# INDICE (opcion del menu -> metodo):
#   [OPCION 3 -> 1 | OPCION 7 -> 2]  ->  listar_resumen_disponibles()
#   [OPCION 3 -> 1]  ->  obtener_ejemplares_disponibles_por_isbn()
#   [OPCION 3 -> 1]  ->  ejemplar_disponible()
#   [OPCION 3 -> 1]  ->  registrar_prestamo()
#   [OPCION 3 -> 2]  ->  listar_todos_prestamos()
#   [OPCION 3 -> 2]  ->  consultar_detalle_prestamo()
#   [OPCION 3 -> 3]  ->  listar_fechas_prestamos()
#   [OPCION 3 -> 3]  ->  consultar_prestamos_por_fecha()
#   [OPCION 7 -> 3]  ->  listar_prestamos_activos_detalle()

from datetime import date, timedelta
from mysql.connector import Error

from nucleo.conexion import GestorBase
from nucleo.utilidades import formatear_fecha


class GestorPrestamos(GestorBase):
    # Esta clase maneja los prestamos y las consultas por folio y por fecha.

    # Ayuda: trae las devoluciones como un conjunto de (obra, ejemplar, prestamo)
    def _obtener_devueltos(self, cursor):
        cursor.execute("SELECT obra, ejemplar, prestamo FROM devolucion")
        return set((f["obra"], f["ejemplar"], f["prestamo"]) for f in cursor.fetchall())

    # Ayuda: trae los ejemplares que estan prestados ahora (sin devolver)
    # Regresa un conjunto de (obra, ejemplar)
    def _obtener_prestados(self, cursor):
        devueltos = self._obtener_devueltos(cursor)
        cursor.execute("SELECT obra, ejemplar, prestamo FROM prestamo_ejemplar")
        prestados = set()
        for fila in cursor.fetchall():
            if (fila["obra"], fila["ejemplar"], fila["prestamo"]) not in devueltos:
                prestados.add((fila["obra"], fila["ejemplar"]))
        return prestados

    # [OPCION 3 -> 1 | OPCION 7 -> 2]
    def listar_resumen_disponibles(self):
        # Por cada obra, cuantos ejemplares estan disponibles ahora
        cursor = self.db.obtener_cursor()
        try:
            prestados = self._obtener_prestados(cursor)

            sql = """
                SELECT ob.isbn, ob.titulo, ej.ejemplar
                FROM ejemplar AS ej
                INNER JOIN obra AS ob ON ej.obra = ob.isbn
                ORDER BY ob.titulo, ob.isbn, ej.ejemplar
            """
            cursor.execute(sql)

            resumen = {}
            for fila in cursor.fetchall():
                if (fila["isbn"], fila["ejemplar"]) in prestados:
                    continue
                if fila["isbn"] not in resumen:
                    resumen[fila["isbn"]] = {
                        "isbn": fila["isbn"],
                        "titulo": fila["titulo"],
                        "disponibles": 0,
                    }
                resumen[fila["isbn"]]["disponibles"] += 1
            return list(resumen.values())
        finally:
            cursor.close()

    # [OPCION 3 -> 1]
    def obtener_ejemplares_disponibles_por_isbn(self, isbn):
        # Ejemplares disponibles de un ISBN, con su ubicacion
        cursor = self.db.obtener_cursor()
        try:
            prestados = self._obtener_prestados(cursor)

            sql = """
                SELECT ej.obra, ob.titulo, ej.ejemplar,
                       loc.seccion, loc.pasillo, loc.estante
                FROM ejemplar AS ej
                INNER JOIN obra AS ob ON ej.obra = ob.isbn
                INNER JOIN localizacion AS loc ON ej.localizacion = loc.id_localizacion
                WHERE ej.obra = %s
                ORDER BY ej.ejemplar
            """
            cursor.execute(sql, (isbn,))
            return [f for f in cursor.fetchall() if (f["obra"], f["ejemplar"]) not in prestados]
        finally:
            cursor.close()

    # [OPCION 3 -> 1]
    def ejemplar_disponible(self, isbn, num_ejemplar):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "SELECT 1 FROM ejemplar WHERE obra = %s AND ejemplar = %s",
                (isbn, num_ejemplar),
            )
            if cursor.fetchone() is None:
                return False

            # Prestamos de este ejemplar y sus devoluciones
            cursor.execute(
                "SELECT prestamo FROM prestamo_ejemplar WHERE obra = %s AND ejemplar = %s",
                (isbn, num_ejemplar),
            )
            prestamos = [f["prestamo"] for f in cursor.fetchall()]

            cursor.execute(
                "SELECT prestamo FROM devolucion WHERE obra = %s AND ejemplar = %s",
                (isbn, num_ejemplar),
            )
            devueltos = [f["prestamo"] for f in cursor.fetchall()]

            # Esta disponible si todos sus prestamos ya se devolvieron
            for folio in prestamos:
                if folio not in devueltos:
                    return False
            return True
        finally:
            cursor.close()

    # [OPCION 3 -> 1]
    def registrar_prestamo(self, prestamo):
        # Crea el prestamo (fecha limite = +14 dias) revisando fechas y disponibilidad
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

    # [OPCION 3 -> 2]
    def listar_todos_prestamos(self):
        # Todos los prestamos con el total de ejemplares y cuantos faltan por devolver
        cursor = self.db.obtener_cursor()
        try:
            devueltos = self._obtener_devueltos(cursor)

            sql = """
                SELECT pres.folio, pres.fecha_salida, pres.fecha_limite,
                       CONCAT(us.nombre_pila, ' ', us.primer_ap, ' ', IFNULL(us.segundo_ap, '')) AS usuario,
                       presej.obra, presej.ejemplar
                FROM prestamo AS pres
                INNER JOIN usuario AS us ON pres.usuario = us.id_usuario
                INNER JOIN prestamo_ejemplar AS presej ON pres.folio = presej.prestamo
                ORDER BY pres.folio
            """
            cursor.execute(sql)

            prestamos = {}
            for fila in cursor.fetchall():
                folio = fila["folio"]
                if folio not in prestamos:
                    prestamos[folio] = {
                        "folio": folio,
                        "fecha_salida": fila["fecha_salida"],
                        "fecha_limite": fila["fecha_limite"],
                        "usuario": fila["usuario"].strip(),
                        "total_ejemplares": 0,
                        "pendientes": 0,
                    }
                prestamos[folio]["total_ejemplares"] += 1
                if (fila["obra"], fila["ejemplar"], folio) not in devueltos:
                    prestamos[folio]["pendientes"] += 1
            return list(prestamos.values())
        finally:
            cursor.close()

    # [OPCION 3 -> 2]
    def consultar_detalle_prestamo(self, folio):
        # Informacion completa de un prestamo y todos sus ejemplares
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT pres.folio,
                       pres.fecha_salida,
                       pres.fecha_limite,
                       CONCAT(us.nombre_pila, ' ', us.primer_ap, ' ', IFNULL(us.segundo_ap, '')) AS usuario,
                       ob.isbn,
                       ob.titulo,
                       ob.subtitulo,
                       presej.ejemplar
                FROM prestamo AS pres
                INNER JOIN usuario AS us ON pres.usuario = us.id_usuario
                INNER JOIN prestamo_ejemplar AS presej ON presej.prestamo = pres.folio
                INNER JOIN obra AS ob ON presej.obra = ob.isbn
                WHERE pres.folio = %s
                ORDER BY ob.titulo, presej.ejemplar
            """
            cursor.execute(sql, (folio,))
            filas = cursor.fetchall()

            # Fechas de devolucion de este prestamo, por (obra, ejemplar)
            cursor.execute(
                "SELECT obra, ejemplar, fecha_devolucion FROM devolucion WHERE prestamo = %s",
                (folio,),
            )
            fechas_dev = {(f["obra"], f["ejemplar"]): f["fecha_devolucion"] for f in cursor.fetchall()}

            for fila in filas:
                fila["usuario"] = fila["usuario"].strip()
                fila["fecha_devolucion"] = fechas_dev.get((fila["isbn"], fila["ejemplar"]))
            return filas
        finally:
            cursor.close()

    # [OPCION 3 -> 3]
    def listar_fechas_prestamos(self):
        # Fechas con prestamos y cuantos prestamos y ejemplares hubo en cada una
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT pres.fecha_salida, pres.folio, presej.ejemplar
                FROM prestamo AS pres
                INNER JOIN prestamo_ejemplar AS presej ON presej.prestamo = pres.folio
                ORDER BY pres.fecha_salida DESC
            """
            cursor.execute(sql)

            fechas = {}
            for fila in cursor.fetchall():
                fecha = fila["fecha_salida"]
                if fecha not in fechas:
                    fechas[fecha] = {"folios": set(), "total_ejemplares": 0}
                fechas[fecha]["folios"].add(fila["folio"])
                fechas[fecha]["total_ejemplares"] += 1

            resultado = []
            for fecha, datos in fechas.items():
                resultado.append(
                    {
                        "fecha_salida": fecha,
                        "total_prestamos": len(datos["folios"]),
                        "total_ejemplares": datos["total_ejemplares"],
                    }
                )
            return resultado
        finally:
            cursor.close()

    # [OPCION 3 -> 3]
    def consultar_prestamos_por_fecha(self, fecha):
        # Prestamos de una fecha con cantidad de ejemplares y empleado
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT pres.fecha_salida,
                       pres.folio,
                       CONCAT(us.nombre_pila, ' ', us.primer_ap, ' ', IFNULL(us.segundo_ap, '')) AS usuario,
                       COUNT(presej.ejemplar) AS cantidad_ejemplares,
                       pres.fecha_limite,
                       CONCAT(emp.nombre_pila, ' ', emp.primer_ap, ' ', IFNULL(emp.segundo_ap, '')) AS empleado
                FROM prestamo AS pres
                INNER JOIN usuario AS us ON pres.usuario = us.id_usuario
                INNER JOIN empleado AS emp ON pres.empleado = emp.id_empleado
                INNER JOIN prestamo_ejemplar AS presej ON presej.prestamo = pres.folio
                WHERE pres.fecha_salida = %s
                GROUP BY pres.fecha_salida,
                         pres.folio,
                         us.nombre_pila, us.primer_ap, us.segundo_ap,
                         pres.fecha_limite,
                         emp.nombre_pila, emp.primer_ap, emp.segundo_ap
                ORDER BY pres.folio
            """
            cursor.execute(sql, (fecha,))
            filas = cursor.fetchall()
            for fila in filas:
                fila["usuario"] = fila["usuario"].strip()
                fila["empleado"] = fila["empleado"].strip()
            return filas
        finally:
            cursor.close()

    # [OPCION 7 -> 3]
    def listar_prestamos_activos_detalle(self):
        # Detalle de cada ejemplar que esta prestado ahora
        cursor = self.db.obtener_cursor()
        try:
            devueltos = self._obtener_devueltos(cursor)

            sql = """
                SELECT pres.folio, pres.fecha_salida, pres.fecha_limite,
                       CONCAT(us.nombre_pila, ' ', us.primer_ap, ' ', IFNULL(us.segundo_ap, '')) AS usuario,
                       presej.obra, ob.titulo, presej.ejemplar,
                       CONCAT(emp.nombre_pila, ' ', emp.primer_ap, ' ', IFNULL(emp.segundo_ap, '')) AS empleado
                FROM prestamo AS pres
                INNER JOIN usuario AS us ON pres.usuario = us.id_usuario
                INNER JOIN empleado AS emp ON pres.empleado = emp.id_empleado
                INNER JOIN prestamo_ejemplar AS presej ON pres.folio = presej.prestamo
                INNER JOIN obra AS ob ON presej.obra = ob.isbn
                ORDER BY pres.folio, ob.titulo, presej.ejemplar
            """
            cursor.execute(sql)

            activos = []
            for fila in cursor.fetchall():
                if (fila["obra"], fila["ejemplar"], fila["folio"]) in devueltos:
                    continue
                fila["usuario"] = fila["usuario"].strip()
                fila["empleado"] = fila["empleado"].strip()
                activos.append(fila)
            return activos
        finally:
            cursor.close()
