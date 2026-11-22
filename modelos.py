"""Clases POO correspondientes a las entidades del Modelo Relacional (20 tablas)."""

from datetime import timedelta
from decimal import Decimal


def _validar_texto(valor, campo, max_len, obligatorio=True):
    """Validador reutilizable para setters de cadenas."""
    if valor is None or str(valor).strip() == "":
        if obligatorio:
            raise ValueError(f"El campo '{campo}' es obligatorio.")
        return None
    limpio = str(valor).strip()
    if len(limpio) > max_len:
        raise ValueError(f"El campo '{campo}' no puede superar {max_len} caracteres.")
    return limpio


class Persona:
    """Clase base para personas del sistema (Autor, Usuario y Empleado)."""

    def __init__(self, nombre_pila, primer_ap, segundo_ap=None):
        self.nombre_pila = nombre_pila
        self.primer_ap = primer_ap
        self.segundo_ap = segundo_ap

    @property
    def nombre_pila(self):
        return self._nombre_pila

    @nombre_pila.setter
    def nombre_pila(self, valor):
        self._nombre_pila = _validar_texto(valor, "nombre_pila", 50)

    @property
    def primer_ap(self):
        return self._primer_ap

    @primer_ap.setter
    def primer_ap(self, valor):
        self._primer_ap = _validar_texto(valor, "primer_ap", 50)

    @property
    def segundo_ap(self):
        return self._segundo_ap

    @segundo_ap.setter
    def segundo_ap(self, valor):
        self._segundo_ap = _validar_texto(valor, "segundo_ap", 50, obligatorio=False)

    @property
    def nombre_completo(self):
        partes = [self._nombre_pila, self._primer_ap]
        if self._segundo_ap:
            partes.append(self._segundo_ap)
        return " ".join(partes)


class Autor(Persona):
    def __init__(self, nombre_pila, primer_ap, segundo_ap=None, num_id=None):
        super().__init__(nombre_pila, primer_ap, segundo_ap)
        self.num_id = num_id

    def __str__(self):
        return f"[{self.num_id}] {self.nombre_completo}"


class Usuario(Persona):
    def __init__(
        self,
        nombre_pila,
        primer_ap,
        dir_calle,
        dir_numero,
        dir_colonia,
        segundo_ap=None,
        id_usuario=None,
        telefonos=None,
    ):
        super().__init__(nombre_pila, primer_ap, segundo_ap)
        self.id_usuario = id_usuario
        self.dir_calle = dir_calle
        self.dir_numero = dir_numero
        self.dir_colonia = dir_colonia
        self.telefonos = telefonos or []

    @property
    def dir_calle(self):
        return self._dir_calle

    @dir_calle.setter
    def dir_calle(self, valor):
        self._dir_calle = _validar_texto(valor, "dir_calle", 30)

    @property
    def dir_numero(self):
        return self._dir_numero

    @dir_numero.setter
    def dir_numero(self, valor):
        self._dir_numero = _validar_texto(valor, "dir_numero", 10)

    @property
    def dir_colonia(self):
        return self._dir_colonia

    @dir_colonia.setter
    def dir_colonia(self, valor):
        self._dir_colonia = _validar_texto(valor, "dir_colonia", 50)

    def __str__(self):
        return f"[{self.id_usuario}] {self.nombre_completo} ({self.dir_calle} #{self.dir_numero}, {self.dir_colonia})"


class Empleado(Persona):
    def __init__(
        self,
        nombre_pila,
        primer_ap,
        nombre_user,
        contrasena,
        segundo_ap=None,
        id_empleado=None,
    ):
        super().__init__(nombre_pila, primer_ap, segundo_ap)
        self.id_empleado = id_empleado
        self.nombre_user = nombre_user
        self.contrasena = contrasena

    @property
    def nombre_user(self):
        return self._nombre_user

    @nombre_user.setter
    def nombre_user(self, valor):
        self._nombre_user = _validar_texto(valor, "nombre_user", 30)

    @property
    def contrasena(self):
        return self._contrasena

    @contrasena.setter
    def contrasena(self, valor):
        self._contrasena = _validar_texto(valor, "contraseña", 50)

    def __str__(self):
        return f"[{self.id_empleado}] {self.nombre_completo} (@{self.nombre_user})"


