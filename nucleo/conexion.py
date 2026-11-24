"""Archivo de la conexion. Aqui se ve como el programa se conecta a la base de datos MySQL (XAMPP)."""

import mysql.connector
from mysql.connector import Error


class ConexionDB:
    """Clase de la conexion. Guarda una sola conexion a MySQL que se reutiliza, y maneja guardar o deshacer cambios."""

    _instancia = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._conexion = None
        return cls._instancia

    def conectar(self):
        """Abre la conexion a la base de datos, o usa la que ya esta abierta."""
        if self._conexion is not None and self._conexion.is_connected():
            return self._conexion

        try:
            self._conexion = mysql.connector.connect(
                host="localhost",
                port=3306,
                user="root",
                password="",
                database="prestamos_bibliotecarios",
                charset="utf8mb4",
                collation="utf8mb4_general_ci",
                autocommit=False,
            )
            return self._conexion
        except Error as e:
            raise ConnectionError(
                f"No se pudo conectar a MySQL (verifica que XAMPP esté encendido): {e}"
            ) from e

    def obtener_cursor(self, diccionario=True):
        """Regresa un cursor para ejecutar consultas."""
        conexion = self.conectar()
        return conexion.cursor(dictionary=diccionario)

    def confirmar(self):
        """Guarda los cambios hechos (commit)."""
        if self._conexion and self._conexion.is_connected():
            self._conexion.commit()

    def revertir(self):
        """Deshace los cambios si hubo error (rollback)."""
        if self._conexion and self._conexion.is_connected():
            self._conexion.rollback()

    def cerrar(self):
        """Cierra la conexion."""
        if self._conexion and self._conexion.is_connected():
            self._conexion.close()
            self._conexion = None


class GestorBase:
    """Clase base de los gestores. Todos comparten la misma conexion."""

    def __init__(self):
        self.db = ConexionDB()
