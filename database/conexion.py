# database/conexion.py
import sqlite3

DB_NAME = "ponchaindel.db"

def obtener_conexion():
    """Abre y retorna la conexión a la BD activando llaves foráneas y un timeout de espera."""
    conn = sqlite3.connect(DB_NAME, timeout=10.0)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn