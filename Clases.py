from datetime import datetime, timedelta

#CLASES(INDEPENDIENTES QUE LE PERTENECEN A OBRA Y EJEMPLAR)
class Categoria:
    contador_id = 1
    def __init__(self, descripcion):
        self.codigo = Categoria.contador_id
        Categoria.contador_id += 1
        self.descripcion = descripcion

class TipoObra:
    contador_id = 1
    def __init__(self, tipo_obra):
        self.id_tipo = TipoObra.contador_id
        TipoObra.contador_id += 1
        self.tipo_obra = tipo_obra 

class Editorial:
    contador_id = 1
    def __init__(self, nombre, pais):
        self.id_editorial = Editorial.contador_id
        Editorial.contador_id += 1
        self.nombre = nombre
        self.pais = pais

class Autor:
    contador_id = 1
    def __init__(self, nombre, primer_ap, segundo_ap):
        self.num_id = Autor.contador_id
        Autor.contador_id += 1
        self.nombre = nombre
        self.primer_ap = primer_ap
        self.segundo_ap = segundo_ap

class Localizacion:
    contador_id = 1
    def __init__(self, pasillo, estante, seccion):
        self.id_localizacion = Localizacion.contador_id
        Localizacion.contador_id += 1
        self.pasillo = pasillo
        self.estante = estante
        self.seccion = seccion

#CLASES CENTRALES
class Obra:
    def __init__(self, isbn, titulo, subtitulo, num_paginas, año_publicacion, categoria, tipo_obra, editorial):
        self.isbn = isbn
        self.titulo = titulo
        self.subtitulo = subtitulo
        self.num_paginas = num_paginas
        self.año_publicacion = año_publicacion
        self.categoria = categoria      
        self.tipo_obra = tipo_obra      
        self.editorial = editorial      
        self.autores = [] #Esta linea es porque una obra puede tener muchos autores

    def agregar_autor(self, autor):
        self.autores.append(autor)

class Ejemplar:
    contador_id = 1
    def __init__(self, obra, localizacion):
        self.num_consecutivo = Ejemplar.contador_id
        Ejemplar.contador_id += 1
        self.obra = obra
        self.localizacion = localizacion
        self.disponible = True

    def registrar_prestamo_ejemplar(self):
        if self.disponible:
            self.disponible = False
            return True
        else:
            print(f"El ejemplar {self.num_consecutivo} ya está prestado.")
            return False
        
#CLASES DE USUARIO Y PERSONAL
class Empleado:
    contador_id = 100
    def __init__(self, nombre, puesto, contraseña):
        self.id_empleado = Empleado.contador_id
        Empleado.contador_id += 1
        self.nombre = nombre
        self.puesto = puesto
        self.contraseña = contraseña

class Usuario:
    contador_id = 1000
    def __init__(self, nombre, direccion, telefono, contraseña):
        self.id_usuario = Usuario.contador_id
        Usuario.contador_id += 1
        self.nombre = nombre
        self.direccion = direccion
        self.telefono = telefono
        self.contraseña = contraseña

#CLASES CON CALCULOS
class Prestamo:
    contador_folio = 5000
    def __init__(self, usuario, empleado):
        self.folio = Prestamo.contador_folio
        Prestamo.contador_folio += 1
        self.usuario = usuario
        self.empleado = empleado
        self.ejemplares_prestados = []
        self.fecha_salida = datetime.now()
        self.fecha_limite = self.fecha_salida + timedelta(days=3)   #Aqui se calculan los 3 dias como limite del prestamo
        self.fecha_devolucion = None

    def agregar_ejemplar_a_prestamo(self, ejemplar):
        if ejemplar.registrar_prestamo_ejemplar():
            self.ejemplares_prestados.append(ejemplar)
            print(f"Ejemplar '{ejemplar.obra.titulo}' agregado al folio {self.folio}.")

class Multa:
    contador_id = 1
    def __init__(self, prestamo, dias_retraso):
        self.id_multa = Multa.contador_id
        Multa.contador_id += 1
        self.prestamo = prestamo
        self.dias_retraso = dias_retraso
        self.estado = "Pendiente"
        self.total = dias_retraso * 15   #Se cobran $15 pesos por cada dia de retraso