class Pais:
    def __init__(self, clave, nombre):
        self.clave = clave
        self.nombre = nombre

    @property
    def clave(self):
        return self._clave

    @clave.setter
    def clave(self, valor):
        self._clave = _validar_texto(valor, "clave", 5).upper()

    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        self._nombre = _validar_texto(valor, "nombre", 50)

    def __str__(self):
        return f"[{self.clave}] {self.nombre}"


class Categoria:
    def __init__(self, codigo, genero):
        self.codigo = codigo
        self.genero = genero

    @property
    def codigo(self):
        return self._codigo

    @codigo.setter
    def codigo(self, valor):
        self._codigo = _validar_texto(valor, "codigo", 5).upper()

    @property
    def genero(self):
        return self._genero

    @genero.setter
    def genero(self, valor):
        self._genero = _validar_texto(valor, "genero", 30)

    def __str__(self):
        return f"[{self.codigo}] {self.genero}"


class TipoObra:
    def __init__(self, tipo_obra, id_tipo=None):
        self.id_tipo = id_tipo
        self.tipo_obra = tipo_obra

    @property
    def tipo_obra(self):
        return self._tipo_obra

    @tipo_obra.setter
    def tipo_obra(self, valor):
        self._tipo_obra = _validar_texto(valor, "tipo_obra", 50)

    def __str__(self):
        return f"[{self.id_tipo}] {self.tipo_obra}"


class Editorial:
    def __init__(self, nombre, pais, id_editorial=None):
        self.id_editorial = id_editorial
        self.nombre = nombre
        self.pais = pais

    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        self._nombre = _validar_texto(valor, "nombre", 50)

    @property
    def pais(self):
        return self._pais

    @pais.setter
    def pais(self, valor):
        self._pais = _validar_texto(valor, "pais", 5).upper()

    def __str__(self):
        return f"[{self.id_editorial}] {self.nombre} ({self.pais})"


class Proveedor:
    def __init__(self, rfc, nombre_empresa, telefonos=None):
        self.rfc = rfc
        self.nombre_empresa = nombre_empresa
        self.telefonos = telefonos or []

    @property
    def rfc(self):
        return self._rfc

    @rfc.setter
    def rfc(self, valor):
        self._rfc = _validar_texto(valor, "RFC", 13).upper()

    @property
    def nombre_empresa(self):
        return self._nombre_empresa

    @nombre_empresa.setter
    def nombre_empresa(self, valor):
        self._nombre_empresa = _validar_texto(valor, "nombre_empresa", 50)

    def __str__(self):
        return f"[{self.rfc}] {self.nombre_empresa}"


class Localizacion:
    def __init__(self, estante, seccion, pasillo, id_localizacion=None):
        self.id_localizacion = id_localizacion
        self.estante = estante
        self.seccion = seccion
        self.pasillo = pasillo

    @property
    def estante(self):
        return self._estante

    @estante.setter
    def estante(self, valor):
        if not isinstance(valor, int) or valor < 0:
            raise ValueError("El estante debe ser un entero mayor o igual a 0.")
        self._estante = valor

    @property
    def seccion(self):
        return self._seccion

    @seccion.setter
    def seccion(self, valor):
        self._seccion = _validar_texto(valor, "seccion", 50)

    @property
    def pasillo(self):
        return self._pasillo

    @pasillo.setter
    def pasillo(self, valor):
        if not isinstance(valor, int) or valor < 0:
            raise ValueError("El pasillo debe ser un entero mayor o igual a 0.")
        self._pasillo = valor

    def __str__(self):
        return f"[{self.id_localizacion}] Sección: {self.seccion} | Pasillo: {self.pasillo} | Estante: {self.estante}"


class Obra:
    def __init__(
        self,
        isbn,
        titulo,
        anio_publicacion,
        num_paginas,
        tipo,
        categoria,
        subtitulo=None,
        autores=None,
        editoriales=None,
    ):
        self.isbn = isbn
        self.titulo = titulo
        self.subtitulo = subtitulo
        self.anio_publicacion = anio_publicacion
        self.num_paginas = num_paginas
        self.tipo = tipo
        self.categoria = categoria
        self.autores = autores or []
        self.editoriales = editoriales or []

    @property
    def isbn(self):
        return self._isbn

    @isbn.setter
    def isbn(self, valor):
        self._isbn = _validar_texto(valor, "isbn", 17)

    @property
    def titulo(self):
        return self._titulo

    @titulo.setter
    def titulo(self, valor):
        self._titulo = _validar_texto(valor, "titulo", 50)

    @property
    def subtitulo(self):
        return self._subtitulo

    @subtitulo.setter
    def subtitulo(self, valor):
        self._subtitulo = _validar_texto(valor, "subtitulo", 100, obligatorio=False)

    @property
    def anio_publicacion(self):
        return self._anio_publicacion

    @anio_publicacion.setter
    def anio_publicacion(self, valor):
        if not isinstance(valor, int) or valor < 1000 or valor > 2100:
            raise ValueError("El año de publicación debe ser un entero válido (1000-2100).")
        self._anio_publicacion = valor

    @property
    def num_paginas(self):
        return self._num_paginas

    @num_paginas.setter
    def num_paginas(self, valor):
        if not isinstance(valor, int) or valor <= 0:
            raise ValueError("El número de páginas debe ser mayor a 0.")
        self._num_paginas = valor

    @property
    def categoria(self):
        return self._categoria

    @categoria.setter
    def categoria(self, valor):
        self._categoria = _validar_texto(valor, "categoria", 5).upper()

    def __str__(self):
        return f"[{self.isbn}] {self.titulo} ({self.anio_publicacion})"


class Ejemplar:
    def __init__(self, obra, ejemplar, localizacion):
        self.obra = obra
        self.ejemplar = ejemplar
        self.localizacion = localizacion

    def __str__(self):
        return f"Obra {self.obra} - Ejemplar #{self.ejemplar} (Loc: {self.localizacion})"


class Prestamo:
    DIAS_PLAZO = 14

    def __init__(
        self,
        fecha_salida,
        empleado,
        usuario,
        fecha_limite=None,
        folio=None,
        ejemplares=None,
    ):
        self.folio = folio
        self.fecha_salida = fecha_salida
        self.fecha_limite = (
            fecha_limite
            if fecha_limite is not None
            else fecha_salida + timedelta(days=self.DIAS_PLAZO)
        )
        if self.fecha_limite < self.fecha_salida:
            raise ValueError("La fecha límite no puede ser anterior a la fecha de salida.")
        self.empleado = empleado
        self.usuario = usuario
        self.ejemplares = ejemplares or []

    def __str__(self):
        return f"Folio #{self.folio} | Usuario {self.usuario} | Límite: {self.fecha_limite}"


class Devolucion:
    def __init__(
        self,
        fecha_devolucion,
        empleado,
        obra,
        ejemplar,
        prestamo,
        id_devolucion=None,
    ):
        self.id_devolucion = id_devolucion
        self.fecha_devolucion = fecha_devolucion
        self.empleado = empleado
        self.obra = obra
        self.ejemplar = ejemplar
        self.prestamo = prestamo

    def __str__(self):
        return f"Devolución #{self.id_devolucion} | Préstamo #{self.prestamo} | {self.obra} (Ej. #{self.ejemplar})"


class Multa:
    def __init__(
        self,
        devolucion,
        monto_dia,
        dias_retraso,
        estado="Pendiente",
        id_multa=None,
        total=None,
    ):
        if dias_retraso <= 0:
            raise ValueError("Los días de retraso deben ser mayores a 0.")
        self.id_multa = id_multa
        self.devolucion = devolucion
        self.estado = estado
        self.monto_dia = Decimal(str(monto_dia)).quantize(Decimal("0.01"))
        self.dias_retraso = dias_retraso
        if total is not None:
            self.total = Decimal(str(total)).quantize(Decimal("0.01"))
        else:
            self.total = (self.monto_dia * dias_retraso).quantize(Decimal("0.01"))

    @property
    def estado(self):
        return self._estado

    @estado.setter
    def estado(self, valor):
        self._estado = _validar_texto(valor, "estado", 15)

    def __str__(self):
        return f"Multa #{self.id_multa} (Devolución #{self.devolucion}) | {self.dias_retraso} días | Total: ${self.total} [{self.estado}]"