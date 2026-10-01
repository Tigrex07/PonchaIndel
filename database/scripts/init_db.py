# database/scripts/init_db.py
from database.conexion import obtener_conexion

def inicializar_bd():
    """Inicializa la base de datos de acuerdo a la revisión del esquema propuesta."""
    conn = obtener_conexion()
    cursor = conn.cursor()

    # 1. Tabla Maestros
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS maestros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL,
        tipo TEXT CHECK(tipo IN ('NORMAL', 'PA')) NOT NULL,
        activo INTEGER DEFAULT 1
    );
    """)

    # 2. Tabla Periodo (Cuatrimestres)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS periodo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        fechaInicio TEXT NOT NULL,
        fechaFinal TEXT NOT NULL
    );
    """)

    # 3. Tabla Turno (Catálogo de turnos con días asignados)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS turno (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL,
        horaEntrada TEXT NOT NULL,  -- Formato 'HH:MM'
        horaSalida TEXT NOT NULL,   -- Formato 'HH:MM'
        diassemana TEXT NOT NULL DEFAULT '1,2,3,4,5' -- '1,2,3,4,5' = Lunes a Viernes
    );
    """)

    # Insertar turnos predeterminados iniciales si no existen
    cursor.execute("INSERT OR IGNORE INTO turno (id, nombre, horaEntrada, horaSalida, diassemana) VALUES (1, 'Matutino', '07:00', '15:00', '1,2,3,4,5');")
    cursor.execute("INSERT OR IGNORE INTO turno (id, nombre, horaEntrada, horaSalida, diassemana) VALUES (2, 'Vespertino', '14:00', '22:00', '1,2,3,4,5');")

    # 4. Tabla Horarios (Asignación de Turno por Maestro y Periodo)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS horarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        idmaestro INTEGER NOT NULL,
        idperiodo INTEGER NOT NULL,
        idturno INTEGER NOT NULL,
        FOREIGN KEY (idmaestro) REFERENCES maestros(id) ON DELETE CASCADE,
        FOREIGN KEY (idperiodo) REFERENCES periodo(id) ON DELETE CASCADE,
        FOREIGN KEY (idturno) REFERENCES turno(id) ON DELETE RESTRICT,
        CONSTRAINT uq_maestro_periodo UNIQUE (idmaestro, idperiodo)
    );
    """)

    # 5. Tabla Ponchadas (Marcajes procesados)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ponchadas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        idMaestro INTEGER NOT NULL,
        fecha TEXT NOT NULL,  -- Formato 'YYYY-MM-DD'
        hora TEXT NOT NULL,   -- Formato 'HH:MM:SS'
        tipo TEXT CHECK(tipo IN ('ENTRADA', 'SALIDA', 'DESCONOCIDO')) DEFAULT 'DESCONOCIDO',
        FOREIGN KEY (idMaestro) REFERENCES maestros(id) ON DELETE CASCADE
    );
    """)

    # 6. Tabla Usuarios (Autenticación y Roles)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        correo TEXT UNIQUE NOT NULL,
        clave TEXT NOT NULL, -- Guardará el hash encriptado de la contraseña
        rol TEXT CHECK(rol IN ('ADMIN', 'OPERADOR')) NOT NULL DEFAULT 'OPERADOR',
        activo INTEGER DEFAULT 1
    );
    """)


    # Insertar un usuario Administrador por defecto si no existe
    # Contraseña temporal por defecto: admin123 (Se recomienda implementar hashing con hashlib o bcrypt)
    cursor.execute("""
        INSERT OR IGNORE INTO usuarios (id, nombre, correo, clave, rol)
        VALUES (1, 'Tigrex Team', 'admin@ponchaindel.com', '1234', 'ADMIN');
    """)

    conn.commit()
    conn.close()
    print("Base de datos SQLite actualizada e inicializada con éxito con la nueva revisión.")

if __name__ == "__main__":
    inicializar_bd()