"""Consultas SQL del inicio de sesión (tabla empleado).

ÍNDICE (opción del menú -> método):
  [LOGIN]  ->  iniciar_sesion()
"""

from nucleo.conexion import GestorBase
from nucleo.modelos import Empleado


class GestorAuth(GestorBase):
    """Gestiona el inicio de sesión de empleados en texto plano."""

    # [LOGIN]
    def iniciar_sesion(self, nombre_user, contrasena):
        cursor = self.db.obtener_cursor()
        try:
            sql = """
                SELECT id_empleado, nombre_pila, primer_ap, segundo_ap, nombre_user, `contraseña`
                FROM empleado
                WHERE nombre_user = %s AND `contraseña` = %s
            """
            cursor.execute(sql, (nombre_user, contrasena))
            fila = cursor.fetchone()
            if not fila:
                return None

            return Empleado(
                id_empleado=fila["id_empleado"],
                nombre_pila=fila["nombre_pila"],
                primer_ap=fila["primer_ap"],
                segundo_ap=fila["segundo_ap"],
                nombre_user=fila["nombre_user"],
                contrasena=fila["contraseña"],
            )
        finally:
            cursor.close()
