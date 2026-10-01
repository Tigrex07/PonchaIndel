# database/modelos.py
import pandas as pd
from database.conexion import obtener_conexion

# ==========================================
# GESTIÓN DE MAESTROS
# ==========================================

def crear_o_actualizar_maestro(nombre, tipo='NORMAL', activo=1):
    """
    Inserta un nuevo maestro si no existe o devuelve su ID actual.
    Limpia los espacios en blanco del nombre.
    """
    nombre_limpio = str(nombre).strip()
    if not nombre_limpio or nombre_limpio == 'nan':
        return None

    conn = obtener_conexion()
    cursor = conn.cursor()
    
    # Buscar si existe independientemente de mayúsculas/minúsculas
    cursor.execute("SELECT id FROM maestros WHERE UPPER(nombre) = UPPER(?)", (nombre_limpio,))
    res = cursor.fetchone()
    
    if res:
        id_maestro = res[0]
    else:
        cursor.execute("""
            INSERT INTO maestros (nombre, tipo, activo)
            VALUES (?, ?, ?)
        """, (nombre_limpio, tipo, activo))
        id_maestro = cursor.lastrowid
        conn.commit()
    
    conn.close()
    return id_maestro


def obtener_maestros():
    """Devuelve la lista de todos los maestros registrados."""
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, tipo, activo FROM maestros ORDER BY nombre ASC")
    maestros = cursor.fetchall()
    conn.close()
    return maestros

# ==========================================
# GESTIÓN DE PERIODOS / CUATRIMESTRES
# ==========================================

def crear_periodo(nombre, fecha_inicio, fecha_final):
    """Crea un nuevo cuatrimestre/periodo lectivo."""
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO periodo (nombre, fechaInicio, fechaFinal)
        VALUES (?, ?, ?)
    """, (nombre, fecha_inicio, fecha_final))
    id_periodo = cursor.lastrowid
    conn.commit()
    conn.close()
    return id_periodo


def obtener_periodos():
    """Devuelve la lista de todos los periodos registrados."""
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, fechaInicio, fechaFinal FROM periodo ORDER BY id DESC")
    periodos = cursor.fetchall()
    conn.close()
    return periodos

# ==========================================
# GESTIÓN DE TURNOS
# ==========================================

def obtener_turnos():
    """Devuelve el catálogo de turnos disponibles."""
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, horaEntrada, horaSalida, diassemana FROM turno ORDER BY id ASC")
    turnos = cursor.fetchall()
    conn.close()
    return turnos

# ==========================================
# GESTIÓN DE HORARIOS (ASIGNACIÓN)
# ==========================================

def asignar_horario_maestro(id_maestro, id_periodo, id_turno):
    """
    Asigna un turno a un maestro en un periodo específico.
    Si ya existe la relación, actualiza el turno asignado.
    """
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO horarios (idmaestro, idperiodo, idturno)
        VALUES (?, ?, ?)
        ON CONFLICT(idmaestro, idperiodo) DO UPDATE SET idturno = excluded.idturno
    """, (id_maestro, id_periodo, id_turno))
    id_horario = cursor.lastrowid
    conn.commit()
    conn.close()
    return id_horario


def obtener_horario_maestro(id_maestro, id_periodo):
    """Obtiene el turno asignado a un maestro en un periodo determinado."""
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT h.id, t.nombre, t.horaEntrada, t.horaSalida, t.diassemana
        FROM horarios h
        JOIN turno t ON h.idturno = t.id
        WHERE h.idmaestro = ? AND h.idperiodo = ?
    """, (id_maestro, id_periodo))
    horario = cursor.fetchone()
    conn.close()
    return horario

# ==========================================
# PERSISTENCIA DE PONCHADAS
# ==========================================

def guardar_ponchadas_desde_df(df_resumen):
    """
    Guarda todos los maestros y sus marcajes procesados desde el DataFrame.
    Procesa todas las filas en una sola transacción segura para evitar datos incompletos.
    """
    conn = obtener_conexion()
    cursor = conn.cursor()

    maestros_guardados = 0

    for _, row in df_resumen.iterrows():
        nombre = str(row['Nombre']).strip()
        fecha = str(row['Fecha']).strip()
        entrada = str(row['Entrada']).strip() if pd.notna(row['Entrada']) else None
        salida = str(row['Salida']).strip() if pd.notna(row['Salida']) else None

        if not nombre or nombre == 'nan':
            continue

        # 1. Registrar o recuperar id del maestro usando la misma transacción
        cursor.execute("SELECT id FROM maestros WHERE UPPER(nombre) = UPPER(?)", (nombre,))
        res = cursor.fetchone()

        if res:
            id_maestro = res[0]
        else:
            cursor.execute("INSERT INTO maestros (nombre, tipo, activo) VALUES (?, 'NORMAL', 1)", (nombre,))
            id_maestro = cursor.lastrowid
            maestros_guardados += 1

        # 2. Registrar marcaje de Entrada
        if entrada and entrada != 'nan':
            cursor.execute("""
                INSERT INTO ponchadas (idMaestro, fecha, hora, tipo)
                VALUES (?, ?, ?, 'ENTRADA')
            """, (id_maestro, fecha, entrada))

        # 3. Registrar marcaje de Salida
        if salida and salida != 'nan' and salida != entrada:
            cursor.execute("""
                INSERT INTO ponchadas (idMaestro, fecha, hora, tipo)
                VALUES (?, ?, ?, 'SALIDA')
            """, (id_maestro, fecha, salida))

    # Guardar cambios y cerrar conexión
    conn.commit()
    conn.close()
    print(f"Sincronización con SQLite exitosa. Nuevos maestros agregados: {maestros_guardados}")


# ==========================================
# GESTIÓN DE USUARIOS Y AUTENTICACIÓN
# ==========================================

def verificar_credenciales(correo, clave):
    """
    Valida el correo y la clave del usuario para iniciar sesión.
    Devuelve los datos del usuario si es correcto, o None si falla.
    """
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nombre, correo, rol 
        FROM usuarios 
        WHERE LOWER(correo) = LOWER(?) AND clave = ? AND activo = 1
    """, (correo.strip(), clave.strip()))
    usuario = cursor.fetchone()
    conn.close()
    return usuario # Devuelve (id, nombre, correo, rol)

def crear_usuario(nombre, correo, clave, rol='OPERADOR'):
    """
    Crea un nuevo usuario en la base de datos.
    """
    conn = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO usuarios (nombre, correo, clave, rol)
            VALUES (?, ?, ?, ?)
        """, (nombre.strip(), correo.strip(), clave.strip(), rol))
        conn.commit()
        id_usuario = cursor.lastrowid
    except Exception as e:
        id_usuario = None
        print(f"Error al crear usuario: {e}")
    finally:
        conn.close()
    return id_usuario

def obtener_usuarios():
    """Devuelve la lista de todos los usuarios registrados."""
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, correo, rol, activo FROM usuarios ORDER BY nombre ASC")
    usuarios = cursor.fetchall()
    conn.close()
    return usuarios