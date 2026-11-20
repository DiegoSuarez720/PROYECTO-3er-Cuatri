"""Funciones auxiliares para menús, validaciones de entrada y tablas en terminal con rich."""

import os
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

consola = Console()


def limpiar_pantalla():
    """Limpia la terminal según el sistema operativo."""
    os.system("cls" if os.name == "nt" else "clear")


def pausar(mensaje="Presiona ENTER para continuar..."):
    """Detiene la ejecución hasta que el usuario presione Enter."""
    consola.input(f"\n[dim]{mensaje}[/dim]")


def mostrar_titulo(titulo, subtitulo=""):
    """Muestra un encabezado resaltado en un panel."""
    cuerpo = f"[bold cyan]{titulo}[/bold cyan]"
    if subtitulo:
        cuerpo += f"\n[dim]{subtitulo}[/dim]"
    consola.print(Panel(cuerpo, expand=False, border_style="cyan"))


def mostrar_exito(mensaje):
    consola.print(f"[bold green]✔ {mensaje}[/bold green]")


def mostrar_error(mensaje):
    consola.print(f"[bold red]✖ {mensaje}[/bold red]")


def mostrar_aviso(mensaje):
    consola.print(f"[bold yellow]⚠ {mensaje}[/bold yellow]")


def mostrar_tabla(titulo, columnas, filas):
    """Dibuja una tabla formateada en terminal con rich."""
    if not filas:
        mostrar_aviso(f"No hay registros para mostrar en '{titulo}'.")
        return

    tabla = Table(title=titulo, show_lines=True, header_style="bold cyan")
    for col in columnas:
        tabla.add_column(str(col))

    for fila in filas:
        tabla.add_row(*["-" if valor is None else str(valor) for valor in fila])

    consola.print(tabla)


def pedir_texto(etiqueta, max_len=None, obligatorio=True, valor_defecto=None):
    """Solicita una cadena validando si es obligatoria y su longitud máxima en SQL."""
    while True:
        sufijo = f" [{valor_defecto}]" if valor_defecto is not None else ""
        if not obligatorio and valor_defecto is None:
            sufijo = " (opcional, Enter para omitir)"

        valor = consola.input(f"[bold]{etiqueta}{sufijo}:[/bold] ").strip()

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


def pedir_entero(etiqueta, minimo=None, maximo=None):
    """Solicita un número entero dentro de un rango opcional."""
    while True:
        texto = consola.input(f"[bold]{etiqueta}:[/bold] ").strip()
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


def pedir_decimal(etiqueta, minimo=Decimal("0.00")):
    """Solicita un monto decimal exacto (para evitar errores de redondeo con dinero)."""
    while True:
        texto = consola.input(f"[bold]{etiqueta}:[/bold] ").strip()
        try:
            monto = Decimal(texto)
        except InvalidOperation:
            mostrar_error("Ingresa un monto numérico válido (ejemplo: 15.50).")
            continue

        if monto < minimo:
            mostrar_error(f"El monto debe ser mayor o igual a {minimo}.")
            continue

        return monto.quantize(Decimal("0.01"))


def pedir_fecha(etiqueta, permitir_hoy=True):
    """Solicita una fecha en formato AAAA-MM-DD."""
    hoy = date.today()
    while True:
        ayuda = f" (AAAA-MM-DD, Enter = {hoy})" if permitir_hoy else " (AAAA-MM-DD)"
        texto = consola.input(f"[bold]{etiqueta}{ayuda}:[/bold] ").strip()

        if not texto and permitir_hoy:
            return hoy

        try:
            return datetime.strptime(texto, "%Y-%m-%d").date()
        except ValueError:
            mostrar_error("Formato inválido. Usa AAAA-MM-DD (ejemplo: 2026-11-19).")


def confirmar(etiqueta):
    """Pide confirmación Sí/No al usuario."""
    while True:
        resp = consola.input(f"[bold yellow]{etiqueta} (s/n):[/bold yellow] ").strip().lower()
        if resp in ("s", "si", "sí"):
            return True
        if resp in ("n", "no"):
            return False
        mostrar_error("Responde 's' para sí o 'n' para no.")