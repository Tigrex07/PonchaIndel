# frontend/views/vista_horarios.py
import customtkinter as ctk
from tkinter import messagebox
from database.modelos import (
    obtener_periodos, 
    crear_periodo, 
    agregar_bloque_horario, 
    obtener_horarios_maestro, 
    eliminar_bloque_horario,
    existe_traslape_horario
)
from database.conexion import obtener_conexion

class VistaHorarios(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)

        # Diccionarios para mapear días
        self.dias_map = {
            "Lunes": 1, "Martes": 2, "Miércoles": 3, 
            "Jueves": 4, "Viernes": 5, "Sábado": 6, "Domingo": 7
        }
        self.dias_inv = {v: k for k, v in self.dias_map.items()}

        # Cargar datos iniciales de la BD
        self.periodos_dict = {}  # { "Nombre Periodo": id_periodo }
        self.maestros_dict = {}   # { "Nombre Maestro": id_maestro }

        self.crear_interfaz()
        self.cargar_combos()

    def crear_interfaz(self):
        # Título
        label_titulo = ctk.CTkLabel(self, text="Gestión y Creador de Horarios (Maestros PA)", font=ctk.CTkFont(size=20, weight="bold"))
        label_titulo.pack(pady=10, padx=20, anchor="w")

        # Contenedor Principal en 2 columnas
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # ==========================================
        # COLUMNA IZQUIERDA: Formulario de Registro
        # ==========================================
        frame_form = ctk.CTkFrame(main_frame, width=320)
        frame_form.pack(side="left", fill="y", padx=(0, 10), pady=5)

        ctk.CTkLabel(frame_form, text="Asignar Nuevo Bloque", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=10)

        # 1. Selector de Periodo
        ctk.CTkLabel(frame_form, text="Periodo / Cuatrimestre:").pack(anchor="w", padx=15, pady=(5,0))
        self.combo_periodo = ctk.CTkOptionMenu(frame_form, values=["Cargando..."])
        self.combo_periodo.pack(fill="x", padx=15, pady=5)

        # 2. Selector de Maestro
        ctk.CTkLabel(frame_form, text="Maestro:").pack(anchor="w", padx=15, pady=(5,0))
        self.combo_maestro = ctk.CTkOptionMenu(frame_form, values=["Cargando..."], command=self.actualizar_tabla)
        self.combo_maestro.pack(fill="x", padx=15, pady=5)

        # 3. Selector de Día
        ctk.CTkLabel(frame_form, text="Día de la Semana:").pack(anchor="w", padx=15, pady=(5,0))
        self.combo_dia = ctk.CTkOptionMenu(frame_form, values=list(self.dias_map.keys()))
        self.combo_dia.pack(fill="x", padx=15, pady=5)

        # 4. Horas
        frame_horas = ctk.CTkFrame(frame_form, fg_color="transparent")
        frame_horas.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(frame_horas, text="Entrada (HH:MM):").grid(row=0, column=0, sticky="w")
        self.entry_entrada = ctk.CTkEntry(frame_horas, placeholder_text="08:00", width=90)
        self.entry_entrada.grid(row=1, column=0, padx=(0, 5), pady=5)

        ctk.CTkLabel(frame_horas, text="Salida (HH:MM):").grid(row=0, column=1, sticky="w")
        self.entry_salida = ctk.CTkEntry(frame_horas, placeholder_text="10:00", width=90)
        self.entry_salida.grid(row=1, column=1, padx=(5, 0), pady=5)

        # Botón Guardar
        btn_guardar = ctk.CTkButton(
            frame_form, 
            text="➕ Agregar Bloque", 
            fg_color="#1F4E78", 
            hover_color="#153654",
            command=self.guardar_bloque
        )
        btn_guardar.pack(fill="x", padx=15, pady=20)

        # ==========================================
        # COLUMNA DERECHA: Tabla de Horarios Asignados
        # ==========================================
        frame_tabla = ctk.CTkFrame(main_frame)
        frame_tabla.pack(side="right", fill="both", expand=True, pady=5)

        ctk.CTkLabel(frame_tabla, text="Horario Asignado del Maestro", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=10)

        # Scrollable Frame para simular la lista/tabla de bloques
        self.scroll_tabla = ctk.CTkScrollableFrame(frame_tabla)
        self.scroll_tabla.pack(fill="both", expand=True, padx=15, pady=10)

    # ==========================================
    # LÓGICA Y CONEXIÓN CON EL BACKEND
    # ==========================================

    def cargar_combos(self):
        # Cargar Periodos
        periodos = obtener_periodos()
        if periodos:
            self.periodos_dict = {p[1]: p[0] for p in periodos}
            self.combo_periodo.configure(values=list(self.periodos_dict.keys()))
            self.combo_periodo.set(list(self.periodos_dict.keys())[0])
        else:
            # Crear periodo por defecto si no existe ninguno
            id_p = crear_periodo("Enero - Abril 2026", "2026-01-01", "2026-04-30")
            self.periodos_dict = {"Enero - Abril 2026": id_p}
            self.combo_periodo.configure(values=["Enero - Abril 2026"])

        # Cargar Maestros desde SQLite
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute("SELECT id_maestro, nombre FROM maestros WHERE activo = 1 ORDER BY nombre ASC")
        maestros = cursor.fetchall()
        conn.close()

        if maestros:
            self.maestros_dict = {m[1]: m[0] for m in maestros}
            self.combo_maestro.configure(values=list(self.maestros_dict.keys()))
            self.combo_maestro.set(list(self.maestros_dict.keys())[0])
            self.actualizar_tabla(self.combo_maestro.get())
        else:
            self.combo_maestro.configure(values=["No hay maestros en BD"])

    def guardar_bloque(self):
        nombre_m = self.combo_maestro.get()
        nombre_p = self.combo_periodo.get()
        dia_txt = self.combo_dia.get()
        entrada = self.entry_entrada.get().strip()
        salida = self.entry_salida.get().strip()

        if nombre_m not in self.maestros_dict:
            messagebox.showwarning("Atención", "Selecciona un maestro válido.")
            return

        if not entrada or not salida:
            messagebox.showwarning("Atención", "Ingresa las horas de entrada y salida.")
            return

        id_m = self.maestros_dict[nombre_m]
        id_p = self.periodos_dict[nombre_p]
        dia_num = self.dias_map[dia_txt]

        # Validar Traslape con el Backend
        if existe_traslape_horario(id_m, id_p, dia_num, entrada, salida):
            messagebox.showerror(
                "Conflicto de Horario", 
                f"El maestro {nombre_m} ya tiene un horario asignado que choca con el rango {entrada} - {salida} el día {dia_txt}."
            )
            return

        # Guardar en BD
        agregar_bloque_horario(id_m, id_p, dia_num, entrada, salida)
        messagebox.showinfo("Éxito", f"Bloque ({dia_txt} {entrada} - {salida}) asignado correctamente.")

        # Limpiar campos y refrescar
        self.entry_entrada.delete(0, 'end')
        self.entry_salida.delete(0, 'end')
        self.actualizar_tabla(nombre_m)

    def actualizar_tabla(self, nombre_maestro=None):
        # Limpiar lista anterior
        for widget in self.scroll_tabla.winfo_children():
            widget.destroy()

        if not nombre_maestro or nombre_maestro not in self.maestros_dict:
            return

        id_m = self.maestros_dict[nombre_maestro]
        id_p = self.periodos_dict.get(self.combo_periodo.get())

        if not id_p:
            return

        bloques = obtener_horarios_maestro(id_m, id_p)

        if not bloques:
            ctk.CTkLabel(self.scroll_tabla, text="No hay horarios asignados para este maestro.", text_color="gray").pack(pady=20)
            return

        # Mostrar cada bloque en una tarjeta/fila
        for b in bloques:
            id_h, dia_num, ent, sal = b
            frame_item = ctk.CTkFrame(self.scroll_tabla)
            frame_item.pack(fill="x", pady=4, padx=5)

            txt = f"🗓️ {self.dias_inv.get(dia_num, 'Día')} | ⏰ {ent} hrs  ➔  {sal} hrs"
            ctk.CTkLabel(frame_item, text=txt, font=ctk.CTkFont(size=13)).pack(side="left", padx=15, pady=8)

            btn_del = ctk.CTkButton(
                frame_item, 
                text="Eliminar", 
                fg_color="#A93226", 
                hover_color="#7B241C", 
                width=70, height=25,
                command=lambda id_del=id_h: self.borrar_bloque(id_del)
            )
            btn_del.pack(side="right", padx=10)

    def borrar_bloque(self, id_horario):
        eliminar_bloque_horario(id_horario)
        self.actualizar_tabla(self.combo_maestro.get())