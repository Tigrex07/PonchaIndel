# database/conexion.py
import sqlite3

DB_NAME = "ponchaindel.db"


def obtener_conexion():
  """Abre y retorna la conexión a la BD activando la restricción de llaves foráneas."""
  conn = sqlite3.connect(DB_NAME)
  conn.execute("PRAGMA foreign_keys = ON;")
  return conn