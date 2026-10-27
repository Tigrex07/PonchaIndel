import pandas as pd
from datetime import datetime
from database.conexion import obtener_conexion

# ==========================================
# INICIALIZACIÓN DE BASE DE DATOS Y TABLAS
# ==========================================

def inicializar_base_datos():
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS maestros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL,
            tipo TEXT CHECK(tipo IN ('NORMAL', 'PA')) NOT NULL,
            activo INTEGER DEFAULT 1
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS periodo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            fechaInicio TEXT NOT NULL,
            fechaFinal TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS turno (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL,
            horaEntrada TEXT NOT NULL,
            horaSalida TEXT NOT NULL,
            diassemana TEXT NOT NULL DEFAULT '1,2,3,4,5'
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS horarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            idmaestro INTEGER NOT NULL,
            idperiodo INTEGER NOT NULL,
            idturno INTEGER NOT NULL,
            activo INTEGER DEFAULT 1,
            FOREIGN KEY (idmaestro) REFERENCES maestros(id) ON DELETE CASCADE,
            FOREIGN KEY (idperiodo) REFERENCES periodo(id) ON DELETE CASCADE,
            FOREIGN KEY (idturno) REFERENCES turno(id) ON DELETE RESTRICT,
            CONSTRAINT uq_maestro_periodo UNIQUE (idmaestro, idperiodo)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ponchadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            idMaestro INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            hora TEXT NOT NULL,
            tipo TEXT CHECK(tipo IN ('ENTRADA', 'SALIDA', 'DESCONOCIDO')) DEFAULT 'DESCONOCIDO',
            FOREIGN KEY (idMaestro) REFERENCES maestros(id) ON DELETE CASCADE
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            correo TEXT UNIQUE NOT NULL,
            clave TEXT NOT NULL,
            rol TEXT CHECK(rol IN ('ADMIN', 'OPERADOR')) NOT NULL DEFAULT 'OPERADOR',
            activo INTEGER DEFAULT 1
        )
    """)
    
    conn.commit()
    conn.close()


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
        cursor.execute("UPDATE maestros SET activo = ? WHERE id = ?", (activo, id_maestro))
        conn.commit()
    else:
        cursor.execute("""
            INSERT INTO maestros (nombre, tipo, activo)
            VALUES (?, ?, ?)
        """, (nombre_limpio, tipo, activo))
        id_maestro = cursor.lastrowid
        conn.commit()
    
    conn.close()
    return id_maestro

def obtener_maestros(solo_activos=False):
    conn = obtener_conexion()
    cursor = conn.cursor()
    if solo_activos:
        cursor.execute("SELECT id, nombre, tipo, activo FROM maestros WHERE activo = 1 ORDER BY nombre ASC")
    else:
        cursor.execute("SELECT id, nombre, tipo, activo FROM maestros ORDER BY nombre ASC")
    maestros = cursor.fetchall()
    conn.close()
    return maestros

def cambiar_estado_maestro(id_maestro, activo):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("UPDATE maestros SET activo = ? WHERE id = ?", (activo, id_maestro))
    conn.commit()
    conn.close()


# ==========================================
# GESTIÓN DE PERIODOS / CUATRIMESTRES
# ==========================================

def calcular_cuatrimestre_info(fecha_dt):
    anio = fecha_dt.year
    mes = fecha_dt.month
    if 1 <= mes <= 4:
        return f"Enero - Abril {anio}", f"{anio}-01-01", f"{anio}-04-30"
    elif 5 <= mes <= 8:
        return f"Mayo - Agosto {anio}", f"{anio}-05-01", f"{anio}-08-31"
    else:
        return f"Septiembre - Diciembre {anio}", f"{anio}-09-01", f"{anio}-12-31"

def obtener_o_crear_periodo_por_fecha(fecha_str):
    try:
        dt = datetime.strptime(str(fecha_str).strip().split(" ")[0], "%Y-%m-%d")
    except ValueError:
        dt = datetime.now()
    
    nombre_p, ini_p, fin_p = calcular_cuatrimestre_info(dt)
    
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM periodo WHERE nombre = ?", (nombre_p,))
    res = cursor.fetchone()
    
    if res:
        id_periodo = res[0]
    else:
        cursor.execute("""
            INSERT INTO periodo (nombre, fechaInicio, fechaFinal)
            VALUES (?, ?, ?)
        """, (nombre_p, ini_p, fin_p))
        id_periodo = cursor.lastrowid
        conn.commit()
    
    conn.close()
    return id_periodo

def _obtener_o_crear_periodo_con_cursor(cursor, fecha_str):
    try:
        dt = datetime.strptime(str(fecha_str).strip().split(" ")[0], "%Y-%m-%d")
    except ValueError:
        dt = datetime.now()
    
    nombre_p, ini_p, fin_p = calcular_cuatrimestre_info(dt)
    cursor.execute("SELECT id FROM periodo WHERE nombre = ?", (nombre_p,))
    res = cursor.fetchone()
    
    if res:
        return res[0]
    else:
        cursor.execute("""
            INSERT INTO periodo (nombre, fechaInicio, fechaFinal)
            VALUES (?, ?, ?)
        """, (nombre_p, ini_p, fin_p))
        return cursor.lastrowid

def obtener_cuatrimestre_actual():
    return obtener_o_crear_periodo_por_fecha(datetime.now())

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

def crear_turno(nombre, hora_entrada, hora_salida, diassemana="LUN, MAR, MIE, JUE, VIE"):
    conn = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO turno (nombre, horaEntrada, horaSalida, diassemana)
            VALUES (?, ?, ?, ?)
        """, (nombre.upper(), hora_entrada, hora_salida, diassemana))
        conn.commit()
        id_turno = cursor.lastrowid
    except Exception as e:
        id_turno = None
        print(f"Error al crear turno: {e}")
    finally:
        conn.close()
    return id_turno

