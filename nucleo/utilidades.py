"""Archivo de utilidades. Aqui se ven las funciones de ayuda: validaciones, fichas, tablas y para pedir datos al usuario."""

import os
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation


PALABRAS_CANCELAR = ("cancelar", "salir")
PALABRAS_ATRAS = ("atras", "atrás", "regresar", "volver")
PALABRAS_RESERVADAS = PALABRAS_CANCELAR + PALABRAS_ATRAS + ("nuevo", "nueva")
FORMATO_FECHA = "%d-%m-%Y"
LIMITE_INT_MYSQL = 2147483647


class OperacionCancelada(Exception):
    """Error especial. Se usa cuando el usuario escribe 'cancelar' o 'salir' para volver al menu."""


class PasoAnterior(Exception):
    """Error especial. Se usa cuando el usuario escribe 'atras' o 'regresar' para volver al paso anterior."""


def limpiar_pantalla():
    """Limpia la pantalla de la terminal."""
    os.system("cls" if os.name == "nt" else "clear")


def pausar(mensaje="Presiona ENTER para continuar..."):
    """Espera a que el usuario presione Enter."""
    input(f"\n{mensaje}")


def formatear_fecha(valor):
    """Convierte una fecha a texto DD-MM-AAAA."""
    if valor is None:
        return "-"
    if isinstance(valor, date):
        return valor.strftime(FORMATO_FECHA)
    return str(valor)


def normalizar_telefono(texto):
    """Deja solo los numeros de un telefono para ver si esta repetido."""
    return re.sub(r"\D", "", texto or "")


# ==========================================================
# VALIDADORES (REVISAN QUE LOS DATOS TENGAN SENTIDO)
# ==========================================================
def validar_isbn(texto):
    """Revisa que el ISBN tenga formato de 10 o 13 digitos (guiones opcionales)."""
    valor = texto.strip().upper()
    if len(valor) > 17:
        return (False, "El ISBN no puede exceder 17 caracteres.")
    if not re.fullmatch(r"[0-9\-]+X?", valor):
        return (False, "El ISBN solo puede contener dígitos, guiones (y una 'X' final en ISBN-10).")
    if valor.startswith("-") or valor.endswith("-") or "--" in valor:
        return (False, "El ISBN tiene guiones mal ubicados.")

    limpio = valor.replace("-", "")
    if len(limpio) not in (10, 13):
        return (False, f"El ISBN debe tener exactamente 10 o 13 dígitos (ingresaste {len(limpio)}).")
    if len(limpio) == 13 and "X" in limpio:
        return (False, "Un ISBN-13 solo puede contener números (sin 'X').")
    if len(set(limpio)) == 1:
        return (False, "El ISBN no puede estar formado por el mismo dígito repetido.")
    return (True, "")


def validar_titulo(texto):
    """Acepta titulos con letras o numeros (ej. '1984'), pero no solo simbolos."""
    if not re.search(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]", texto):
        return (False, "Debe contener al menos una letra o número (no solo símbolos).")
    return (True, "")


