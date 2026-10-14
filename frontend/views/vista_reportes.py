from datetime import datetime
import os
from tkinter import filedialog, messagebox
import customtkinter as ctk
import pandas as pd

from database.conexion import obtener_conexion
from database.modelos import obtener_maestros
from backend.gestor_plantillas import GestorPlantillas
from frontend.tema import COLORES

class VistaReportes(ctk.CTkFrame):
  def __init__(self, parent):
    super().__init__(parent, fg_color=COLORES["fondo_principal"])
    self.gestor_plantillas = GestorPlantillas()
    self.docentes_data = []
    self.checkboxes_maestros = {}
    self.crear_interfaz()
    self.actualizar_datos()

  def crear_interfaz(self):
    header_frame = ctk.CTkFrame(self, fg_color="transparent")
    header_frame.pack(fill="x", padx=20, pady=(15, 5))

    self.lbl_titulo = ctk.CTkLabel(
        header_frame, text="📊 Generador de Control Quincenal",
        font=ctk.CTkFont(size=26, weight="bold"), text_color=COLORES["texto_principal"]
    )
    self.lbl_titulo.pack(side="left")

    main_container = ctk.CTkFrame(self, fg_color="transparent")
    main_container.pack(fill="both", expand=True, padx=20, pady=10)

    # PANEL IZQUIERDO
    left_frame = ctk.CTkFrame(main_container, width=400, fg_color=COLORES["panel_secundario"], corner_radius=15, border_color=COLORES["borde_acento"], border_width=2)
    left_frame.pack(side="left", fill="both", padx=(0, 15), pady=5)

    ctk.CTkLabel(left_frame, text="⚙️ Configuración del Documento", font=ctk.CTkFont(size=18, weight="bold"), text_color=COLORES["texto_principal"]).pack(pady=(20, 10), padx=20, anchor="w")

    ctk.CTkLabel(left_frame, text="🏢 Área / Dirección (Para plantilla):", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORES["texto_secundario"]).pack(anchor="w", padx=20, pady=(5, 5))
    
    self.entry_depto = ctk.CTkEntry(
        left_frame, placeholder_text="Ej. RECURSOS HUMANOS / PTC", fg_color=COLORES["fondo_principal"], 
        text_color=COLORES["texto_principal"], border_width=1, border_color=COLORES["bordes"], height=40, font=ctk.CTkFont(size=13)
    )
    self.entry_depto.pack(fill="x", padx=20, pady=(0, 10))
    self.entry_depto.insert(0, "RECURSOS HUMANOS / ADMINISTRATIVOS Y PTC")

    periodo_box = ctk.CTkFrame(left_frame, fg_color="transparent")
    periodo_box.pack(fill="x", padx=20, pady=(5, 5))

    ctk.CTkLabel(periodo_box, text="📅 Quincena Actual:", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORES["texto_secundario"]).pack(side="left")
    self.btn_auto_quincena = ctk.CTkButton(
        periodo_box, text="⚡ Auto-detectar", width=110, height=28, corner_radius=6,
        font=ctk.CTkFont(size=11, weight="bold"), fg_color=COLORES["primario"], hover_color=COLORES["primario_hover"], command=self.detectar_quincena_automatica
    )
    self.btn_auto_quincena.pack(side="right")

    self.entry_periodo = ctk.CTkEntry(
        left_frame, placeholder_text="Ej. 1RA QUINCENA...", fg_color=COLORES["fondo_principal"], 
        text_color=COLORES["texto_principal"], border_width=1, border_color=COLORES["bordes"], height=40, font=ctk.CTkFont(size=13)
    )
    self.entry_periodo.pack(fill="x", padx=20, pady=(0, 15))

    btn_box = ctk.CTkFrame(left_frame, fg_color="transparent")
    btn_box.pack(fill="x", padx=20, pady=(0, 10))
    
    self.btn_todos = ctk.CTkButton(
        btn_box, text="✅ Marcar Todos", width=140, height=35, corner_radius=8,
        fg_color=COLORES["panel_terciario"], hover_color=COLORES["primario"], text_color=COLORES["texto_principal"], command=lambda: self.toggle_todos(True)
    )
    self.btn_todos.pack(side="left")
    self.btn_ninguno = ctk.CTkButton(
        btn_box, text="❌ Limpiar", width=110, height=35, corner_radius=8,
        fg_color=COLORES["panel_terciario"], hover_color=COLORES["peligro"], text_color=COLORES["texto_principal"], command=lambda: self.toggle_todos(False)
    )
    self.btn_ninguno.pack(side="right")

    # ANCLAMOS EL BOTÓN AL FONDO (Para evitar que la lista lo oculte)
    self.lbl_estado = ctk.CTkLabel(left_frame, text="Selecciona docentes para exportar.", font=ctk.CTkFont(size=13), text_color=COLORES["texto_secundario"])
    self.lbl_estado.pack(side="bottom", pady=(0, 15))

    self.btn_generar = ctk.CTkButton(
        left_frame, text="📄 Generar Excel Oficial", font=ctk.CTkFont(size=16, weight="bold"),
        fg_color=COLORES["exito"], hover_color=COLORES["exito_hover"], text_color="#FFFFFF", height=50, corner_radius=10, command=self.generar_excel_quincenal
    )
    self.btn_generar.pack(side="bottom", fill="x", padx=20, pady=(10, 5))

    # AHORA COLOCAMOS LA LISTA (Llenará solo el espacio que sobre)
    self.scroll_maestros = ctk.CTkScrollableFrame(left_frame, fg_color=COLORES["fondo_principal"], corner_radius=10, border_width=1, border_color=COLORES["bordes"])
    self.scroll_maestros.pack(side="top", fill="both", expand=True, padx=20, pady=(5, 10))


    # PANEL DERECHO
    right_frame = ctk.CTkFrame(main_container, fg_color=COLORES["panel_secundario"], corner_radius=15, border_color=COLORES["bordes"], border_width=1)
    right_frame.pack(side="right", fill="both", expand=True, pady=5)

    ctk.CTkLabel(right_frame, text="👁️ Vista Previa en Tiempo Real", font=ctk.CTkFont(size=18, weight="bold"), text_color=COLORES["texto_principal"]).pack(pady=(20, 10), padx=25, anchor="w")

    self.txt_preview = ctk.CTkTextbox(
        right_frame, font=ctk.CTkFont(family="Consolas", size=13),
        fg_color=COLORES["fondo_principal"], text_color=COLORES["texto_principal"],
        border_width=1, border_color=COLORES["bordes"], corner_radius=12
    )
    self.txt_preview.pack(fill="both", expand=True, padx=25, pady=(5, 25))

  def detectar_quincena_automatica(self):
    try:
      conn = obtener_conexion()
      cursor = conn.cursor()
      cursor.execute("SELECT MAX(fecha) FROM ponchadas")
      res = cursor.fetchone()
      conn.close()
      if res and res[0]:
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
          try:
            dt = datetime.strptime(res[0], fmt)
            meses_es = {"JANUARY": "ENERO", "FEBRUARY": "FEBRERO", "MARCH": "MARZO", "APRIL": "ABRIL", "MAY": "MAYO", "JUNE": "JUNIO", "JULY": "JULIO", "AUGUST": "AGOSTO", "SEPTEMBER": "SEPTIEMBRE", "OCTOBER": "OCTUBRE", "NOVEMBER": "NOVIEMBRE", "DECEMBER": "DICIEMBRE"}
            mes_txt = meses_es.get(dt.strftime("%B").upper(), dt.strftime("%B").upper())
            texto = f"1RA QUINCENA DE {mes_txt} DE {dt.year} (DEL 01 AL 15)" if dt.day <= 15 else f"2DA QUINCENA DE {mes_txt} DE {dt.year} (DEL 16 AL 31)"
            self.entry_periodo.delete(0, "end")
            self.entry_periodo.insert(0, texto)
            return
          except ValueError: pass
      self.entry_periodo.delete(0, "end")
      self.entry_periodo.insert(0, "QUINCENA ACTUAL DE PRUEBA")
    except:
      self.entry_periodo.delete(0, "end")
      self.entry_periodo.insert(0, "QUINCENA ACTUAL DE PRUEBA")

  def actualizar_datos(self):
    for w in self.scroll_maestros.winfo_children(): w.destroy()
    self.checkboxes_maestros.clear()
    filas = obtener_maestros()
    if filas:
      for r in filas:
        var_chk = ctk.BooleanVar(value=False)
        chk = ctk.CTkCheckBox(
            self.scroll_maestros, text=r[1], variable=var_chk, text_color=COLORES["texto_principal"], 
            fg_color=COLORES["primario"], hover_color=COLORES["primario_hover"], font=ctk.CTkFont(size=13), command=self.actualizar_vista_previa_global
        )
        chk.pack(anchor="w", padx=15, pady=8)
        self.checkboxes_maestros[r[0]] = (r[1], var_chk)
      self.actualizar_vista_previa_global()
      self.detectar_quincena_automatica()
    else:
      self.txt_preview.delete("1.0", "end")
      self.txt_preview.insert("1.0", "⚠️ Sincroniza un CSV primero.")

  def toggle_todos(self, seleccionar: bool):
    for _, var_chk in self.checkboxes_maestros.values(): var_chk.set(seleccionar)
    self.actualizar_vista_previa_global()

  def actualizar_vista_previa_global(self):
    ids = [i for i, (_, v) in self.checkboxes_maestros.items() if v.get()]
    if not ids:
      self.txt_preview.delete("1.0", "end")
      self.txt_preview.insert("1.0", "ℹ️ Marca las casillas a la izquierda para ver los registros.")
      self.lbl_estado.configure(text="0 docentes seleccionados", text_color=COLORES["texto_secundario"])
      return
    try:
      conn = obtener_conexion()
      df = pd.read_sql_query(f"SELECT m.nombre as Docente, p.fecha, p.hora, p.tipo FROM ponchadas p JOIN maestros m ON p.idMaestro = m.id WHERE p.idMaestro IN ({','.join(['?']*len(ids))}) ORDER BY m.nombre ASC, p.fecha ASC, p.hora ASC", conn, params=ids)
      conn.close()
      self.txt_preview.delete("1.0", "end")
      if df.empty:
        self.txt_preview.insert("end", "No hay ponchadas registradas.\n")
      else:
        self.txt_preview.insert("end", f"{'DOCENTE':<22} | {'FECHA':<12} | {'HORA':<10} | {'TIPO'}\n")
        self.txt_preview.insert("end", "-" * 65 + "\n")
        for _, row in df.iterrows(): self.txt_preview.insert("end", f"{str(row['Docente'])[:20]:<22} | {str(row['fecha']):<12} | {str(row['hora']):<10} | {str(row['tipo'])}\n")
      self.lbl_estado.configure(text=f"{len(ids)} docentes listos", text_color=COLORES["primario"])
    except Exception as e: self.txt_preview.insert("1.0", f"Error:\n{str(e)}")

  def generar_excel_quincenal(self):
    ids = [i for i, (_, v) in self.checkboxes_maestros.items() if v.get()]
    if not ids: return messagebox.showwarning("Atención", "Selecciona al menos un maestro.")
    ruta = filedialog.asksaveasfilename(title="Guardar Excel Oficial", defaultextension=".xlsx", initialfile="Control_Quincenal.xlsx", filetypes=[("Excel", "*.xlsx")])
    if not ruta: return
    try:
      conn = obtener_conexion()
      df_raw = pd.read_sql_query(f"SELECT m.nombre as Nombre, p.fecha, p.hora, p.tipo FROM ponchadas p JOIN maestros m ON p.idMaestro = m.id WHERE p.idMaestro IN ({','.join(['?']*len(ids))}) ORDER BY m.nombre ASC, p.fecha ASC", conn, params=ids)
      conn.close()
      self.gestor_plantillas.inyectar_control_quincenal((self.entry_depto.get() or "RECURSOS HUMANOS"), (self.entry_periodo.get() or "QUINCENA"), df_raw, ruta)
      messagebox.showinfo("Éxito", f"Reporte guardado en:\n{ruta}")
      if messagebox.askyesno("Abrir", "¿Abrir el archivo Excel?"): self.gestor_plantillas.abrir_documento_generado(ruta)
    except Exception as e: messagebox.showerror("Error", str(e))