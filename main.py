"""Punto de entrada: AplicacionBiblioteca y Menú Principal (opciones 1 a 7 y 0)."""

from acceso.login_menu import iniciar_sesion
from acceso.login_sql import GestorAuth
from listados.listados_menu import MenuListados
from nucleo.conexion import ConexionDB
from nucleo.utilidades import (
    limpiar_pantalla,
    mostrar_error,
    mostrar_titulo,
    pedir_entero,
)
from prestamos_y_multas.devoluciones_menu import MenuDevoluciones
from prestamos_y_multas.devoluciones_sql import GestorDevoluciones
from prestamos_y_multas.multas_menu import MenuMultas
from prestamos_y_multas.multas_sql import GestorMultas
from prestamos_y_multas.prestamos_menu import MenuPrestamos
from prestamos_y_multas.prestamos_sql import GestorPrestamos
from registros.catalogos_menu import MenuCatalogos
from registros.catalogos_sql import GestorCatalogos
from registros.obras_menu import MenuObras
from registros.obras_sql import GestorObras


class AplicacionBiblioteca:
    """Controla el flujo de menús en terminal y delega cada opción a su módulo."""

    def __init__(self):
        self.auth = GestorAuth()
        self.catalogos = GestorCatalogos()
        self.obras = GestorObras()
        self.prestamos = GestorPrestamos()
        self.devoluciones = GestorDevoluciones()
        self.multas = GestorMultas()
        self.empleado_activo = None

        # Menús que no dependen del empleado en sesión
        self.menu_obras = MenuObras(self.obras, self.catalogos)
        self.menu_multas = MenuMultas(self.multas)
        self.menu_catalogos = MenuCatalogos(self.catalogos)
        self.menu_listados = MenuListados(self.obras, self.prestamos, self.multas)

    def ejecutar(self):
        """Punto de entrada del programa."""
        try:
            ConexionDB().conectar()
        except ConnectionError as e:
            mostrar_error(str(e))
            return

        try:
            while True:
                empleado = iniciar_sesion(self.auth)
                if not empleado:
                    break
                self.empleado_activo = empleado
                self.menu_principal()
        finally:
            ConexionDB().cerrar()
            print("\nConexión cerrada. ¡Hasta luego!")

    # ==========================================================
    # MENÚ PRINCIPAL
    # ==========================================================
    def menu_principal(self):
        while True:
            limpiar_pantalla()
            mostrar_titulo(
                "MENÚ PRINCIPAL - SISTEMA BIBLIOTECARIO",
                f"Empleado en sesión: {self.empleado_activo.nombre_completo} (@{self.empleado_activo.nombre_user})",
            )
            print("1. Obras y abastecimiento")
            print("2. Asignar localización a ejemplares")
            print("3. Préstamos de ejemplares")
            print("4. Devoluciones de ejemplares")
            print("5. Multas por devolución tardía")
            print("6. Catálogos auxiliares (Autores, Usuarios, Proveedores, etc.)")
            print("7. Listados rápidos de apoyo")
            print("0. Cerrar sesión\n")

            opcion = pedir_entero(
                "Selecciona una opción",
                minimo=0,
                maximo=7,
                permitir_cancelar=False,
                permitir_atras=False,
            )

            if opcion == 1:
                self.menu_obras.flujo_obras()
            elif opcion == 2:
                self.menu_obras.flujo_asignar_localizacion()
            elif opcion == 3:
                # El empleado en sesión se pasa en el momento de abrir el menú
                MenuPrestamos(
                    self.prestamos,
                    self.obras,
                    self.multas,
                    self.catalogos,
                    self.empleado_activo,
                ).flujo_prestamos()
            elif opcion == 4:
                MenuDevoluciones(
                    self.devoluciones, self.empleado_activo
                ).flujo_devoluciones()
            elif opcion == 5:
                self.menu_multas.flujo_multas()
            elif opcion == 6:
                self.menu_catalogos.menu_catalogos()
            elif opcion == 7:
                self.menu_listados.menu_listados_apoyo()
            elif opcion == 0:
                self.empleado_activo = None
                break


if __name__ == "__main__":
    app = AplicacionBiblioteca()
    app.ejecutar()
