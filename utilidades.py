"""Funciones auxiliares en consola estándar (sin librerías externas) para validaciones y tablas."""

import os
from datetime import date, datetime
from decimal import Decimal, InvalidOperation


PALABRAS_CANCELAR = ("cancelar", "salir")
PALABRAS_ATRAS = ("atras", "atrás", "regresar", "volver")
FORMATO_FECHA = "%d-%m-%Y"


class OperacionCancelada(Exception):
    """Se lanza cuando el usuario escribe 'cancelar' o 'salir' para salir al menú."""


class PasoAnterior(Exception):
    """Se lanza cuando el usuario escribe 'atras' o 'regresar' para volver al paso anterior."""


def limpiar_pantalla():
    """Limpia la terminal según el sistema operativo."""
    os.system("cls" if os.name == "nt" else "clear")


def pausar(mensaje="Presiona ENTER para continuar..."):
    """Detiene la ejecución hasta que el usuario presione Enter."""
    input(f"\n{mensaje}")


def formatear_fecha(valor):
    """Convierte un objeto date/datetime a texto DD-MM-AAAA."""
    if valor is None:
        return "-"
    if isinstance(valor, date):
        return valor.strftime(FORMATO_FECHA)
    return str(valor)


def mostrar_titulo(titulo, subtitulo=""):
    """Muestra un encabezado limpio en texto plano."""
    linea = "=" * max(55, len(titulo) + 4)
    print(linea)
    print(f"  {titulo}")
    if subtitulo:
        print(f"  {subtitulo}")
    print(linea)
    print()


def mostrar_ayuda_cancelar():
    """Recuerda al usuario cómo volver un paso atrás o cancelar todo el registro."""
    print("(Escribe 'atras' o 'regresar' para el paso anterior | 'cancelar' o 'salir' para salir al menú)\n")


def mostrar_exito(mensaje):
    print(f"[OK] {mensaje}")


def mostrar_error(mensaje):
    print(f"[ERROR] {mensaje}")


def mostrar_aviso(mensaje):
    print(f"[AVISO] {mensaje}")


def mostrar_tabla(titulo, columnas, filas):
    """Dibuja una tabla alineada en texto plano formateando fechas como DD-MM-AAAA."""
    print(f"\n--- {titulo} ---")
    if not filas:
        print("(Sin registros para mostrar)\n")
        return

    filas_texto = []
    for fila in filas:
        fila_formateada = []
        for valor in fila:
            if valor is None:
                fila_formateada.append("-")
            elif isinstance(valor, date):
                fila_formateada.append(valor.strftime(FORMATO_FECHA))
            else:
                fila_formateada.append(str(valor))
        filas_texto.append(fila_formateada)

    anchos = []
    for i, col in enumerate(columnas):
        max_dato = max(len(f[i]) for f in filas_texto)
        anchos.append(max(len(str(col)), max_dato))

    separador = "+" + "+".join("-" * (ancho + 2) for ancho in anchos) + "+"
    encabezado = "| " + " | ".join(
        f"{str(col):<{anchos[i]}}" for i, col in enumerate(columnas)
    ) + " |"

    print(separador)
    print(encabezado)
    print(separador)
    for fila in filas_texto:
        linea = "| " + " | ".join(
            f"{fila[i]:<{anchos[i]}}" for i in range(len(columnas))
        ) + " |"
        print(linea)
    print(separador)
    print()


def _verificar_navegacion(texto, permitir_cancelar, permitir_atras):
    """Detecta comandos de navegación ('cancelar'/'salir' y 'atras'/'regresar')."""
    comando = texto.strip().lower()
    if permitir_cancelar and comando in PALABRAS_CANCELAR:
        raise OperacionCancelada()
    if permitir_atras and comando in PALABRAS_ATRAS:
        raise PasoAnterior()


def pedir_texto(
    etiqueta,
    max_len=None,
    obligatorio=True,
    valor_defecto=None,
    permitir_cancelar=True,
    permitir_atras=True,
):
    """Solicita una cadena validando si es obligatoria, longitud máxima y navegación."""
    while True:
        sufijo = f" [{valor_defecto}]" if valor_defecto is not None else ""
        if not obligatorio and valor_defecto is None:
            sufijo = " (opcional, Enter para omitir)"

        valor = input(f"{etiqueta}{sufijo}: ").strip()
        _verificar_navegacion(valor, permitir_cancelar, permitir_atras)

        if not valor:
            if valor_defecto is not None:
                valor = valor_defecto
            elif not obligatorio:
                return None
            else:
                mostrar_error("Este campo es obligatorio.")
                continue

        if max_len is not None and len(valor) > max_len:
            mostrar_error(f"Máximo {max_len} caracteres (ingresaste {len(valor)}).")
            continue

        return valor


def pedir_entero(
    etiqueta,
    minimo=None,
    maximo=None,
    permitir_cancelar=True,
    permitir_atras=True,
):
    """Solicita un número entero dentro de un rango opcional."""
    while True:
        texto = input(f"{etiqueta}: ").strip()
        _verificar_navegacion(texto, permitir_cancelar, permitir_atras)

        try:
            numero = int(texto)
        except ValueError:
            mostrar_error("Debes ingresar un número entero válido.")
            continue

        if minimo is not None and numero < minimo:
            mostrar_error(f"El valor debe ser mayor o igual a {minimo}.")
            continue
        if maximo is not None and numero > maximo:
            mostrar_error(f"El valor debe ser menor o igual a {maximo}.")
            continue

        return numero


def pedir_decimal(
    etiqueta,
    minimo=Decimal("0.00"),
    permitir_cancelar=True,
    permitir_atras=True,
):
    """Solicita un monto decimal exacto."""
    while True:
        texto = input(f"{etiqueta}: ").strip()
        _verificar_navegacion(texto, permitir_cancelar, permitir_atras)

        try:
            monto = Decimal(texto)
        except InvalidOperation:
            mostrar_error("Ingresa un monto numérico válido (ejemplo: 15.50).")
            continue

        if monto < minimo:
            mostrar_error(f"El monto debe ser mayor o igual a {minimo}.")
            continue

        return monto.quantize(Decimal("0.01"))


def pedir_fecha(
    etiqueta,
    permitir_hoy=True,
    permitir_cancelar=True,
    permitir_atras=True,
):
    """Solicita y valida inmediatamente una fecha en formato DD-MM-AAAA."""
    hoy = date.today()
    while True:
        hoy_txt = hoy.strftime(FORMATO_FECHA)
        ayuda = f" (DD-MM-AAAA, Enter = {hoy_txt})" if permitir_hoy else " (DD-MM-AAAA)"
        texto = input(f"{etiqueta}{ayuda}: ").strip()
        _verificar_navegacion(texto, permitir_cancelar, permitir_atras)

        if not texto and permitir_hoy:
            return hoy

        try:
            return datetime.strptime(texto, FORMATO_FECHA).date()
        except ValueError:
            mostrar_error("Formato de fecha inválido. Usa DD-MM-AAAA (ejemplo: 22-11-2026).")


def confirmar(etiqueta, permitir_cancelar=True, permitir_atras=True):
    """Pide confirmación Sí/No al usuario."""
    while True:
        resp = input(f"{etiqueta} (s/n): ").strip().lower()
        _verificar_navegacion(resp, permitir_cancelar, permitir_atras)

        if resp in ("s", "si", "sí"):
            return True
        if resp in ("n", "no"):
            return False
        mostrar_error("Responde 's' para sí o 'n' para no.")