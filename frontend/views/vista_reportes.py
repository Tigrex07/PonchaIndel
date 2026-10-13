# frontend/views/vista_reportes.py
from datetime import datetime
import os
from tkinter import filedialog, messagebox
import customtkinter as ctk
import pandas as pd

from database.conexion import obtener_conexion
from database.modelos import obtener_maestros
from backend.gestor_plantillas import GestorPlantillas


class VistaReportes(ctk.CTkFrame):

  def __init__(self, parent):
    super().__init__(parent)

    self.gestor_plantillas = GestorPlantillas()
    self.docentes_data = []  # Lista de tuplas (id, nombre)
    self.checkboxes_maestros = {}  # {id_maestro: (nombre, ctk.CTkCheckBox)}

    self.crear_interfaz()
    self.actualizar_datos()
    self.detectar_quincena_automatica()  # Detección inicial automática

  def crear_interfaz(self):
    # -------------------------------------------------------------
    # 1. ENCABEZADO PRINCIPAL
    # -------------------------------------------------------------
    header_frame = ctk.CTkFrame(self, fg_color="transparent")
    header_frame.pack(fill="x", padx=20, pady=(15, 5))

    self.lbl_titulo = ctk.CTkLabel(
        header_frame,
        text="📊 Centro de Reportes y Generador Quincenal",
        font=ctk.CTkFont(size=22, weight="bold"),
        text_color="#F3F4F6",
    )
    self.lbl_titulo.pack(side="left")

    # Contenedor Principal (2 Columnas)
    main_container = ctk.CTkFrame(self, fg_color="transparent")
    main_container.pack(fill="both", expand=True, padx=20, pady=10)

    # =============================================================
    # COLUMNA IZQUIERDA: Selección y Parámetros
    # =============================================================
    left_frame = ctk.CTkFrame(
        main_container, width=380, fg_color="#1E293B", corner_radius=12
    )
    left_frame.pack(side="left", fill="both", padx=(0, 10), pady=5)

    ctk.CTkLabel(
        left_frame,
        text="Parámetros y Docentes",
        font=ctk.CTkFont(size=16, weight="bold"),
        text_color="#93C5FD",
    ).pack(pady=(15, 5), padx=15, anchor="w")

    # 1. Área / Dirección (Celda A3)
    ctk.CTkLabel(
        left_frame,
        text="Área / Dirección (Celda A3):",
        font=ctk.CTkFont(size=11, weight="bold"),
        text_color="#E2E8F0",
    ).pack(anchor="w", padx=15, pady=(5, 2))

    self.entry_depto = ctk.CTkEntry(
        left_frame,
        placeholder_text="Ej. RECURSOS HUMANOS / PTC",
        fg_color="#0F172A",
        text_color="#FFFFFF",
        placeholder_text_color="#64748B",
        border_width=1,
        border_color="#334155",
        height=32,
    )
    self.entry_depto.pack(fill="x", padx=15, pady=(0, 8))
    self.entry_depto.insert(0, "RECURSOS HUMANOS / ADMINISTRATIVOS Y PTC")

    # 2. Periodo / Quincena (Celda A5) + Botón Inteligente
    periodo_label_box = ctk.CTkFrame(left_frame, fg_color="transparent")
    periodo_label_box.pack(fill="x", padx=15, pady=(5, 2))

    ctk.CTkLabel(
        periodo_label_box,
        text="Periodo / Quincena (Celda A5):",
        font=ctk.CTkFont(size=11, weight="bold"),
        text_color="#E2E8F0",
    ).pack(side="left")

    self.btn_auto_quincena = ctk.CTkButton(
        periodo_label_box,
        text="🔍 Auto-detectar",
        width=100,
        height=24,
        font=ctk.CTkFont(size=10, weight="bold"),
        fg_color="#2563EB",
        hover_color="#1D4ED8",
        command=self.detectar_quincena_automatica,
    )
    self.btn_auto_quincena.pack(side="right")

    self.entry_periodo = ctk.CTkEntry(
        left_frame,
        placeholder_text="Ej. 1RA QUINCENA DE OCTUBRE 2026",
        fg_color="#0F172A",
        text_color="#FFFFFF",
        placeholder_text_color="#64748B",
        border_width=1,
        border_color="#334155",
        height=32,
    )
    self.entry_periodo.pack(fill="x", padx=15, pady=(0, 12))

    # Botones de Control Rápido (Marcar Todos / Limpiar)
    btn_box = ctk.CTkFrame(left_frame, fg_color="transparent")
    btn_box.pack(fill="x", padx=15, pady=(0, 5))

    self.btn_todos = ctk.CTkButton(
        btn_box,
        text="Marcar Todos",
        width=130,
        height=28,
        fg_color="#334155",
        hover_color="#475569",
        command=lambda: self.toggle_todos(True),
    )
    self.btn_todos.pack(side="left")

    self.btn_ninguno = ctk.CTkButton(
        btn_box,
        text="Limpiar",
        width=100,
        height=28,
        fg_color="#334155",
        hover_color="#475569",
        command=lambda: self.toggle_todos(False),
    )
    self.btn_ninguno.pack(side="right")

    # Lista con Scroll para la selección múltiple de maestros
    self.scroll_maestros = ctk.CTkScrollableFrame(
        left_frame,
        fg_color="#0F172A",
        corner_radius=8,
        border_width=1,
        border_color="#334155",
    )
    self.scroll_maestros.pack(
        fill="both", expand=True, padx=15, pady=(5, 12)
    )

    # Botón Principal de Exportación
    self.btn_generar = ctk.CTkButton(
        left_frame,
        text="📄 Generar Control Quincenal Excel",
        font=ctk.CTkFont(size=14, weight="bold"),
        fg_color="#10B981",
        hover_color="#059669",
        height=42,
        command=self.generar_excel_quincenal,
    )
    self.btn_generar.pack(fill="x", padx=15, pady=10)

    self.lbl_estado = ctk.CTkLabel(
        left_frame,
        text="Selecciona uno o más maestros.",
        font=ctk.CTkFont(size=11),
        text_color="#64748B",
    )
    self.lbl_estado.pack(pady=(0, 10))

    # =============================================================
    # COLUMNA DERECHA: Vista Previa de Registros
    # =============================================================
    right_frame = ctk.CTkFrame(
        main_container, fg_color="#1E293B", corner_radius=12
    )
    right_frame.pack(side="right", fill="both", expand=True, pady=5)

    ctk.CTkLabel(
        right_frame,
        text="Vista Previa de Registros en Base de Datos",
        font=ctk.CTkFont(size=16, weight="bold"),
        text_color="#93C5FD",
    ).pack(pady=(15, 5), padx=20, anchor="w")

    self.txt_preview = ctk.CTkTextbox(
        right_frame,
        font=ctk.CTkFont(family="Consolas", size=12),
        fg_color="#0F172A",
        text_color="#F8FAFC",
        border_width=1,
        border_color="#334155",
        corner_radius=8,
    )
    self.txt_preview.pack(fill="both", expand=True, padx=20, pady=(5, 20))
    self.txt_preview.insert(
        "1.0", "Cargando registros de la Base de Datos SQLite...\n"
    )

  # -------------------------------------------------------------
  # DETECCIÓN INTELIGENTE DE QUINCENA
  # -------------------------------------------------------------

  def detectar_quincena_automatica(self):
    """Consulta la última fecha en la BD y determina automáticamente el texto de la quincena."""
    try:
      conn = obtener_conexion()
      cursor = conn.cursor()
      cursor.execute("SELECT MAX(fecha) FROM ponchadas")
      res = cursor.fetchone()
      conn.close()

      fecha_maxima = res[0] if res and res[0] else None

      if fecha_maxima:
        # Intentar parsear la fecha (formato esperado DD/MM/YYYY o YYYY-MM-DD)
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
          try:
            dt = datetime.strptime(fecha_maxima, fmt)
            dia = dt.day
            mes_nombre = dt.strftime("%B").upper()
            # Traducción básica de meses si sale en inglés
            meses_es = {
                "JANUARY": "ENERO",
                "FEBRUARY": "FEBRERO",
                "MARCH": "MARZO",
                "APRIL": "ABRIL",
                "MAY": "MAYO",
                "JUNE": "JUNIO",
                "JULY": "JULIO",
                "AUGUST": "AGOSTO",
                "SEPTEMBER": "SEPTIEMBRE",
                "OCTOBER": "OCTUBRE",
                "NOVEMBER": "NOVIEMBRE",
                "DECEMBER": "DICIEMBRE",
            }
            mes_txt = meses_es.get(mes_nombre, mes_nombre)
            anio = dt.year

            if dia <= 15:
              texto_quincena = (
                  f"1RA QUINCENA DE {mes_txt} DE {anio} (DEL 01 AL 15)"
              )
            else:
              texto_quincena = (
                  f"2DA QUINCENA DE {mes_txt} DE {anio} (DEL 16 AL 31)"
              )

            self.entry_periodo.delete(0, "end")
            self.entry_periodo.insert(0, texto_quincena)
            return
          except ValueError:
            continue

      # Valor por defecto si no hay registros válidos
      self.entry_periodo.delete(0, "end")
      self.entry_periodo.insert(0, "QUINCENA ACTUAL DE PRUEBA")

    except Exception as e:
      print(f"Error al auto-detectar quincena: {e}")
      self.entry_periodo.delete(0, "end")
      self.entry_periodo.insert(0, "QUINCENA ACTUAL DE PRUEBA")

  # -------------------------------------------------------------
  # GESTIÓN DE DATOS Y SELECCIÓN MÚLTIPLE
  # -------------------------------------------------------------

  def actualizar_datos(self):
    try:
      for widget in self.scroll_maestros.winfo_children():
        widget.destroy()

      self.checkboxes_maestros.clear()
      filas = obtener_maestros()

      if filas:
        self.docentes_data = filas
        for row in filas:
          id_m = row[0]
          nombre_m = row[1]

          var_chk = ctk.BooleanVar(value=False)
          chk = ctk.CTkCheckBox(
              self.scroll_maestros,
              text=nombre_m,
              variable=var_chk,
              text_color="#F1F5F9",
              fg_color="#2563EB",
              hover_color="#1D4ED8",
              command=self.actualizar_vista_previa_global,
          )
          chk.pack(anchor="w", padx=10, pady=6)
          self.checkboxes_maestros[id_m] = (nombre_m, var_chk)

        self.actualizar_vista_previa_global()
        self.detectar_quincena_automatica()
      else:
        self.txt_preview.delete("1.0", "end")
        self.txt_preview.insert(
            "1.0",
            "⚠️ No se encontraron maestros en la Base de Datos.\nCarga un"
            " archivo CSV en el Módulo 1 primero.",
        )
    except Exception as e:
      self.txt_preview.delete("1.0", "end")
      self.txt_preview.insert("1.0", f"Error al consultar la BD:\n{str(e)}")

  def toggle_todos(self, seleccionar: bool):
    for _, var_chk in self.checkboxes_maestros.values():
      var_chk.set(seleccionar)
    self.actualizar_vista_previa_global()

  def actualizar_vista_previa_global(self):
    ids_seleccionados = [
        id_m
        for id_m, (_, var) in self.checkboxes_maestros.items()
        if var.get()
    ]

    if not ids_seleccionados:
      self.txt_preview.delete("1.0", "end")
      self.txt_preview.insert(
          "1.0",
          "ℹ️ Ningún maestro seleccionado.\nMarca las casillas a la izquierda"
          " para ver sus registros.",
      )
      self.lbl_estado.configure(
          text="0 docentes seleccionados", text_color="#64748B"
      )
      return

    try:
      conn = obtener_conexion()
      placeholders = ",".join(["?"] * len(ids_seleccionados))
      query = f"""
                SELECT m.nombre as Docente, p.fecha, p.hora, p.tipo 
                FROM ponchadas p
                JOIN maestros m ON p.idMaestro = m.id
                WHERE p.idMaestro IN ({placeholders})
                ORDER BY m.nombre ASC, p.fecha ASC, p.hora ASC
            """
      df = pd.read_sql_query(query, conn, params=ids_seleccionados)
      conn.close()

      self.txt_preview.delete("1.0", "end")
      self.txt_preview.insert(
          "end",
          f"=== REGISTROS DE LOS {len(ids_seleccionados)} DOCENTES"
          " SELECCIONADOS ===\n\n",
      )

      if df.empty:
        self.txt_preview.insert(
            "end", "No hay ponchadas registradas para los docentes marcados.\n"
        )
      else:
        self.txt_preview.insert(
            "end",
            f"{'DOCENTE':<20} | {'FECHA':<12} | {'HORA':<8} | {'TIPO'}\n",
        )
        self.txt_preview.insert("end", "-" * 55 + "\n")

        for _, row in df.iterrows():
          doc = str(row["Docente"])[:18]
          f = str(row["fecha"])
          h = str(row["hora"])
          t = str(row["tipo"])
          self.txt_preview.insert(
              "end", f"{doc:<20} | {f:<12} | {h:<8} | {t}\n"
          )

      self.lbl_estado.configure(
          text=f"{len(ids_seleccionados)} docentes seleccionados",
          text_color="#10B981",
      )

    except Exception as e:
      self.txt_preview.delete("1.0", "end")
      self.txt_preview.insert(
          "1.0", f"Error al consultar registros:\n{str(e)}"
      )

  # -------------------------------------------------------------
  # GENERACIÓN E INYECCIÓN EN LA PLANTILLA OFICIAL
  # -------------------------------------------------------------

  def generar_excel_quincenal(self):
    ids_seleccionados = [
        id_m
        for id_m, (_, var) in self.checkboxes_maestros.items()
        if var.get()
    ]

    if not ids_seleccionados:
      messagebox.showwarning(
          "Atención",
          "Por favor selecciona al menos un maestro de la lista para"
          " exportar.",
      )
      return

    ruta_salida = filedialog.asksaveasfilename(
        title="Guardar Control Quincenal Oficial",
        defaultextension=".xlsx",
        initialfile="Control_Quincenal_Oficial.xlsx",
        filetypes=[("Archivos de Excel", "*.xlsx")],
    )

    if not ruta_salida:
      return

    try:
      conn = obtener_conexion()
      placeholders = ",".join(["?"] * len(ids_seleccionados))
      query = f"""
                SELECT m.nombre as Nombre, p.fecha, p.hora, p.tipo 
                FROM ponchadas p
                JOIN maestros m ON p.idMaestro = m.id
                WHERE p.idMaestro IN ({placeholders})
                ORDER BY m.nombre ASC, p.fecha ASC
            """
      df_raw = pd.read_sql_query(query, conn, params=ids_seleccionados)
      conn.close()

      registros_finales = []
      for nombre_docente, sub_df in df_raw.groupby("Nombre"):
        fechas = sub_df["fecha"].unique()
        for f in fechas:
          dia_data = sub_df[sub_df["fecha"] == f]
          entradas = dia_data[dia_data["tipo"] == "ENTRADA"]["hora"].values
          salidas = dia_data[dia_data["tipo"] == "SALIDA"]["hora"].values

          registros_finales.append({
              "Nombre": nombre_docente,
              "Fecha": f,
              "Entrada": entradas[0] if len(entradas) > 0 else "--:--",
              "Salida": salidas[0] if len(salidas) > 0 else "--:--",
          })

      df_inyectar = pd.DataFrame(registros_finales)

      area_texto = self.entry_depto.get() or "RECURSOS HUMANOS"
      periodo_texto = self.entry_periodo.get() or "QUINCENA ACTUAL"

      # Inyección mediante GestorPlantillas (A3, A5 y filas desde la 11)
      self.gestor_plantillas.inyectar_control_quincenal(
          departamento=area_texto,
          periodo=periodo_texto,
          df_registros=df_raw,
          ruta_salida=ruta_salida,
      )

      messagebox.showinfo(
          "Éxito",
          f"Reporte quincenal generado exitosamente en:\n{ruta_salida}",
      )

      if messagebox.askyesno(
          "Abrir Documento", "¿Deseas abrir el archivo Excel oficial ahora?"
      ):
        self.gestor_plantillas.abrir_documento_generado(ruta_salida)

    except Exception as e:
      messagebox.showerror(
          "Error de Generación",
          f"Ocurrió un error al inyectar en la plantilla:\n{str(e)}",
      )