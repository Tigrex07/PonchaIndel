import pandas as pd
from database.conexion import obtener_conexion

# ==========================================
# GESTIÓN DE MAESTROS
# ==========================================

def crear_o_actualizar_maestro(nombre, tipo='NORMAL', activo=1):
    nombre_limpio = str(nombre).strip()
    if not nombre_limpio or nombre_limpio == 'nan':
        return None

    conn = obtener_conexion()
    cursor = conn.cursor()
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
# PERSISTENCIA DE PONCHADAS (FILTRO ANTI-BASURA AÑADIDO)
# ==========================================

def guardar_ponchadas_desde_df(df_resumen):
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

        # 1. Registrar o recuperar id del maestro
        cursor.execute("SELECT id FROM maestros WHERE UPPER(nombre) = UPPER(?)", (nombre,))
        res = cursor.fetchone()

        if res:
            id_maestro = res[0]
        else:
            cursor.execute("INSERT INTO maestros (nombre, tipo, activo) VALUES (?, 'NORMAL', 1)", (nombre,))
            id_maestro = cursor.lastrowid
            maestros_guardados += 1

        # 2. Registrar marcaje de Entrada (SOLO SI NO EXISTE)
        if entrada and entrada != 'nan':
            cursor.execute("SELECT id FROM ponchadas WHERE idMaestro = ? AND fecha = ? AND tipo = 'ENTRADA'", (id_maestro, fecha))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO ponchadas (idMaestro, fecha, hora, tipo)
                    VALUES (?, ?, ?, 'ENTRADA')
                """, (id_maestro, fecha, entrada))

        # 3. Registrar marcaje de Salida (SOLO SI NO EXISTE)
        if salida and salida != 'nan' and salida != entrada:
            cursor.execute("SELECT id FROM ponchadas WHERE idMaestro = ? AND fecha = ? AND tipo = 'SALIDA'", (id_maestro, fecha))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO ponchadas (idMaestro, fecha, hora, tipo)
                    VALUES (?, ?, ?, 'SALIDA')
                """, (id_maestro, fecha, salida))

    conn.commit()
    conn.close()
    print(f"Sincronización exitosa. Nuevos maestros: {maestros_guardados}")

# ==========================================
# GESTIÓN DE USUARIOS Y AUTENTICACIÓN
# ==========================================

def verificar_credenciales(correo, clave):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nombre, correo, rol 
        FROM usuarios 
        WHERE LOWER(correo) = LOWER(?) AND clave = ? AND activo = 1
    """, (correo.strip(), clave.strip()))
    usuario = cursor.fetchone()
    conn.close()
    return usuario

def crear_usuario(nombre, correo, clave, rol='OPERADOR'):
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
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, correo, rol, activo FROM usuarios ORDER BY nombre ASC")
    usuarios = cursor.fetchall()
    conn.close()
    return usuarios

# ==========================================
# FUNCIONES NUEVAS AGREGADAS (NECESARIAS PARA HORARIOS Y EXCEL)
# ==========================================

def crear_turno(nombre, hora_entrada, hora_salida, diassemana="LUN, MAR, MIE, JUE, VIE"):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO turno (nombre, horaEntrada, horaSalida, diassemana)
        VALUES (?, ?, ?, ?)
    """, (nombre.upper(), hora_entrada, hora_salida, diassemana))
    conn.commit()
    conn.close()

def obtener_horario_activo_maestro(nombre_maestro):
    """Obtiene el último turno asignado a un maestro para calcular sus retardos dinámicos en el Excel."""
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.horaEntrada, t.horaSalida
        FROM horarios h
        JOIN maestros m ON h.idmaestro = m.id
        JOIN turno t ON h.idturno = t.id
        WHERE UPPER(m.nombre) = UPPER(?)
        ORDER BY h.id DESC LIMIT 1
    """, (nombre_maestro,))
    res = cursor.fetchone()
    conn.close()
    return res