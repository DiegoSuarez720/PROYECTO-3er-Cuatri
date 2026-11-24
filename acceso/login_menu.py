"""Archivo del login. Aqui se ve como el empleado escribe su usuario y contrasena para entrar."""

import shutil

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

LOGO = r"""
       @@@@@.                                                                           =@@@@       
        @*#@@@@@@@@@@@@@@@@                                              -@@@@@@@@@@@@@@@@#@@       
        @%***************#@@@@@@@@@@@@@@*                   @@@@@@@@@@@@@@@#***************@-       
        @@****************************#@@@@@@@@@@@@@@@@@@@@@@%****************************#@        
         @@@*************************************@ @***********************************@@@@@        
           @@@@**********************************@ @*******************************%@@@@-           
              @@@@*******************************@ @***************************#@@@@@               
                 @@@%****************************@ @***********************#@@@@@                   
                   @@@@**************************@ @********************@@@@@                       
                      @@@@**********************@@*@@@@@@@@@@@@@@@@@@@@@@                           
                         @@@@***************@@@@@:                =+@                               
                            @@@@***********@@                                                       
                              *@@@*******@@@                                                        
                                 @@@@%%@@@                                                          
                                    @@ @@    @@ :@@@@@@@@@                            @@            
                                      @    =@            @@@                       @@@@*            
                                     @@   @@                @@@               =@@@@@**@             
             @                         @@@                     @@@         @@@@@*****@@             
              @@@@@                                               @@     @@@*********@              
              @**#@@@@@@                                @@@@        @@  @@***********@              
              @@*******@@@@@@@                               @@@@    @@@@***********@@              
               @************%@@@@+      *@#          @@          @@@@@**************@               
               @****************@@@@@@@     @           @@@.     @*****************#@               
               @@*********************@    @@@@@@@         @@@@@@@*****************@@               
                @*********************@@@@@     @@@@@@@       @********************@                
                @*************************@   @@   -@  @@@@  @@*******************@@                
                @@************************@@@@    @@#@@   @@@@********************@                 
                 @@@@@@@@@@@@@@%*************@@@@@:=%#@  @@*********@@@@@@@@@@@@@@@                 
                              +@@@@@@@@@@@@@@@@@@@ @@@@@@@@@@@@@@@@@@                               
                                              %@@@@@@@@                                             
         @@@@   @@@@   @@@@@   @@@@  @@@@@   @@@   @      @@@@@  @@@@   @@@@    @@@    @@@@         
         @   @  @   @  @      @        @    @   @  @        @    @   @  @   @  @   @  @             
         @@@@   @@@@   @@@@    @@@     @    @@@@@  @        @    @@@@   @@@@   @   @   @@@          
         @      @  @   @          @    @    @   @  @        @    @   @  @  @   @   @      @         
         @      @   @  @@@@@  @@@@     @    @   @  @@@@@  @@@@@  @@@@   @   @   @@@   @@@@          
"""


def mostrar_logo_centrado():
    """Imprime el logo y el encabezado centrados segun el ancho actual de la consola."""
    ancho_consola = shutil.get_terminal_size((100, 30)).columns
    lineas = LOGO.strip("\n").splitlines()
    ancho_logo = max(len(linea) for linea in lineas)
    margen = max(0, (ancho_consola - ancho_logo) // 2)

    for linea in lineas:
        print(" " * margen + linea)

    print(("=" * 75).center(ancho_consola))
    print("SISTEMA DE PRÉSTAMOS BIBLIOTECARIOS".center(ancho_consola))
    print("Inicio de sesión de empleados (escribe 'salir' en usuario para terminar)".center(ancho_consola))
    print(("=" * 75).center(ancho_consola))


def iniciar_sesion(auth):
    """Pide usuario y contrasena. Regresa el empleado si son correctos, o None si escribe 'salir'."""
    while True:
        limpiar_pantalla()
        mostrar_logo_centrado()
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