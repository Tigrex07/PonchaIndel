# database/modelos.py
from database.conexion import obtener_conexion


def guardar_ponchadas_desde_df(df_resumen):
  """Recibe el DataFrame procesado con columnas [Nombre, Fecha, Entrada, Salida]

  y persiste los docentes y sus ponchadas en SQLite.
  """
  conn = obtener_conexion()
  cursor = conn.cursor()

  for _, row in df_resumen.iterrows():
    nombre = row['Nombre']
    fecha = row['Fecha']
    entrada = row['Entrada']
    salida = row['Salida']

    # 1. Obtener o registrar maestro (Por defecto tipo NORMAL)
    cursor.execute('SELECT id_maestro FROM maestros WHERE nombre = ?', (nombre,))
    res = cursor.fetchone()

    if res:
      id_maestro = res[0]
    else:
      num_emp_temp = f'EMP_{abs(hash(nombre)) % 1000000:06d}'
      cursor.execute(
          """
                INSERT INTO maestros (nombre, num_empleado, tipo_docente)
                VALUES (?, ?, 'NORMAL')
            """,
          (nombre, num_emp_temp),
      )
      id_maestro = cursor.lastrowid

    # 2. Registrar marcaje de Entrada
    if entrada:
      cursor.execute(
          """
                INSERT INTO ponchadas (id_maestro, fecha, hora, tipo_evento)
                VALUES (?, ?, ?, 'ENTRADA')
            """,
          (id_maestro, fecha, entrada),
      )

    # 3. Registrar marcaje de Salida
    if salida and salida != entrada:
      cursor.execute(
          """
                INSERT INTO ponchadas (id_maestro, fecha, hora, tipo_evento)
                VALUES (?, ?, ?, 'SALIDA')
            """,
          (id_maestro, fecha, salida),
      )

  conn.commit()
  conn.close()
  print('Datos guardados exitosamente en SQLite.')


  # ==========================================
# GESTIÓN DE PERIODOS / CUATRIMESTRES (1.3.1)
# ==========================================

def crear_periodo(nombre_periodo, fecha_inicio, fecha_fin):
    """
    Crea un nuevo cuatrimestre/periodo lectivo.
    Ejemplo: crear_periodo("Enero - Abril 2026", "2026-01-01", "2026-04-30")
    """
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO periodos (nombre_periodo, fecha_inicio, fecha_fin)
        VALUES (?, ?, ?)
    """, (nombre_periodo, fecha_inicio, fecha_fin))
    id_periodo = cursor.lastrowid
    conn.commit()
    conn.close()
    return id_periodo

def obtener_periodos():
    """
    Devuelve la lista de todos los periodos registrados.
    """
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT id_periodo, nombre_periodo, fecha_inicio, fecha_fin FROM periodos ORDER BY id_periodo DESC")
    periodos = cursor.fetchall()
    conn.close()
    return periodos

# ==========================================
# GESTIÓN DE HORARIOS BASE Y MAESTROS PA (1.3.2)
# ==========================================

def agregar_bloque_horario(id_maestro, id_periodo, dia_semana, hora_entrada, hora_salida):
    """
    Inserta un bloque de horario para un docente.
    Soporta múltiples bloques por día para Maestros PA.
    dia_semana: 1 = Lunes, 2 = Martes, ..., 7 = Domingo.
    Formato horas: 'HH:MM' (Ej. '08:00', '10:00')
    """
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO horarios_base (id_maestro, id_periodo, dia_semana, hora_entrada, hora_salida)
        VALUES (?, ?, ?, ?, ?)
    """, (id_maestro, id_periodo, dia_semana, hora_entrada, hora_salida))
    id_horario = cursor.lastrowid
    conn.commit()
    conn.close()
    return id_horario

def obtener_horarios_maestro(id_maestro, id_periodo):
    """
    Obtiene todos los bloques asignados a un maestro en un periodo específico.
    Los ordena por día de la semana y por hora de entrada.
    """
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id_horario, dia_semana, hora_entrada, hora_salida
        FROM horarios_base
        WHERE id_maestro = ? AND id_periodo = ?
        ORDER BY dia_semana ASC, hora_entrada ASC
    """, (id_maestro, id_periodo))
    horarios = cursor.fetchall()
    conn.close()
    return horarios

def eliminar_bloque_horario(id_horario):
    """
    Elimina un bloque de horario específico por su ID.
    """
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM horarios_base WHERE id_horario = ?", (id_horario,))
    conn.commit()
    conn.close()


#Traslape


def existe_traslape_horario(id_maestro, id_periodo, dia_semana, nueva_entrada, nueva_salida, id_horario_ignorar=None):
    """
    Verifica si las nuevas horas de entrada y salida se empalman/traslapan 
    con algún horario ya registrado para el mismo maestro, periodo y día de la semana.
    
    Retorna True si hay conflicto (traslape), False si el horario está libre.
    """
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    # Consulta todos los bloques existentes para ese maestro en ese día
    if id_horario_ignorar:
        cursor.execute("""
            SELECT id_horario, hora_entrada, hora_salida 
            FROM horarios_base 
            WHERE id_maestro = ? AND id_periodo = ? AND dia_semana = ? AND id_horario != ?
        """, (id_maestro, id_periodo, dia_semana, id_horario_ignorar))
    else:
        cursor.execute("""
            SELECT id_horario, hora_entrada, hora_salida 
            FROM horarios_base 
            WHERE id_maestro = ? AND id_periodo = ? AND dia_semana = ?
        """, (id_maestro, id_periodo, dia_semana))
        
    bloques = cursor.fetchall()
    conn.close()

    # Convertir 'HH:MM' a minutos desde el inicio del día para fácil comparación
    def h_a_minutos(hora_str):
        partes = hora_str.split(":")
        return int(partes[0]) * 60 + int(partes[1])

    e_nuevo = h_a_minutos(nueva_entrada)
    s_nuevo = h_a_minutos(nueva_salida)

    # Validar que la hora de entrada sea menor que la de salida
    if e_nuevo >= s_nuevo:
        return True  # Conflicto: la hora de entrada no puede ser igual o posterior a la salida

    for b in bloques:
        _, h_ent_exist, h_sal_exist = b
        e_exist = h_a_minutos(h_ent_exist)
        s_exist = h_a_minutos(h_sal_exist)

        # Lógica de traslape: dos intervalos (A, B) y (C, D) chocan si A < D y C < B
        if e_nuevo < s_exist and e_exist < s_nuevo:
            return True  # ¡Hay traslape!

    return False  # Horario libre de traslapes