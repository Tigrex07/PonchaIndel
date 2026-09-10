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