def validar_texto_descriptivo(texto):
    """Para subtitulos, editoriales, empresas, calles, colonias y secciones: pide al menos una letra."""
    if len(texto.strip()) < 2:
        return (False, "Debe tener al menos 2 caracteres.")
    if not re.search(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", texto):
        return (False, "Debe contener al menos una letra (no solo números o símbolos).")
    return (True, "")


def validar_solo_letras(texto):
    """Para nombres de paises, tipos de obra y generos: solo letras, espacios y guiones."""
    valor = texto.strip()
    if not re.fullmatch(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ \-]+", valor):
        return (False, "Solo se permiten letras, espacios y guiones (sin números ni símbolos).")
    if len(re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", valor)) < 2:
        return (False, "Debe contener al menos 2 letras.")
    return (True, "")


def validar_nombre_persona(texto):
    """Para nombres y apellidos de autores, usuarios y empleados (acepta iniciales como 'H.')."""
    valor = texto.strip()
    if not re.fullmatch(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ .'\-]+", valor):
        return (False, "El nombre solo puede contener letras, espacios, puntos, guiones o apóstrofos.")
    if len(re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", valor)) < 2:
        return (False, "Debe contener al menos 2 letras.")
    return (True, "")


def validar_clave_pais(texto):
    """Clave del pais: de 2 a 5 letras, sin numeros ni espacios."""
    valor = texto.strip().upper()
    if not re.fullmatch(r"[A-Z]{2,5}", valor):
        return (False, "La clave de país debe tener entre 2 y 5 letras (ejemplo: MEX, ESP, USA).")
    return (True, "")


def validar_codigo_categoria(texto):
    """Codigo de categoria (Dewey o texto): de 2 a 5 letras o numeros, sin espacios."""
    valor = texto.strip().upper()
    if not re.fullmatch(r"[A-Z0-9]{2,5}", valor):
        return (False, "El código debe tener entre 2 y 5 letras o números sin espacios (ej. 005, FIC).")
    return (True, "")


def validar_rfc(texto):
    """Revisa que el RFC tenga forma correcta (12 caracteres empresa o 13 persona)."""
    valor = texto.strip().upper()
    coincidencia = re.fullmatch(r"[A-ZÑ&]{3,4}(\d{2})(\d{2})(\d{2})[A-Z0-9]{3}", valor)
    if not coincidencia:
        return (
            False,
            "RFC inválido. Usa 12 o 13 caracteres (3-4 letras + fecha AAMMDD + 3 alfanuméricos, ej. DIS890412AB1).",
        )
    yy, mm, dd = int(coincidencia.group(1)), int(coincidencia.group(2)), int(coincidencia.group(3))
    try:
        anio_ref = 2000 + yy if yy <= (date.today().year % 100) else 1900 + yy
        date(anio_ref, mm, dd)
    except ValueError:
        return (False, "La fecha AAMMDD contenida en el RFC no es una fecha calendario válida.")
    return (True, "")


def validar_telefono(texto):
    """Revisa que el telefono tenga de 10 a 15 digitos y no sea el mismo digito repetido."""
    valor = texto.strip()
    if not re.fullmatch(r"\+?[0-9\-\s()]+", valor):
        return (False, "El teléfono solo puede contener números, espacios, guiones, paréntesis o '+' inicial.")
    digitos = normalizar_telefono(valor)
    if len(digitos) < 10 or len(digitos) > 15:
        return (False, f"El teléfono debe contener entre 10 y 15 dígitos (ingresaste {len(digitos)}).")
    if len(set(digitos)) == 1:
        return (False, "El teléfono no puede consistir en el mismo dígito repetido.")
    return (True, "")


def validar_numero_domicilio(texto):
    """Revisa el numero de domicilio (acepta S/N o con al menos un digito)."""
    valor = texto.strip().upper()
    if valor in ("S/N", "SN"):
        return (True, "")
    if not re.fullmatch(r"[A-Za-z0-9\-\s/]+", texto.strip()) or not re.search(r"\d", valor):
        return (False, "Ingresa un número de domicilio válido (ejemplo: 412, 105-B o S/N).")
    return (True, "")


def validar_nombre_usuario(texto):
    """Revisa el usuario del empleado: de 3 a 30 caracteres, sin espacios y que no sea palabra reservada."""
    valor = texto.strip()
    if valor.lower() in PALABRAS_RESERVADAS:
        return (False, f"'{valor}' es una palabra reservada del sistema. Elige otro nombre de usuario.")
    if not re.fullmatch(r"[A-Za-z0-9._\-]{3,30}", valor):
        return (False, "El usuario debe tener entre 3 y 30 caracteres (solo letras, números, '.', '_' o '-').")
    if not re.search(r"[A-Za-z]", valor):
        return (False, "El nombre de usuario debe contener al menos una letra.")
    return (True, "")


def validar_contrasena(texto):
    """Revisa la contrasena del empleado nuevo: de 6 a 50 caracteres, sin espacios."""
    if len(texto) < 6:
        return (False, "La contraseña debe tener al menos 6 caracteres.")
    if " " in texto:
        return (False, "La contraseña no debe contener espacios.")
    return (True, "")


# ==========================================================
# MOSTRAR COSAS EN PANTALLA
# ==========================================================
def mostrar_titulo(titulo, subtitulo=""):
    """Muestra un titulo en texto plano."""
    linea = "=" * max(55, len(titulo) + 4)
    print(linea)
    print(f"  {titulo}")
    if subtitulo:
        print(f"  {subtitulo}")
    print(linea)
    print()


def mostrar_ayuda_cancelar():
    """Avisa al usuario como regresar un paso o cancelar."""
    print("(Escribe 'atras' o 'regresar' para el paso anterior | 'cancelar' o 'salir' para salir al menú)\n")


def mostrar_exito(mensaje):
    print(f"[OK] {mensaje}")


def mostrar_error(mensaje):
    print(f"[ERROR] {mensaje}")


def mostrar_aviso(mensaje):
    print(f"[AVISO] {mensaje}")


def mostrar_ficha(titulo, campos):
    """Muestra los datos en vertical (etiqueta: valor)."""
    ancho_etiqueta = max(len(str(etq)) for etq, _ in campos) if campos else 10
    linea = "-" * max(55, len(titulo) + 4)
    print(f"\n{linea}")
    print(f"  {titulo}")
    print(linea)

    for etiqueta, valor in campos:
        if valor is None:
            print(f"  {str(etiqueta):<{ancho_etiqueta}} : -")
        elif isinstance(valor, date):
            print(f"  {str(etiqueta):<{ancho_etiqueta}} : {valor.strftime(FORMATO_FECHA)}")
        elif isinstance(valor, (list, tuple)):
            if not valor:
                print(f"  {str(etiqueta):<{ancho_etiqueta}} : -")
            else:
                print(f"  {str(etiqueta):<{ancho_etiqueta}} : {valor[0]}")
                for extra in valor[1:]:
                    print(f"  {'':<{ancho_etiqueta}}   {extra}")
        else:
            print(f"  {str(etiqueta):<{ancho_etiqueta}} : {valor}")

    print(f"{linea}\n")


def mostrar_tabla(titulo, columnas, filas):
    """Dibuja una tabla en texto plano con las fechas como DD-MM-AAAA."""
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


# ==========================================================
# PEDIR DATOS Y REGRESAR O CANCELAR
# ==========================================================
def _verificar_navegacion(texto, permitir_cancelar, permitir_atras):
    """Revisa si el usuario escribio 'cancelar', 'salir', 'atras' o 'regresar'."""
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
    validador=None,
):
    """Pide un texto y revisa si es obligatorio, su largo maximo y si es valido."""
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

        if validador is not None:
            es_valido, msg_error = validador(valor)
            if not es_valido:
                mostrar_error(msg_error)
                continue

        return valor


def pedir_entero(
    etiqueta,
    minimo=None,
    maximo=LIMITE_INT_MYSQL,
    permitir_cancelar=True,
    permitir_atras=True,
    valor_defecto=None,
):
    """Pide un numero entero dentro de un rango. Si hay valor_defecto, Enter lo deja igual."""
    while True:
        sufijo = f" [{valor_defecto}]" if valor_defecto is not None else ""
        texto = input(f"{etiqueta}{sufijo}: ").strip()
        _verificar_navegacion(texto, permitir_cancelar, permitir_atras)

        if not texto and valor_defecto is not None:
            numero = valor_defecto
        else:
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
    maximo=Decimal("999999.99"),
    permitir_cancelar=True,
    permitir_atras=True,
):
    """Pide un monto con decimales dentro de un rango."""
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
        if maximo is not None and monto > maximo:
            mostrar_error(f"El monto debe ser menor o igual a {maximo}.")
            continue

        return monto.quantize(Decimal("0.01"))


def pedir_fecha(
    etiqueta,
    permitir_hoy=True,
    permitir_cancelar=True,
    permitir_atras=True,
    fecha_min=None,
    fecha_max=None,
    permitir_futuro=False,
):
    """Pide una fecha DD-MM-AAAA y revisa que no sea futura ni fuera de rango."""
    hoy = date.today()
    limite_sup = fecha_max
    if not permitir_futuro:
        limite_sup = hoy if limite_sup is None else min(limite_sup, hoy)

    while True:
        hoy_txt = hoy.strftime(FORMATO_FECHA)
        puede_usar_hoy = (
            permitir_hoy
            and (fecha_min is None or hoy >= fecha_min)
            and (limite_sup is None or hoy <= limite_sup)
        )
        ayuda = f" (DD-MM-AAAA, Enter = {hoy_txt})" if puede_usar_hoy else " (DD-MM-AAAA)"
        texto = input(f"{etiqueta}{ayuda}: ").strip()
        _verificar_navegacion(texto, permitir_cancelar, permitir_atras)

        if not texto and puede_usar_hoy:
            fecha_ingresada = hoy
        else:
            try:
                fecha_ingresada = datetime.strptime(texto, FORMATO_FECHA).date()
            except ValueError:
                mostrar_error("Formato de fecha inválido. Usa DD-MM-AAAA (ejemplo: 23-11-2026).")
                continue

        if not permitir_futuro and fecha_ingresada > hoy:
            mostrar_error(f"No se permiten fechas futuras (fecha máxima permitida: {hoy_txt}).")
            continue
        if fecha_min is not None and fecha_ingresada < fecha_min:
            mostrar_error(
                f"La fecha no puede ser anterior al {formatear_fecha(fecha_min)}."
            )
            continue
        if fecha_max is not None and fecha_ingresada > fecha_max:
            mostrar_error(
                f"La fecha no puede ser posterior al {formatear_fecha(fecha_max)}."
            )
            continue

        return fecha_ingresada


def confirmar(etiqueta, permitir_cancelar=True, permitir_atras=True):
    """Pregunta si o no al usuario."""
    while True:
        resp = input(f"{etiqueta} (s/n): ").strip().lower()
        _verificar_navegacion(resp, permitir_cancelar, permitir_atras)

        if resp in ("s", "si", "sí"):
            return True
        if resp in ("n", "no"):
            return False
        mostrar_error("Responde 's' para sí o 'n' para no.")