def obtener_turnos():
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, horaEntrada, horaSalida, diassemana FROM turno ORDER BY id ASC")
    turnos = cursor.fetchall()
    conn.close()
    return turnos


# ==========================================
# GESTIÓN DE HORARIOS (ASIGNACIÓN CON ACTIVO)
# ==========================================

def asignar_horario_maestro(id_maestro, id_periodo, id_turno, activo=1):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO horarios (idmaestro, idperiodo, idturno, activo)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(idmaestro, idperiodo) DO UPDATE SET idturno = excluded.idturno, activo = excluded.activo
    """, (id_maestro, id_periodo, id_turno, activo))
    id_horario = cursor.lastrowid
    if not id_horario:
        cursor.execute("SELECT id FROM horarios WHERE idmaestro = ? AND idperiodo = ?", (id_maestro, id_periodo))
        res = cursor.fetchone()
        if res: id_horario = res[0]
    conn.commit()
    conn.close()
    return id_horario

def cambiar_estado_horario(id_horario, activo):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("UPDATE horarios SET activo = ? WHERE id = ?", (activo, id_horario))
    conn.commit()
    conn.close()

def obtener_horario_maestro(id_maestro, id_periodo):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT h.id, t.nombre, t.horaEntrada, t.horaSalida, t.diassemana, h.activo
        FROM horarios h
        JOIN turno t ON h.idturno = t.id
        WHERE h.idmaestro = ? AND h.idperiodo = ?
    """, (id_maestro, id_periodo))
    horario = cursor.fetchone()
    conn.close()
    return horario


# ==========================================
# PERSISTENCIA DE PONCHADAS (CON CURSOR ÚNICO)
# ==========================================

