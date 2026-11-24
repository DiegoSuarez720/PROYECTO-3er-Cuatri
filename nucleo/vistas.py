"""Funciones públicas para mostrar tablas de datos y confirmar continuación (usadas por todos los menús)."""

from nucleo.utilidades import (
    confirmar,
    mostrar_tabla,
    OperacionCancelada,
    PasoAnterior,
)


def mostrar_paises(datos):
    mostrar_tabla("Países", ["Clave", "Nombre"], [(d["clave"], d["nombre"]) for d in datos])


def mostrar_tipos(datos):
    mostrar_tabla(
        "Tipos de Obra", ["ID", "Tipo"], [(d["id_tipo"], d["tipo_obra"]) for d in datos]
    )


def mostrar_categorias(datos):
    mostrar_tabla(
        "Categorías", ["Código", "Género"], [(d["codigo"], d["genero"]) for d in datos]
    )


def mostrar_autores(datos):
    filas = [
        (d["num_id"], f"{d['nombre_pila']} {d['primer_ap']} {d['segundo_ap'] or ''}".strip())
        for d in datos
    ]
    mostrar_tabla("Autores", ["ID", "Nombre completo"], filas)


def mostrar_editoriales(datos):
    filas = [
        (d["id_editorial"], d["nombre"], f"{d['pais']} - {d['nombre_pais']}") for d in datos
    ]
    mostrar_tabla("Editoriales", ["ID", "Nombre", "País"], filas)


def mostrar_proveedores(datos):
    filas = [(d["RFC"], d["nombre_empresa"], d["telefonos"]) for d in datos]
    mostrar_tabla("Proveedores", ["RFC", "Empresa", "Teléfonos"], filas)


def mostrar_localizaciones(datos):
    filas = [
        (d["id_localizacion"], d["seccion"], d["pasillo"], d["estante"]) for d in datos
    ]
    mostrar_tabla("Localizaciones", ["ID", "Sección", "Pasillo", "Estante"], filas)


def mostrar_usuarios(datos):
    filas = [
        (
            d["id_usuario"],
            f"{d['nombre_pila']} {d['primer_ap']} {d['segundo_ap'] or ''}".strip(),
            f"{d['dir_calle']} #{d['dir_numero']}, {d['dir_colonia']}",
            d["telefonos"],
        )
        for d in datos
    ]
    mostrar_tabla("Usuarios", ["ID", "Nombre completo", "Dirección", "Teléfonos"], filas)


def mostrar_obras(datos):
    filas = [
        (
            d["isbn"],
            d["titulo"],
            d["anio"],
            d["tipo_obra"],
            d["genero"],
            d["total_autores"],
            d["total_ejemplares"],
        )
        for d in datos
    ]
    mostrar_tabla(
        "Obras",
        ["ISBN", "Título", "Año", "Tipo", "Categoría", "Autores", "Ejemplares"],
        filas,
    )


def mostrar_resumen_disponibles(datos):
    filas = [(d["isbn"], d["titulo"], d["disponibles"]) for d in datos]
    mostrar_tabla(
        "Obras con Ejemplares Disponibles",
        ["ISBN", "Título", "Disponibles"],
        filas,
    )


def mostrar_prestamos_activos_resumen(datos):
    filas = [
        (
            d["folio"],
            d["fecha_salida"],
            d["fecha_limite"],
            d["usuario"],
            d["pendientes"],
            d["empleado"],
        )
        for d in datos
    ]
    mostrar_tabla(
        "Préstamos Activos (Resumen)",
        ["Folio", "Salida", "Límite", "Usuario", "Pendientes", "Empleado"],
        filas,
    )


def mostrar_prestamos_activos_detalle(datos):
    filas = [
        (
            d["folio"],
            d["usuario"],
            d["fecha_salida"],
            d["fecha_limite"],
            d["obra"],
            d["titulo"],
            d["ejemplar"],
        )
        for d in datos
    ]
    mostrar_tabla(
        "Préstamos Activos (Detalle de Ejemplares)",
        ["Folio", "Usuario", "Salida", "Límite", "ISBN", "Título", "Ej. #"],
        filas,
    )


def mostrar_multas(datos):
    filas = [
        (
            d["id_multa"],
            d["prestamo"],
            d["usuario"],
            d["obra"],
            d["ejemplar"],
            d["dias_retraso"],
            f"${d['total']}",
            d["estado"],
        )
        for d in datos
    ]
    mostrar_tabla(
        "Multas",
        ["Multa #", "Folio", "Usuario", "ISBN", "Ej. #", "Días", "Total", "Estado"],
        filas,
    )


def confirmar_continuar(etiqueta):
    """Pregunta si desea continuar; 'atras'/'cancelar' regresan al menú."""
    try:
        return confirmar(etiqueta)
    except (OperacionCancelada, PasoAnterior):
        return False
