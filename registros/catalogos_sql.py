# En este archivo se ven las consultas SQL de los catalogos auxiliares:
# paises, tipos, categorias, autores, editoriales, proveedores,
# localizaciones, usuarios y empleados (opcion 6 del menu principal).
#
# INDICE (opcion del menu -> metodos):
#   [OPCION 6 -> 1]  PAISES: listar_paises, existe_pais, existe_pais_nombre, crear_pais
#   [OPCION 6 -> 2]  TIPOS DE OBRA: listar_tipos, existe_tipo, existe_tipo_nombre, crear_tipo
#   [OPCION 6 -> 3]  CATEGORIAS: listar_categorias, existe_categoria, existe_categoria_genero, crear_categoria
#   [OPCION 6 -> 4]  AUTORES: listar_autores, existe_autor, existe_autor_nombre, crear_autor
#   [OPCION 6 -> 5]  EDITORIALES: listar_editoriales, existe_editorial, existe_editorial_nombre, crear_editorial
#   [OPCION 6 -> 6]  PROVEEDORES Y TELEFONOS: listar_proveedores, existe_proveedor, existe_telefono_proveedor, crear_proveedor, agregar_telefono_proveedor
#   [OPCION 6 -> 7]  LOCALIZACIONES: listar_localizaciones, existe_localizacion, existe_localizacion_datos, crear_localizacion
#   [OPCION 6 -> 8]  USUARIOS Y TELEFONOS: listar_usuarios, existe_usuario, existe_usuario_datos, existe_telefono_usuario, crear_usuario, agregar_telefono_usuario
#   [OPCION 6 -> 9]  EMPLEADOS: listar_empleados, existe_empleado_user, crear_empleado

from mysql.connector import Error

from nucleo.conexion import GestorBase
from nucleo.utilidades import normalizar_telefono


