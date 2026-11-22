"""Módulo de conexión Singleton a MySQL (XAMPP) para prestamos_bibliotecarios."""

import mysql.connector
from mysql.connector import Error


class ConexionDB:
    """Administra una única conexión reutilizable a MySQL con soporte de transacciones."""

    _instancia = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._conexion = None
        return cls._instancia

    def conectar(self):
        """Establece o reactiva la conexión a la base de datos en XAMPP."""
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
        """Devuelve un cursor listo para ejecutar consultas parametrizadas."""
        conexion = self.conectar()
        return conexion.cursor(dictionary=diccionario)

    def confirmar(self):
        """Confirma (commit) la transacción actual."""
        if self._conexion and self._conexion.is_connected():
            self._conexion.commit()

    def revertir(self):
        """Revierte (rollback) la transacción actual en caso de error."""
        if self._conexion and self._conexion.is_connected():
            self._conexion.rollback()

    def cerrar(self):
        """Cierra la conexión de forma segura."""
        if self._conexion and self._conexion.is_connected():
            self._conexion.close()
            self._conexion = None