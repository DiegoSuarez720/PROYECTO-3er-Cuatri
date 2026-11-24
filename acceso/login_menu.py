"""Archivo del login. Aqui se ve como el empleado escribe su usuario y contrasena para entrar."""

from mysql.connector import Error

from nucleo.utilidades import (
    OperacionCancelada,
    PasoAnterior,
    limpiar_pantalla,
    mostrar_error,
    mostrar_exito,
    mostrar_titulo,
    pausar,
    pedir_texto,
)


def iniciar_sesion(auth):
    """Pide usuario y contrasena. Regresa el empleado si son correctos, o None si escribe 'salir'."""
    while True:
        limpiar_pantalla()
        mostrar_titulo(
            "SISTEMA DE PRÉSTAMOS BIBLIOTECARIOS",
            "Inicio de sesión de empleados (escribe 'salir' en usuario para terminar)",
        )
        usuario = pedir_texto(
            "Usuario", max_len=30, permitir_cancelar=False, permitir_atras=False
        )
        if usuario.lower() in ("salir", "cancelar"):
            return None

        try:
            contrasena = pedir_texto(
                "Contraseña (escribe 'atras' para cambiar de usuario)", max_len=50
            )
        except (OperacionCancelada, PasoAnterior):
            continue

        try:
            empleado = auth.iniciar_sesion(usuario, contrasena)
        except Error as e:
            mostrar_error(f"Error al consultar empleado: {e}")
            pausar()
            continue

        if empleado:
            mostrar_exito(f"Bienvenido, {empleado.nombre_completo}.")
            pausar()
            return empleado

        mostrar_error("Usuario o contraseña incorrectos.")
        pausar()
