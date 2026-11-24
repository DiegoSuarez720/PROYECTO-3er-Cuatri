"""Consultas SQL de catálogos auxiliares (Opción 6 del menú principal).

ÍNDICE (opción del menú -> método):
  [OPCIÓN 6 -> 1]  PAISES: listar_paises, existe_pais, existe_pais_nombre, crear_pais
  [OPCIÓN 6 -> 2]  TIPOS DE OBRA: listar_tipos, existe_tipo, existe_tipo_nombre, crear_tipo
  [OPCIÓN 6 -> 3]  CATEGORIAS: listar_categorias, existe_categoria, existe_categoria_genero, crear_categoria
  [OPCIÓN 6 -> 4]  AUTORES: listar_autores, existe_autor, existe_autor_nombre, crear_autor
  [OPCIÓN 6 -> 5]  EDITORIALES: listar_editoriales, existe_editorial, existe_editorial_nombre, crear_editorial
  [OPCIÓN 6 -> 6]  PROVEEDORES Y TELEFONOS: listar_proveedores, existe_proveedor, existe_telefono_proveedor, crear_proveedor, agregar_telefono_proveedor
  [OPCIÓN 6 -> 7]  LOCALIZACIONES: listar_localizaciones, existe_localizacion, existe_localizacion_datos, crear_localizacion
  [OPCIÓN 6 -> 8]  USUARIOS Y TELEFONOS: listar_usuarios, existe_usuario, existe_usuario_datos, existe_telefono_usuario, crear_usuario, agregar_telefono_usuario
  [OPCIÓN 6 -> 9]  EMPLEADOS: listar_empleados, existe_empleado_user, crear_empleado
"""

from mysql.connector import Error

from nucleo.conexion import GestorBase
from nucleo.utilidades import normalizar_telefono


