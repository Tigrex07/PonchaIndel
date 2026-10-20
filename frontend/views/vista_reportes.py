# frontend/views/vista_reportes.py
import calendar
from datetime import datetime
import os
from tkinter import filedialog, messagebox
import customtkinter as ctk
import pandas as pd

from database.conexion import obtener_conexion
from database.modelos import obtener_maestros
from backend.gestor_plantillas import GestorPlantillas
from frontend.tema import COLORES
from backend.generador_excel import GeneradorExcelProgramatico
from backend.generador_pdf import GeneradorPDFPaginado


class VistaReportes(ctk.CTkFrame):

  def __init__(self, parent):
    super().__init__(parent, fg_color=COLORES["fondo_principal"])
    self.gestor_plantillas = GestorPlantillas()
    self.docentes_data = []
    self.checkboxes_maestros = {}
    self.quincenas_dict = {}

    self.crear_interfaz()
    self.actualizar_datos()

  def crear_interfaz(self):
    header_frame = ctk.CTkFrame(self, fg_color="transparent")
    header_frame.pack(fill="x", padx=20, pady=(15, 5))

    self.lbl_titulo = ctk.CTkLabel(
        header_frame,
        text="📊 Generador de Control Quincenal",
        font=ctk.CTkFont(size=26, weight="bold"),
        text_color=COLORES["texto_principal"],
    )
    self.lbl_titulo.pack(side="left")

    main_container = ctk.CTkFrame(self, fg_color="transparent")
    main_container.pack(fill="both", expand=True, padx=20, pady=10)

    # PANEL IZQUIERDO
    left_frame = ctk.CTkFrame(
        main_container,
        width=400,
        fg_color=COLORES["panel_secundario"],
        corner_radius=15,
        border_color=COLORES["borde_acento"],
        border_width=2,
    )
    left_frame.pack(side="left", fill="both", padx=(0, 15), pady=5)

    ctk.CTkLabel(
        left_frame,
        text="⚙️ Configuración del Documento",
        font=ctk.CTkFont(size=18, weight="bold"),
        text_color=COLORES["texto_principal"],
    ).pack(pady=(20, 10), padx=20, anchor="w")

    ctk.CTkLabel(
        left_frame,
        text="🏢 Área / Dirección (Para plantilla):",
        font=ctk.CTkFont(size=12, weight="bold"),
        text_color=COLORES["texto_secundario"],
    ).pack(anchor="w", padx=20, pady=(5, 5))

    self.entry_depto = ctk.CTkEntry(
        left_frame,
        placeholder_text="Ej. RECURSOS HUMANOS / PTC",
        fg_color=COLORES["fondo_principal"],
        text_color=COLORES["texto_principal"],
        border_width=1,
        border_color=COLORES["bordes"],
        height=40,
        font=ctk.CTkFont(size=13),
    )
    self.entry_depto.pack(fill="x", padx=20, pady=(0, 10))
    self.entry_depto.insert(0, "RECURSOS HUMANOS / ADMINISTRATIVOS Y PTC")

    ctk.CTkLabel(
        left_frame,
        text="📅 Rango a Evaluar:",
        font=ctk.CTkFont(size=12, weight="bold"),
        text_color=COLORES["texto_secundario"],
    ).pack(anchor="w", padx=20, pady=(5, 5))

    self.combo_periodo = ctk.CTkOptionMenu(
        left_frame,
        values=["Calculando quincenas..."],
        fg_color=COLORES["fondo_principal"],
        button_color=COLORES["panel_terciario"],
        button_hover_color=COLORES["primario_hover"],
        height=40,
        text_color=COLORES["texto_principal"],
        font=ctk.CTkFont(size=13, weight="bold"),
        command=self.al_cambiar_quincena,
    )
    self.combo_periodo.pack(fill="x", padx=20, pady=(0, 15))

    btn_box = ctk.CTkFrame(left_frame, fg_color="transparent")
    btn_box.pack(fill="x", padx=20, pady=(0, 10))

    self.btn_todos = ctk.CTkButton(
        btn_box,
        text="✅ Marcar Todos",
        width=140,
        height=35,
        corner_radius=8,
        fg_color=COLORES["panel_terciario"],
        hover_color=COLORES["primario"],
        text_color=COLORES["texto_principal"],
        command=lambda: self.toggle_todos(True),
    )
    self.btn_todos.pack(side="left")

    self.btn_ninguno = ctk.CTkButton(
        btn_box,
        text="❌ Limpiar",
        width=110,
        height=35,
        corner_radius=8,
        fg_color=COLORES["panel_terciario"],
        hover_color=COLORES["peligro"],
        text_color=COLORES["texto_principal"],
        command=lambda: self.toggle_todos(False),
    )
    self.btn_ninguno.pack(side="right")

    self.lbl_estado = ctk.CTkLabel(
        left_frame,
        text="Selecciona docentes para exportar.",
        font=ctk.CTkFont(size=13),
        text_color=COLORES["texto_secundario"],
    )
    self.lbl_estado.pack(side="bottom", pady=(0, 15))

    # Botones de exportación abajo en el panel izquierdo
    self.btn_pdf = ctk.CTkButton(
        left_frame,
        text="📑 Exportar Paginado en PDF",
        font=ctk.CTkFont(size=15, weight="bold"),
        fg_color=COLORES["primario"],
        hover_color=COLORES["primario_hover"],
        text_color="#FFFFFF",
        height=45,
        corner_radius=10,
        command=self.generar_pdf_quincenal,
    )
    self.btn_pdf.pack(side="bottom", fill="x", padx=20, pady=(5, 5))

    self.btn_generar = ctk.CTkButton(
        left_frame,
        text="📄 Generar Excel Oficial",
        font=ctk.CTkFont(size=16, weight="bold"),
        fg_color=COLORES["exito"],
        hover_color=COLORES["exito_hover"],
        text_color="#FFFFFF",
        height=50,
        corner_radius=10,
        command=self.generar_excel_quincenal,
    )
    self.btn_generar.pack(side="bottom", fill="x", padx=20, pady=(5, 5))

    self.scroll_maestros = ctk.CTkScrollableFrame(
        left_frame,
        fg_color=COLORES["fondo_principal"],
        corner_radius=10,
        border_width=1,
        border_color=COLORES["bordes"],
    )
    self.scroll_maestros.pack(
        side="top", fill="both", expand=True, padx=20, pady=(5, 10)
    )

    # PANEL DERECHO
    right_frame = ctk.CTkFrame(
        main_container,
        fg_color=COLORES["panel_secundario"],
        corner_radius=15,
        border_color=COLORES["bordes"],
        border_width=1,
    )
    right_frame.pack(side="right", fill="both", expand=True, pady=5)

    ctk.CTkLabel(
        right_frame,
        text="👁️ Vista Previa en Tiempo Real",
        font=ctk.CTkFont(size=18, weight="bold"),
        text_color=COLORES["texto_principal"],
    ).pack(pady=(20, 10), padx=25, anchor="w")

    self.txt_preview = ctk.CTkTextbox(
        right_frame,
        font=ctk.CTkFont(family="Consolas", size=13),
        fg_color=COLORES["fondo_principal"],
        text_color=COLORES["texto_principal"],
        border_width=1,
        border_color=COLORES["bordes"],
        corner_radius=12,
    )
    self.txt_preview.pack(fill="both", expand=True, padx=25, pady=(5, 25))

  def cargar_quincenas_inteligentes(self):
    try:
      conn = obtener_conexion()
      cursor = conn.cursor()
      cursor.execute("SELECT DISTINCT fecha FROM ponchadas ORDER BY fecha DESC")
      fechas_raw = cursor.fetchall()
      conn.close()

      self.quincenas_dict.clear()
      opciones_lista = []
      quincenas_vistas = set()

      meses_es = {
          1: "ENERO",
          2: "FEBRERO",
          3: "MARZO",
          4: "ABRIL",
          5: "MAYO",
          6: "JUNIO",
          7: "JULIO",
          8: "AGOSTO",
          9: "SEPTIEMBRE",
          10: "OCTUBRE",
          11: "NOVIEMBRE",
          12: "DICIEMBRE",
      }

      if fechas_raw:
        for (f_str,) in fechas_raw:
          try:
            dt = datetime.strptime(f_str, "%Y-%m-%d")
            y, m, d = dt.year, dt.month, dt.day
            mitad = 1 if d <= 15 else 2

            clave_unica = (y, m, mitad)
            if clave_unica not in quincenas_vistas:
              quincenas_vistas.add(clave_unica)
              nombre_mes = meses_es[m]

              if mitad == 1:
                texto_mostrar = f"1RA QUINCENA DE {nombre_mes} {y}"
                f_inicio = f"{y:04d}-{m:02d}-01"
                f_fin = f"{y:04d}-{m:02d}-15"
              else:
                texto_mostrar = f"2DA QUINCENA DE {nombre_mes} {y}"
                f_inicio = f"{y:04d}-{m:02d}-16"
                ultimo_dia = calendar.monthrange(y, m)[1]
                f_fin = f"{y:04d}-{m:02d}-{ultimo_dia}"

              self.quincenas_dict[texto_mostrar] = (f_inicio, f_fin)
              opciones_lista.append(texto_mostrar)
          except ValueError:
            continue

      if opciones_lista:
        self.combo_periodo.configure(values=opciones_lista)
        self.combo_periodo.set(opciones_lista[0])
      else:
        self.quincenas_dict["SIN DATOS"] = ("2000-01-01", "2099-12-31")
        self.combo_periodo.configure(values=["SIN DATOS"])
        self.combo_periodo.set("SIN DATOS")

    except Exception as e:
      print(f"Error cargando quincenas: {e}")

  def actualizar_datos(self):
    self.cargar_quincenas_inteligentes()
    for w in self.scroll_maestros.winfo_children():
      w.destroy()
    self.checkboxes_maestros.clear()

    filas = obtener_maestros()
    if filas:
      for r in filas:
        var_chk = ctk.BooleanVar(value=False)
        chk = ctk.CTkCheckBox(
            self.scroll_maestros,
            text=r[1],
            variable=var_chk,
            text_color=COLORES["texto_principal"],
            fg_color=COLORES["primario"],
            hover_color=COLORES["primario_hover"],
            font=ctk.CTkFont(size=13),
            command=self.actualizar_vista_previa_global,
        )
        chk.pack(anchor="w", padx=15, pady=8)
        self.checkboxes_maestros[r[0]] = (r[1], var_chk)
      self.actualizar_vista_previa_global()
    else:
      self.txt_preview.delete("1.0", "end")
      self.txt_preview.insert(
          "1.0", "⚠️ No hay maestros registrados. Sincroniza un CSV primero."
      )

  def toggle_todos(self, seleccionar: bool):
    for _, var_chk in self.checkboxes_maestros.values():
      var_chk.set(seleccionar)
    self.actualizar_vista_previa_global()

  def al_cambiar_quincena(self, valor_seleccionado):
    self.actualizar_vista_previa_global()

  def actualizar_vista_previa_global(self):
    ids = [i for i, (_, v) in self.checkboxes_maestros.items() if v.get()]
    if not ids:
      self.txt_preview.delete("1.0", "end")
      self.txt_preview.insert(
          "1.0",
          "ℹ️ Selecciona docentes a la izquierda para ver su reporte quincenal.",
      )
      self.lbl_estado.configure(
          text="0 docentes seleccionados", text_color=COLORES["texto_secundario"]
      )
      return

    quincena_activa = self.combo_periodo.get()
    f_inicio, f_fin = self.quincenas_dict.get(
        quincena_activa, ("2000-01-01", "2099-12-31")
    )

    try:
      conn = obtener_conexion()
      placeholders = ",".join(["?"] * len(ids))
      query = f"""
          SELECT DISTINCT m.nombre as Docente, p.fecha, p.hora, p.tipo 
          FROM ponchadas p 
          JOIN maestros m ON p.idMaestro = m.id 
          WHERE p.idMaestro IN ({placeholders}) 
            AND p.fecha >= ? AND p.fecha <= ?
          ORDER BY m.nombre ASC, p.fecha ASC, p.hora ASC
      """
      parametros = ids + [f_inicio, f_fin]
      df = pd.read_sql_query(query, conn, params=parametros)
      conn.close()

      self.txt_preview.delete("1.0", "end")
      if df.empty:
        self.txt_preview.insert(
            "end", f"No hay ponchadas registradas en {quincena_activa}.\n"
        )
      else:
        self.txt_preview.insert(
            "end",
            f"{'DOCENTE':<22} | {'FECHA':<12} | {'HORA':<10} | {'TIPO'}\n",
        )
        self.txt_preview.insert("end", "-" * 65 + "\n")
        for _, row in df.iterrows():
          self.txt_preview.insert(
              "end",
              f"{str(row['Docente'])[:20]:<22} | {str(row['fecha']):<12} |"
              f" {str(row['hora']):<10} | {str(row['tipo'])}\n",
          )

      self.lbl_estado.configure(
          text=f"{len(ids)} docentes listos", text_color=COLORES["primario"]
      )
    except Exception as e:
      self.txt_preview.insert("1.0", f"Error de consulta:\n{str(e)}")

  def generar_excel_quincenal(self):
    ids = [i for i, (_, v) in self.checkboxes_maestros.items() if v.get()]
    if not ids:
      return messagebox.showwarning(
          "Atención", "Selecciona al menos un maestro para exportar."
      )

    quincena_activa = self.combo_periodo.get()
    f_inicio, f_fin = self.quincenas_dict.get(
        quincena_activa, ("2000-01-01", "2099-12-31")
    )

    if quincena_activa == "SIN DATOS":
      return messagebox.showerror(
          "Error", "No hay datos en el sistema para exportar."
      )

    ruta = filedialog.asksaveasfilename(
        title="Guardar Excel Oficial",
        defaultextension=".xlsx",
        initialfile=f"Reporte_{quincena_activa.replace(' ', '_')}.xlsx",
        filetypes=[("Excel", "*.xlsx")],
    )
    if not ruta:
      return

    try:
      conn = obtener_conexion()
      placeholders = ",".join(["?"] * len(ids))
      query = f"""
          SELECT DISTINCT m.nombre as Nombre, p.fecha, p.hora, p.tipo 
          FROM ponchadas p 
          JOIN maestros m ON p.idMaestro = m.id 
          WHERE p.idMaestro IN ({placeholders}) 
            AND p.fecha >= ? AND p.fecha <= ?
          ORDER BY m.nombre ASC, p.fecha ASC
      """
      parametros = ids + [f_inicio, f_fin]
      df_raw = pd.read_sql_query(query, conn, params=parametros)
      conn.close()

      generador = GeneradorExcelProgramatico()
      generador.generar_control_quincenal(
          departamento=(self.entry_depto.get() or "RECURSOS HUMANOS"),
          periodo_texto=quincena_activa,
          fecha_inicio_str=f_inicio,
          fecha_fin_str=f_fin,
          df_registros=df_raw,
          ruta_salida=ruta,
      )

      messagebox.showinfo("Éxito", f"Reporte guardado con éxito en:\n{ruta}")

      if messagebox.askyesno(
          "Abrir Documento", "¿Deseas abrir el archivo Excel generado?"
      ):
        generador.abrir_documento_generado(ruta)

    except Exception as e:
      messagebox.showerror(
          "Error Crítico", f"No se pudo generar el documento:\n{str(e)}"
      )

  def generar_pdf_quincenal(self):
    ids = [i for i, (_, v) in self.checkboxes_maestros.items() if v.get()]
    if not ids:
      return messagebox.showwarning(
          "Atención", "Selecciona al menos un maestro para exportar."
      )

    quincena_activa = self.combo_periodo.get()
    f_inicio, f_fin = self.quincenas_dict.get(
        quincena_activa, ("2000-01-01", "2099-12-31")
    )

    if quincena_activa == "SIN DATOS":
      return messagebox.showerror(
          "Error", "No hay datos en el sistema para exportar."
      )

    ruta = filedialog.asksaveasfilename(
        title="Guardar Reporte en PDF",
        defaultextension=".pdf",
        initialfile=f"Reporte_{quincena_activa.replace(' ', '_')}.pdf",
        filetypes=[("PDF", "*.pdf")],
    )
    if not ruta:
      return

    try:
      conn = obtener_conexion()
      placeholders = ",".join(["?"] * len(ids))
      query = f"""
          SELECT DISTINCT m.nombre as Nombre, p.fecha, p.hora, p.tipo 
          FROM ponchadas p 
          JOIN maestros m ON p.idMaestro = m.id 
          WHERE p.idMaestro IN ({placeholders})
            AND p.fecha >= ? AND p.fecha <= ?
          ORDER BY m.nombre ASC, p.fecha ASC
      """
      parametros = ids + [f_inicio, f_fin]
      df_raw = pd.read_sql_query(query, conn, params=parametros)
      conn.close()

      generador_pdf = GeneradorPDFPaginado()
      generador_pdf.generar_control_quincenal_pdf(
          departamento=(self.entry_depto.get() or "RECURSOS HUMANOS"),
          periodo_texto=quincena_activa,
          fecha_inicio_str=f_inicio,
          fecha_fin_str=f_fin,
          df_registros=df_raw,
          ruta_salida=ruta,
      )
      messagebox.showinfo(
          "Éxito", f"Reporte PDF paginado guardado con éxito en:\n{ruta}"
      )

      if messagebox.askyesno(
          "Abrir Documento", "¿Abrir el archivo PDF generado?"
      ):
        generador_pdf.abrir_documento_generado(ruta)

    except Exception as e:
      messagebox.showerror(
          "Error Crítico", f"No se pudo generar el PDF:\n{str(e)}"
      )