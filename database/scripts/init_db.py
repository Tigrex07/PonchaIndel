# database/scripts/init_db.py
from database.conexion import obtener_conexion


def inicializar_bd():
  """Crea el esquema inicial de la base de datos si no existe."""
  conn = obtener_conexion()
  cursor = conn.cursor()

  # Tabla Maestros
  cursor.execute("""
    CREATE TABLE IF NOT EXISTS maestros (
        id_maestro INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        num_empleado TEXT UNIQUE NOT NULL,
        tipo_docente TEXT CHECK(tipo_docente IN ('NORMAL', 'PA')) NOT NULL,
        activo INTEGER DEFAULT 1
    );
    """)

  # Tabla Periodos
  cursor.execute("""
    CREATE TABLE IF NOT EXISTS periodos (
        id_periodo INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_periodo TEXT NOT NULL,
        fecha_inicio TEXT NOT NULL,
        fecha_fin TEXT NOT NULL
    );
    """)

  # Tabla Horarios Base
  cursor.execute("""
    CREATE TABLE IF NOT EXISTS horarios_base (
        id_horario INTEGER PRIMARY KEY AUTOINCREMENT,
        id_maestro INTEGER NOT NULL,
        id_periodo INTEGER NOT NULL,
        dia_semana INTEGER CHECK(dia_semana BETWEEN 1 AND 7) NOT NULL,
        hora_entrada TEXT NOT NULL,
        hora_salida TEXT NOT NULL,
        FOREIGN KEY (id_maestro) REFERENCES maestros(id_maestro) ON DELETE CASCADE,
        FOREIGN KEY (id_periodo) REFERENCES periodos(id_periodo) ON DELETE CASCADE
    );
    """)

  # Tabla Ponchadas
  cursor.execute("""
    CREATE TABLE IF NOT EXISTS ponchadas (
        id_ponchada INTEGER PRIMARY KEY AUTOINCREMENT,
        id_maestro INTEGER NOT NULL,
        fecha TEXT NOT NULL,
        hora TEXT NOT NULL,
        tipo_evento TEXT CHECK(tipo_evento IN ('ENTRADA', 'SALIDA', 'DESCONOCIDO')) DEFAULT 'DESCONOCIDO',
        FOREIGN KEY (id_maestro) REFERENCES maestros(id_maestro) ON DELETE CASCADE
    );
    """)

  conn.commit()
  conn.close()
  print("Base de datos SQLite verificada e inicializada correctamente.")