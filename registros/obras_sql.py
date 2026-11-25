# En este archivo se ven las consultas SQL de obras, ejemplares y localizacion
# (opciones 1 y 2 del menu; tambien se usan en las opciones 3 y 7).
#
# INDICE (opcion del menu -> metodo):
#   [OPCION 1 -> 2 | OPCION 1 -> 3 | OPCION 2 | OPCION 7 -> 1]  ->  listar_obras()
#   [OPCION 1 -> 2]  ->  obtener_obra()
#   [OPCION 3 -> 1]  ->  obtener_fecha_primera_adquisicion()
#   [OPCION 1 -> 3]  ->  consultar_obra_completa()
#   [OPCION 1 -> 1 | OPCION 3 -> 1]  ->  existe_obra()
#   [OPCION 1 -> 1 | OPCION 1 -> 2]  ->  obtener_localizacion_base()
#   [OPCION 1 -> 1]  ->  registrar_obra_completa()
#   [OPCION 1 -> 2]  ->  abastecer_obra_existente()
#   [OPCION 1 -> 4]  ->  obtener_obra_para_editar()
#   [OPCION 1 -> 4]  ->  actualizar_obra()
#   [OPCION 2]  ->  listar_ejemplares_obra()
#   [OPCION 2]  ->  asignar_localizacion_ejemplar()
#   [OPCION 2]  ->  asignar_localizacion_ejemplares()
#   [OPCION 2]  ->  asignar_localizacion_todos()

from datetime import date
from mysql.connector import Error

from nucleo.conexion import GestorBase
from nucleo.utilidades import formatear_fecha