def guardar_ponchadas_desde_df(df_resumen):
    conn = obtener_conexion()
    cursor = conn.cursor()
    maestros_guardados = 0

    try:
        for _, row in df_resumen.iterrows():
            nombre = str(row['Nombre']).strip()
            fecha = str(row['Fecha']).strip()
            entrada = str(row['Entrada']).strip() if pd.notna(row['Entrada']) else None
            salida = str(row['Salida']).strip() if pd.notna(row['Salida']) else None

            if not nombre or nombre == 'nan':
                continue

            # 1. Asegurar periodo usando el mismo cursor compartido (sin reabrir conexiones)
            _obtener_o_crear_periodo_con_cursor(cursor, fecha)

            # 2. Registrar o recuperar id del maestro
            cursor.execute("SELECT id FROM maestros WHERE UPPER(nombre) = UPPER(?)", (nombre,))
            res = cursor.fetchone()

            if res:
                id_maestro = res[0]
            else:
                cursor.execute("INSERT INTO maestros (nombre, tipo, activo) VALUES (?, 'NORMAL', 1)", (nombre,))
                id_maestro = cursor.lastrowid
                maestros_guardados += 1

            # 3. Registrar marcaje de Entrada
            if entrada and entrada != 'nan':
                cursor.execute("SELECT id FROM ponchadas WHERE idMaestro = ? AND fecha = ? AND tipo = 'ENTRADA'", (id_maestro, fecha))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO ponchadas (idMaestro, fecha, hora, tipo)
                        VALUES (?, ?, ?, 'ENTRADA')
                    """, (id_maestro, fecha, entrada))

            # 4. Registrar marcaje de Salida
            if salida and salida != 'nan' and salida != entrada:
                cursor.execute("SELECT id FROM ponchadas WHERE idMaestro = ? AND fecha = ? AND tipo = 'SALIDA'", (id_maestro, fecha))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO ponchadas (idMaestro, fecha, hora, tipo)
                        VALUES (?, ?, ?, 'SALIDA')
                    """, (id_maestro, fecha, salida))

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
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
            INSERT INTO usuarios (nombre, correo, clave, rol, activo)
            VALUES (?, ?, ?, ?, 1)
        """, (nombre.strip(), correo.strip(), clave.strip(), rol))
        conn.commit()
        id_usuario = cursor.lastrowid
    except Exception as e:
        id_usuario = None
        print(f"Error al crear usuario: {e}")
    finally:
        conn.close()
    return id_usuario

def cambiar_estado_usuario(id_usuario, activo):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET activo = ? WHERE id = ?", (activo, id_usuario))
    conn.commit()
    conn.close()

def obtener_usuarios():
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, correo, rol, activo FROM usuarios ORDER BY nombre ASC")
    usuarios = cursor.fetchall()
    conn.close()
    return usuarios


# ==========================================
# FUNCIONES AUXILIARES PARA HORARIOS
# ==========================================

def obtener_horario_activo_maestro(nombre_maestro):
    """Obtiene el último turno activo de un maestro para calcular retardos en el reporte."""
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.horaEntrada, t.horaSalida
        FROM horarios h
        JOIN maestros m ON h.idmaestro = m.id
        JOIN turno t ON h.idturno = t.id
        WHERE UPPER(m.nombre) = UPPER(?) AND h.activo = 1
        ORDER BY h.id DESC LIMIT 1
    """, (nombre_maestro,))
    res = cursor.fetchone()
    conn.close()
    return res if res else None


def obtener_horario_maestro_por_fecha(nombre_maestro, fecha_str):
    """Obtiene el turno del maestro correspondiente al periodo/cuatrimestre de una fecha dada."""
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.horaEntrada, t.horaSalida
        FROM horarios h
        JOIN maestros m ON h.idmaestro = m.id
        JOIN turno t ON h.idturno = t.id
        JOIN periodo p ON h.idperiodo = p.id
        WHERE UPPER(m.nombre) = UPPER(?)
          AND DATE(?) BETWEEN DATE(p.fechaInicio) AND DATE(p.fechaFinal)
        LIMIT 1
    """, (nombre_maestro, fecha_str))
    res = cursor.fetchone()
    conn.close()
    
    if not res:
        return obtener_horario_activo_maestro(nombre_maestro)
        
    return res


def asegurar_periodos_automaticos():
    """
    Crea automáticamente los tres cuatrimestres estándar (Enero-Abril, Mayo-Agosto, Septiembre-Diciembre)
    para un rango seguro: desde 4 años atrás hasta 4 años en el futuro.
    Esto garantiza que cualquier ponchada histórica o futura siempre tenga su cuatrimestre correspondiente
    sin arriesgar datos previos ni duplicar registros.
    """
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    anio_actual = datetime.now().year
    anos_rango = range(anio_actual - 4, anio_actual + 5) # 4 años atrás y 4 adelante
    
    cuatris_base = [
        ("Enero - Abril", "-01-01", "-04-30"),
        ("Mayo - Agosto", "-05-01", "-08-31"),
        ("Septiembre - Diciembre", "-09-01", "-12-31")
    ]
    
    for ano in anos_rango:
        for nombre_c, ini, fin in cuatris_base:
            nombre_completo = f"{nombre_c} {ano}"
            
            cursor.execute("SELECT id FROM periodo WHERE nombre = ?", (nombre_completo,))
            if not cursor.fetchone():
                f_ini = f"{ano}{ini}"
                f_fin = f"{ano}{fin}"
                cursor.execute("""
                    INSERT INTO periodo (nombre, fechaInicio, fechaFinal)
                    VALUES (?, ?, ?)
                """, (nombre_completo, f_ini, f_fin))
                
    conn.commit()
    conn.close()


# ==========================================
# INICIALIZACIÓN AUTOMÁTICA AL IMPORTAR
# ==========================================
inicializar_base_datos()
asegurar_periodos_automaticos()