class GestorCatalogos(GestorBase):
    """Altas, listados y validadores de existencia / duplicados para todos los catálogos."""

    # --- PAISES ---
    # [OPCIÓN 6 -> 1]
    def listar_paises(self):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT clave, nombre FROM pais ORDER BY clave")
            return cursor.fetchall()
        finally:
            cursor.close()

    # [OPCIÓN 6 -> 1]
    def existe_pais(self, clave):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT 1 FROM pais WHERE UPPER(clave) = UPPER(%s)", (clave.strip(),))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    # [OPCIÓN 6 -> 1]
    def existe_pais_nombre(self, nombre):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "SELECT 1 FROM pais WHERE LOWER(TRIM(nombre)) = LOWER(%s)",
                (nombre.strip(),),
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    # [OPCIÓN 6 -> 1]
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
    # [OPCIÓN 6 -> 2]
    def listar_tipos(self):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT id_tipo, tipo_obra FROM tipo ORDER BY id_tipo")
            return cursor.fetchall()
        finally:
            cursor.close()

    # [OPCIÓN 6 -> 2]
    def existe_tipo(self, id_tipo):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT 1 FROM tipo WHERE id_tipo = %s", (id_tipo,))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    # [OPCIÓN 6 -> 2]
    def existe_tipo_nombre(self, tipo_obra):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "SELECT 1 FROM tipo WHERE LOWER(TRIM(tipo_obra)) = LOWER(%s)",
                (tipo_obra.strip(),),
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    # [OPCIÓN 6 -> 2]
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
    # [OPCIÓN 6 -> 3]
    def listar_categorias(self):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT codigo, genero FROM categoria ORDER BY codigo")
            return cursor.fetchall()
        finally:
            cursor.close()

    # [OPCIÓN 6 -> 3]
    def existe_categoria(self, codigo):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "SELECT 1 FROM categoria WHERE UPPER(codigo) = UPPER(%s)",
                (codigo.strip(),),
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    # [OPCIÓN 6 -> 3]
    def existe_categoria_genero(self, genero):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "SELECT 1 FROM categoria WHERE LOWER(TRIM(genero)) = LOWER(%s)",
                (genero.strip(),),
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    # [OPCIÓN 6 -> 3]
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
    # [OPCIÓN 6 -> 4]
    def listar_autores(self):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "SELECT num_id, nombre_pila, primer_ap, segundo_ap FROM autor ORDER BY num_id"
            )
            return cursor.fetchall()
        finally:
            cursor.close()

    # [OPCIÓN 6 -> 4]
    def existe_autor(self, num_id):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT 1 FROM autor WHERE num_id = %s", (num_id,))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    # [OPCIÓN 6 -> 4]
    def existe_autor_nombre(self, nombre_pila, primer_ap, segundo_ap=None):
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT 1 FROM autor
                WHERE LOWER(TRIM(nombre_pila)) = LOWER(%s)
                  AND LOWER(TRIM(primer_ap)) = LOWER(%s)
                  AND LOWER(TRIM(COALESCE(segundo_ap, ''))) = LOWER(%s)
            """
            cursor.execute(
                sql,
                (nombre_pila.strip(), primer_ap.strip(), (segundo_ap or "").strip()),
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    # [OPCIÓN 6 -> 4]
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
    # [OPCIÓN 6 -> 5]
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

    # [OPCIÓN 6 -> 5]
    def existe_editorial(self, id_editorial):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT 1 FROM editorial WHERE id_editorial = %s", (id_editorial,))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    # [OPCIÓN 6 -> 5]
    def existe_editorial_nombre(self, nombre, pais):
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT 1 FROM editorial
                WHERE LOWER(TRIM(nombre)) = LOWER(%s)
                  AND UPPER(pais) = UPPER(%s)
            """
            cursor.execute(sql, (nombre.strip(), pais.strip()))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    # [OPCIÓN 6 -> 5]
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
    # [OPCIÓN 6 -> 6]
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

    # [OPCIÓN 6 -> 6]
    def existe_proveedor(self, rfc):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT 1 FROM proveedor WHERE UPPER(RFC) = UPPER(%s)", (rfc.strip(),))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    # [OPCIÓN 6 -> 6]
    def existe_telefono_proveedor(self, rfc, telefono):
        """Detecta duplicados comparando solo dígitos (ignora guiones o espacios)."""
        objetivo = normalizar_telefono(telefono)
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "SELECT telefono FROM telefono_proveedor WHERE UPPER(proveedor) = UPPER(%s)",
                (rfc.strip(),),
            )
            existentes = cursor.fetchall()
            return any(normalizar_telefono(f["telefono"]) == objetivo for f in existentes)
        finally:
            cursor.close()

    # [OPCIÓN 6 -> 6]
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

    # [OPCIÓN 6 -> 6]
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
    # [OPCIÓN 6 -> 7]
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

    # [OPCIÓN 6 -> 7]
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

    # [OPCIÓN 6 -> 7]
    def existe_localizacion_datos(self, seccion, pasillo, estante):
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT 1 FROM localizacion
                WHERE LOWER(TRIM(seccion)) = LOWER(%s)
                  AND pasillo = %s
                  AND estante = %s
            """
            cursor.execute(sql, (seccion.strip(), pasillo, estante))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    # [OPCIÓN 6 -> 7]
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
    # [OPCIÓN 6 -> 8]
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

    # [OPCIÓN 6 -> 8]
    def existe_usuario(self, id_usuario):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute("SELECT 1 FROM usuario WHERE id_usuario = %s", (id_usuario,))
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    # [OPCIÓN 6 -> 8]
    def existe_usuario_datos(
        self, nombre_pila, primer_ap, segundo_ap, dir_calle, dir_numero, dir_colonia
    ):
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT 1 FROM usuario
                WHERE LOWER(TRIM(nombre_pila)) = LOWER(%s)
                  AND LOWER(TRIM(primer_ap)) = LOWER(%s)
                  AND LOWER(TRIM(COALESCE(segundo_ap, ''))) = LOWER(%s)
                  AND LOWER(TRIM(dir_calle)) = LOWER(%s)
                  AND LOWER(TRIM(dir_numero)) = LOWER(%s)
                  AND LOWER(TRIM(dir_colonia)) = LOWER(%s)
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

    # [OPCIÓN 6 -> 8]
    def existe_telefono_usuario(self, id_usuario, num_tel):
        """Detecta duplicados comparando solo dígitos (ignora guiones o espacios)."""
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

    # [OPCIÓN 6 -> 8]
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

    # [OPCIÓN 6 -> 8]
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
    # [OPCIÓN 6 -> 9]
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

    # [OPCIÓN 6 -> 9]
    def existe_empleado_user(self, nombre_user):
        cursor = self.db.obtener_cursor()
        try:
            cursor.execute(
                "SELECT 1 FROM empleado WHERE LOWER(TRIM(nombre_user)) = LOWER(%s)",
                (nombre_user.strip(),),
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    # [OPCIÓN 6 -> 9]
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
