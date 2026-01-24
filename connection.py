"""
Módulo de conexión a PostgreSQL
Usa la configuración de config.py para establecer la conexión
"""

import psycopg2
from psycopg2 import pool
import config


def get_connection():
    """
    Obtiene una conexión a la base de datos PostgreSQL
    usando la configuración de config.py
    
    Returns:
        psycopg2.connection: Objeto de conexión a la base de datos
    """
    try:
        connection = psycopg2.connect(**config.DB_CONFIG)
        return connection
    except psycopg2.Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        raise


def test_connection():
    """
    Prueba la conexión a la base de datos
    """
    try:
        conn = get_connection()
        print("¡Conexión exitosa a PostgreSQL!")
        conn.close()
        print("Conexión cerrada correctamente")
    except Exception as e:
        print(f"Error en la conexión: {e}")


if __name__ == "__main__":
    test_connection()