class GestorCatalogos(GestorBase):
    # Esta clase tiene las altas, los listados y las revisiones de
    # "ya existe" de todos los catalogos.

    # --- PAISES ---
    # [OPCION 6 -> 1]
    def listar_paises(self):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT clave, nombre FROM pais ORDER BY clave")
            return cursor.fetchall()
        finally:
            cursor.close()

    # [OPCION 6 -> 1]
    def existe_pais(self, clave):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT 1 FROM pais WHERE clave = %s", (clave.strip(),))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    # [OPCION 6 -> 1]
    def existe_pais_nombre(self, nombre):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT 1 FROM pais WHERE nombre = %s", (nombre.strip(),))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    # [OPCION 6 -> 1]
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
    # [OPCION 6 -> 2]
    def listar_tipos(self):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT id_tipo, tipo_obra FROM tipo ORDER BY id_tipo")
            return cursor.fetchall()
        finally:
            cursor.close()

    # [OPCION 6 -> 2]
    def existe_tipo(self, id_tipo):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT 1 FROM tipo WHERE id_tipo = %s", (id_tipo,))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    # [OPCION 6 -> 2]
    def existe_tipo_nombre(self, tipo_obra):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT 1 FROM tipo WHERE tipo_obra = %s", (tipo_obra.strip(),))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    # [OPCION 6 -> 2]
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
    # [OPCION 6 -> 3]
    def listar_categorias(self):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT codigo, genero FROM categoria ORDER BY codigo")
            return cursor.fetchall()
        finally:
            cursor.close()

    # [OPCION 6 -> 3]
    def existe_categoria(self, codigo):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT 1 FROM categoria WHERE codigo = %s", (codigo.strip(),))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    # [OPCION 6 -> 3]
    def existe_categoria_genero(self, genero):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT 1 FROM categoria WHERE genero = %s", (genero.strip(),))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    # [OPCION 6 -> 3]
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
    # [OPCION 6 -> 4]
    def listar_autores(self):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "SELECT num_id, nombre_pila, primer_ap, segundo_ap FROM autor ORDER BY num_id"
            )
            return cursor.fetchall()
        finally:
            cursor.close()

    # [OPCION 6 -> 4]
    def existe_autor(self, num_id):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT 1 FROM autor WHERE num_id = %s", (num_id,))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    # [OPCION 6 -> 4]
    def existe_autor_nombre(self, nombre_pila, primer_ap, segundo_ap=None):
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT 1 FROM autor
                WHERE nombre_pila = %s
                  AND primer_ap = %s
                  AND IFNULL(segundo_ap, '') = %s
            """
            cursor.execute(
                sql,
                (nombre_pila.strip(), primer_ap.strip(), (segundo_ap or "").strip()),
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    # [OPCION 6 -> 4]
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
    # [OPCION 6 -> 5]
    def listar_editoriales(self):
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT ed.id_editorial, ed.nombre, ed.pais, pa.nombre AS nombre_pais
                FROM editorial AS ed
                INNER JOIN pais AS pa ON ed.pais = pa.clave
                ORDER BY ed.id_editorial
            """
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()

    # [OPCION 6 -> 5]
    def existe_editorial(self, id_editorial):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT 1 FROM editorial WHERE id_editorial = %s", (id_editorial,))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    # [OPCION 6 -> 5]
    def existe_editorial_nombre(self, nombre, pais):
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT 1 FROM editorial
                WHERE nombre = %s
                  AND pais = %s
            """
            cursor.execute(sql, (nombre.strip(), pais.strip()))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    # [OPCION 6 -> 5]
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
    # [OPCION 6 -> 6]
    def listar_proveedores(self):
        # Se hacen dos consultas: una de proveedores y otra de telefonos.
        # Los telefonos se unen en Python.
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "SELECT RFC, nombre_empresa FROM proveedor ORDER BY RFC"
            )
            proveedores = cursor.fetchall()

            cursor.execute(
                """
                SELECT prov.RFC, telprov.telefono
                FROM proveedor AS prov
                INNER JOIN telefono_proveedor AS telprov ON prov.RFC = telprov.proveedor
                """
            )
            telefonos_por_rfc = {}
            for fila in cursor.fetchall():
                telefonos_por_rfc.setdefault(fila["RFC"], []).append(fila["telefono"])

            for prov in proveedores:
                lista = telefonos_por_rfc.get(prov["RFC"])
                prov["telefonos"] = ", ".join(lista) if lista else None
            return proveedores
        finally:
            cursor.close()

    # [OPCION 6 -> 6]
    def existe_proveedor(self, rfc):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT 1 FROM proveedor WHERE RFC = %s", (rfc.strip(),))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    # [OPCION 6 -> 6]
    def existe_telefono_proveedor(self, rfc, telefono):
        # Compara solo los digitos (ignora guiones o espacios)
        objetivo = normalizar_telefono(telefono)
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "SELECT telefono FROM telefono_proveedor WHERE proveedor = %s",
                (rfc.strip(),),
            )
            existentes = cursor.fetchall()
            return any(normalizar_telefono(f["telefono"]) == objetivo for f in existentes)
        finally:
            cursor.close()

    # [OPCION 6 -> 6]
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
            vistos = set()
            for tel in proveedor.telefonos:
                limpio = tel.strip()
                clave_tel = normalizar_telefono(limpio)
                if clave_tel in vistos:
                    continue
                vistos.add(clave_tel)
                cursor.execute(
                    "INSERT INTO telefono_proveedor (telefono, proveedor) VALUES (%s, %s)",
                    (limpio, proveedor.rfc),
                )
            self.db.confirmar()
        except Error:
            self.db.revertir()
            raise
        finally:
            cursor.close()

    # [OPCION 6 -> 6]
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
    # [OPCION 6 -> 7]
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

    # [OPCION 6 -> 7]
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

    # [OPCION 6 -> 7]
    def existe_localizacion_datos(self, seccion, pasillo, estante):
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT 1 FROM localizacion
                WHERE seccion = %s
                  AND pasillo = %s
                  AND estante = %s
            """
            cursor.execute(sql, (seccion.strip(), pasillo, estante))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    # [OPCION 6 -> 7]
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
    # [OPCION 6 -> 8]
    def listar_usuarios(self):
        # Se hacen dos consultas: una de usuarios y otra de telefonos.
        # Los telefonos se unen en Python.
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT id_usuario, nombre_pila, primer_ap, segundo_ap,
                       dir_calle, dir_numero, dir_colonia
                FROM usuario
                ORDER BY id_usuario
            """
            cursor.execute(sql)
            usuarios = cursor.fetchall()

            cursor.execute(
                """
                SELECT us.id_usuario, telus.num_tel
                FROM usuario AS us
                INNER JOIN telefono_usuario AS telus ON us.id_usuario = telus.usuario
                """
            )
            telefonos_por_usuario = {}
            for fila in cursor.fetchall():
                telefonos_por_usuario.setdefault(fila["id_usuario"], []).append(fila["num_tel"])

            for usu in usuarios:
                lista = telefonos_por_usuario.get(usu["id_usuario"])
                usu["telefonos"] = ", ".join(lista) if lista else None
            return usuarios
        finally:
            cursor.close()

    # [OPCION 6 -> 8]
    def existe_usuario(self, id_usuario):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT 1 FROM usuario WHERE id_usuario = %s", (id_usuario,))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    # [OPCION 6 -> 8]
    def existe_usuario_datos(
        self, nombre_pila, primer_ap, segundo_ap, dir_calle, dir_numero, dir_colonia
    ):
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT 1 FROM usuario
                WHERE nombre_pila = %s
                  AND primer_ap = %s
                  AND IFNULL(segundo_ap, '') = %s
                  AND dir_calle = %s
                  AND dir_numero = %s
                  AND dir_colonia = %s
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

    # [OPCION 6 -> 8]
    def existe_telefono_usuario(self, id_usuario, num_tel):
        # Compara solo los digitos (ignora guiones o espacios)
        objetivo = normalizar_telefono(num_tel)
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "SELECT num_tel FROM telefono_usuario WHERE usuario = %s",
                (id_usuario,),
            )
            existentes = cursor.fetchall()
            return any(normalizar_telefono(f["num_tel"]) == objetivo for f in existentes)
        finally:
            cursor.close()

    # [OPCION 6 -> 8]
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

            vistos = set()
            for tel in usuario.telefonos:
                limpio = tel.strip()
                clave_tel = normalizar_telefono(limpio)
                if clave_tel in vistos:
                    continue
                vistos.add(clave_tel)
                cursor.execute(
                    "INSERT INTO telefono_usuario (num_tel, usuario) VALUES (%s, %s)",
                    (limpio, nuevo_id),
                )

            self.db.confirmar()
            return nuevo_id
        except Error:
            self.db.revertir()
            raise
        finally:
            cursor.close()

    # [OPCION 6 -> 8]
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
    # [OPCION 6 -> 9]
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

    # [OPCION 6 -> 9]
    def existe_empleado_user(self, nombre_user):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "SELECT 1 FROM empleado WHERE nombre_user = %s",
                (nombre_user.strip(),),
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    # [OPCION 6 -> 9]
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
