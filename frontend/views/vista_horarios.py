# frontend/views/vista_horarios.py
import customtkinter as ctk
from tkinter import messagebox
from database.modelos import (
    obtener_periodos, 
    crear_periodo, 
    obtener_turnos,
    obtener_maestros,
    asignar_horario_maestro,
    obtener_horario_maestro
)

class VistaHorarios(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)

        # Mapeos para identificadores de base de datos
        self.periodos_dict = {}  # { "Nombre Periodo": id_periodo }
        self.maestros_dict = {}   # { "Nombre Maestro": id_maestro }
        self.turnos_dict = {}     # { "Nombre Turno": id_turno }

        self.crear_interfaz()
        self.cargar_datos_bd()

    def crear_interfaz(self):
        # Título
        label_titulo = ctk.CTkLabel(self, text="Asignación de Turnos y Horarios", font=ctk.CTkFont(size=20, weight="bold"))
        label_titulo.pack(pady=10, padx=20, anchor="w")

        # Contenedor Principal en 2 columnas
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # ==========================================
        # COLUMNA IZQUIERDA: Formulario de Asignación
        # ==========================================
        frame_form = ctk.CTkFrame(main_frame, width=320)
        frame_form.pack(side="left", fill="y", padx=(0, 10), pady=5)

        ctk.CTkLabel(frame_form, text="Asignar Turno a Docente", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=10)

        # 1. Selector de Periodo
        ctk.CTkLabel(frame_form, text="Periodo / Cuatrimestre:").pack(anchor="w", padx=15, pady=(5,0))
        self.combo_periodo = ctk.CTkOptionMenu(frame_form, values=["Cargando..."], command=self.al_cambiar_seleccion)
        self.combo_periodo.pack(fill="x", padx=15, pady=5)

        # 2. Selector de Maestro
        ctk.CTkLabel(frame_form, text="Maestro:").pack(anchor="w", padx=15, pady=(5,0))
        self.combo_maestro = ctk.CTkOptionMenu(frame_form, values=["Cargando..."], command=self.al_cambiar_seleccion)
        self.combo_maestro.pack(fill="x", padx=15, pady=5)

        # 3. Selector de Turno
        ctk.CTkLabel(frame_form, text="Turno Asignado:").pack(anchor="w", padx=15, pady=(5,0))
        self.combo_turno = ctk.CTkOptionMenu(frame_form, values=["Cargando..."])
        self.combo_turno.pack(fill="x", padx=15, pady=5)

        # Botón Guardar / Asignar
        btn_guardar = ctk.CTkButton(
            frame_form, 
            text="💾 Guardar Asignación", 
            fg_color="#1F4E78", 
            hover_color="#153654",
            command=self.guardar_asignacion
        )
        btn_guardar.pack(fill="x", padx=15, pady=20)

        # ==========================================
        # COLUMNA DERECHA: Tarjeta de Horario Asignado
        # ==========================================
        frame_detalle = ctk.CTkFrame(main_frame)
        frame_detalle.pack(side="right", fill="both", expand=True, pady=5)

        ctk.CTkLabel(frame_detalle, text="Detalle del Horario Activo", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=10)

        self.card_info = ctk.CTkFrame(frame_detalle)
        self.card_info.pack(fill="both", expand=True, padx=20, pady=20)

        self.lbl_info = ctk.CTkLabel(
            self.card_info, 
            text="Selecciona un maestro y periodo para consultar su turno.",
            font=ctk.CTkFont(size=14),
            justify="center"
        )
        self.lbl_info.pack(expand=True)

    # ==========================================
    # LÓGICA Y CONEXIÓN CON EL BACKEND
    # ==========================================

    def cargar_datos_bd(self):
        """Carga y refresca los dropdowns con los datos más recientes de la BD."""
        # 1. Cargar Periodos
        periodos = obtener_periodos()
        if periodos:
            self.periodos_dict = {p[1]: p[0] for p in periodos}
            self.combo_periodo.configure(values=list(self.periodos_dict.keys()))
            if not self.combo_periodo.get() or self.combo_periodo.get() not in self.periodos_dict:
                self.combo_periodo.set(list(self.periodos_dict.keys())[0])
        else:
            id_p = crear_periodo("Enero - Abril 2026", "2026-01-01", "2026-04-30")
            self.periodos_dict = {"Enero - Abril 2026": id_p}
            self.combo_periodo.configure(values=["Enero - Abril 2026"])

        # 2. Cargar Maestros
        maestros = obtener_maestros()
        if maestros:
            self.maestros_dict = {m[1]: m[0] for m in maestros}
            self.combo_maestro.configure(values=list(self.maestros_dict.keys()))
            if not self.combo_maestro.get() or self.combo_maestro.get() not in self.maestros_dict:
                self.combo_maestro.set(list(self.maestros_dict.keys())[0])
        else:
            self.combo_maestro.configure(values=["No hay maestros en BD"])

        # 3. Cargar Turnos
        turnos = obtener_turnos()
        if turnos:
            self.turnos_dict = {f"{t[1]} ({t[2]} - {t[3]})": t[0] for t in turnos}
            self.combo_turno.configure(values=list(self.turnos_dict.keys()))
            if not self.combo_turno.get() or self.combo_turno.get() not in self.turnos_dict:
                self.combo_turno.set(list(self.turnos_dict.keys())[0])

        self.al_cambiar_seleccion()

    def actualizar_datos(self):
        """Método público invocado tras procesar un CSV para refrescar el menú de maestros."""
        self.cargar_datos_bd()

    def al_cambiar_seleccion(self, _=None):
        nombre_m = self.combo_maestro.get()
        nombre_p = self.combo_periodo.get()

        if nombre_m not in self.maestros_dict or nombre_p not in self.periodos_dict:
            return

        id_m = self.maestros_dict[nombre_m]
        id_p = self.periodos_dict[nombre_p]

        horario = obtener_horario_maestro(id_m, id_p)

        if horario:
            _, nombre_turno, entrada, salida, dias = horario
            texto_info = (
                f"👤 Maestro: {nombre_m}\n"
                f"📅 Periodo: {nombre_p}\n\n"
                f"🏷️ Turno: {nombre_turno}\n"
                f"⏰ Horario: {entrada} hrs  ➔  {salida} hrs\n"
                f"📆 Días aplicables: {dias} (1: Lunes - 5: Viernes)"
            )
            self.lbl_info.configure(text=texto_info, text_color="white")
        else:
            self.lbl_info.configure(
                text=f"El docente '{nombre_m}' no tiene un turno asignado para el periodo '{nombre_p}'.",
                text_color="gray"
            )

    def guardar_asignacion(self):
        nombre_m = self.combo_maestro.get()
        nombre_p = self.combo_periodo.get()
        nombre_t = self.combo_turno.get()

        if nombre_m not in self.maestros_dict:
            messagebox.showwarning("Atención", "Selecciona un maestro válido.")
            return

        id_m = self.maestros_dict[nombre_m]
        id_p = self.periodos_dict[nombre_p]
        id_t = self.turnos_dict[nombre_t]

        asignar_horario_maestro(id_m, id_p, id_t)
        messagebox.showinfo("Éxito", f"Turno asignado correctamente a {nombre_m}.")
        self.al_cambiar_seleccion()