class GestorObras(GestorBase):
    # Esta clase maneja obras, abastecimiento, ejemplares y localizaciones.

    # [OPCION 1 -> 2 | OPCION 1 -> 3 | OPCION 2 | OPCION 7 -> 1]
    def listar_obras(self):
        # Se hacen 3 consultas sencillas y se juntan los resultados en Python
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT ob.isbn, ob.titulo, ob.subtitulo, ob.`año_publicacion` AS anio,
                       tip.tipo_obra, cat.genero
                FROM obra AS ob
                INNER JOIN tipo AS tip ON ob.tipo = tip.id_tipo
                INNER JOIN categoria AS cat ON ob.categoria = cat.codigo
                ORDER BY ob.titulo
            """
            cursor.execute(sql)
            obras = cursor.fetchall()

            cursor.execute("SELECT obra, COUNT(*) AS total FROM ejemplar GROUP BY obra")
            ejemplares_por_obra = {f["obra"]: f["total"] for f in cursor.fetchall()}

            cursor.execute("SELECT obra, COUNT(*) AS total FROM autor_obra GROUP BY obra")
            autores_por_obra = {f["obra"]: f["total"] for f in cursor.fetchall()}

            for obra in obras:
                obra["total_ejemplares"] = ejemplares_por_obra.get(obra["isbn"], 0)
                obra["total_autores"] = autores_por_obra.get(obra["isbn"], 0)
            return obras
        finally:
            cursor.close()

    # [OPCION 1 -> 2]
    def obtener_obra(self, isbn):
        # Datos basicos de una obra (con su anio de publicacion)
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "SELECT isbn, titulo, `año_publicacion` AS anio FROM obra WHERE isbn = %s",
                (isbn,),
            )
            return cursor.fetchone()
        finally:
            cursor.close()

    # [OPCION 3 -> 1]
    def obtener_fecha_primera_adquisicion(self, isbn):
        # Fecha mas antigua en que se compro la obra
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

    # [OPCION 1 -> 3]
    def consultar_obra_completa(self, isbn):
        # Toda la informacion de una obra: tipo, categoria, editorial, pais y autores
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT ob.isbn,
                       ob.titulo,
                       ob.subtitulo,
                       tip.tipo_obra,
                       ob.`año_publicacion` AS anio_publicacion,
                       cat.genero,
                       ob.num_paginas,
                       ed.nombre AS editorial,
                       pa.nombre AS pais,
                       CONCAT(aut.nombre_pila, ' ', aut.primer_ap, ' ', IFNULL(aut.segundo_ap, '')) AS autor
                FROM obra AS ob
                INNER JOIN tipo AS tip ON ob.tipo = tip.id_tipo
                INNER JOIN categoria AS cat ON ob.categoria = cat.codigo
                INNER JOIN obra_editorial AS obraed ON obraed.obra = ob.isbn
                INNER JOIN editorial AS ed ON obraed.editorial = ed.id_editorial
                INNER JOIN pais AS pa ON ed.pais = pa.clave
                INNER JOIN autor_obra AS autobra ON autobra.obra = ob.isbn
                INNER JOIN autor AS aut ON autobra.autor = aut.num_id
                WHERE ob.isbn = %s
                ORDER BY autor, ed.nombre
            """
            cursor.execute(sql, (isbn,))
            filas = cursor.fetchall()
            # Se quita el espacio del final cuando no hay segundo apellido
            for fila in filas:
                fila["autor"] = fila["autor"].strip()
            return filas
        finally:
            cursor.close()

    # [OPCION 1 -> 1 | OPCION 3 -> 1]
    def existe_obra(self, isbn):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT 1 FROM obra WHERE isbn = %s", (isbn,))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    # [OPCION 1 -> 1 | OPCION 1 -> 2]
    def obtener_localizacion_base(self):
        # Primer id_localizacion que exista (por defecto 'Sin asignar / Recepcion')
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

    # [OPCION 1 -> 1]
    def registrar_obra_completa(
        self, obra, rfc_proveedor, fecha_adquisicion, cantidad, id_localizacion=None
    ):
        # Guarda la obra, sus autores, editoriales, el abastecimiento y los ejemplares
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

    # [OPCION 1 -> 2]
    def abastecer_obra_existente(
        self, isbn, rfc_proveedor, fecha_adquisicion, cantidad, id_localizacion=None
    ):
        # Agrega mas ejemplares a una obra que ya existe
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
                "SELECT IFNULL(MAX(ejemplar), 0) AS ultimo FROM ejemplar WHERE obra = %s",
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

    # [OPCION 1 -> 4]
    def obtener_obra_para_editar(self, isbn):
        # Trae los datos de la obra que se pueden cambiar, con su tipo y categoria
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT ob.isbn, ob.titulo, ob.subtitulo, ob.`año_publicacion` AS anio,
                       ob.num_paginas, ob.tipo, tip.tipo_obra, ob.categoria, cat.genero
                FROM obra AS ob
                INNER JOIN tipo AS tip ON ob.tipo = tip.id_tipo
                INNER JOIN categoria AS cat ON ob.categoria = cat.codigo
                WHERE ob.isbn = %s
            """
            cursor.execute(sql, (isbn,))
            return cursor.fetchone()
        finally:
            cursor.close()

    # [OPCION 1 -> 4]
    def actualizar_obra(
        self, isbn, titulo, subtitulo, anio_publicacion, num_paginas, id_tipo, cod_categoria
    ):
        # Cambia los datos de una obra (el ISBN no se puede cambiar)
        hoy = date.today()
        if anio_publicacion < 1450 or anio_publicacion > hoy.year:
            raise ValueError(f"El año de publicación debe estar entre 1450 y {hoy.year}.")

        primera = self.obtener_fecha_primera_adquisicion(isbn)
        if primera is not None and anio_publicacion > primera.year:
            raise ValueError(
                f"El año de publicación no puede ser mayor al año de la primera adquisición ({primera.year})."
            )
        if num_paginas <= 0 or num_paginas > 10000:
            raise ValueError("El número de páginas debe estar entre 1 y 10,000.")

        cursor = self.db.obtener_cursor()
        try:
            sql = """
                UPDATE obra
                SET titulo = %s, subtitulo = %s, `año_publicacion` = %s,
                    num_paginas = %s, tipo = %s, categoria = %s
                WHERE isbn = %s
            """
            cursor.execute(
                sql,
                (titulo, subtitulo, anio_publicacion, num_paginas, id_tipo, cod_categoria, isbn),
            )
            self.db.confirmar()
        except Error:
            self.db.revertir()
            raise
        finally:
            cursor.close()

    # [OPCION 2]
    def listar_ejemplares_obra(self, isbn):
        # Se consultan los ejemplares, los prestamos y las devoluciones por separado
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT ej.obra, ej.ejemplar, ej.localizacion,
                       loc.seccion, loc.pasillo, loc.estante
                FROM ejemplar AS ej
                INNER JOIN localizacion AS loc ON ej.localizacion = loc.id_localizacion
                WHERE ej.obra = %s
                ORDER BY ej.ejemplar
            """
            cursor.execute(sql, (isbn,))
            ejemplares = cursor.fetchall()

            cursor.execute(
                "SELECT obra, ejemplar, prestamo FROM prestamo_ejemplar WHERE obra = %s",
                (isbn,),
            )
            prestamos = cursor.fetchall()

            cursor.execute(
                "SELECT obra, ejemplar, prestamo FROM devolucion WHERE obra = %s",
                (isbn,),
            )
            devueltos = set((f["obra"], f["ejemplar"], f["prestamo"]) for f in cursor.fetchall())

            # Un ejemplar esta prestado si tiene un prestamo sin devolucion
            prestados = set()
            for pres in prestamos:
                if (pres["obra"], pres["ejemplar"], pres["prestamo"]) not in devueltos:
                    prestados.add((pres["obra"], pres["ejemplar"]))

            for ej in ejemplares:
                if (ej["obra"], ej["ejemplar"]) in prestados:
                    ej["estado"] = "Prestado"
                else:
                    ej["estado"] = "Disponible"
            return ejemplares
        finally:
            cursor.close()

    # [OPCION 2]
    def asignar_localizacion_ejemplar(self, isbn, num_ejemplar, id_localizacion):
        # Cambia la localizacion de un ejemplar
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

    # [OPCION 2]
    def asignar_localizacion_ejemplares(self, isbn, numeros_ejemplares, id_localizacion):
        # Cambia la localizacion de varios ejemplares de una obra en una sola transaccion
        cursor = self.db.obtener_cursor()
        try:
            actualizados = 0
            for num_ejemplar in numeros_ejemplares:
                cursor.execute(
                    "UPDATE ejemplar SET localizacion = %s WHERE obra = %s AND ejemplar = %s",
                    (id_localizacion, isbn, num_ejemplar),
                )
                actualizados += 1
            self.db.confirmar()
            return actualizados
        except Error:
            self.db.revertir()
            raise
        finally:
            cursor.close()

    # [OPCION 2]
    def asignar_localizacion_todos(self, isbn, id_localizacion):
        # Pone la misma localizacion a todos los ejemplares de una obra
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
