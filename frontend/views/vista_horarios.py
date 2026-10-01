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

        # Mapeos e historiales en memoria
        self.periodos_dict = {}     # { "Nombre Periodo": id_periodo }
        self.maestros_dict = {}      # { "Nombre Maestro": id_maestro }
        self.turnos_dict = {}        # { "Nombre Turno": id_turno }
        self.maestros_lista = []     # Lista con la estructura completa
        self.checkboxes_vars = {}    # { "Nombre Maestro": BooleanVar }

        # Estado actual de filtros
        self.filtro_estado = "TODOS" # "TODOS", "SIN_TURNO", "CON_TURNO", etc.
        self.maestro_seleccionado_individual = None

        self.crear_interfaz()
        self.cargar_datos_bd()

    def crear_interfaz(self):
        # -------------------------------------------------------------
        # 1. ENCABEZADO Y DASHBOARD DE ESTADÍSTICAS RÁPIDAS
        # -------------------------------------------------------------
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 5))

        title_label = ctk.CTkLabel(
            header_frame, 
            text="📅 Asignación y Control de Turnos", 
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#F3F4F6"
        )
        title_label.pack(side="left")

        # Indicador BD y Tarjetas de resumen
        self.status_bd = ctk.CTkLabel(
            header_frame,
            text="🟢 BD Sincronizada",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#10B981",
            fg_color="#064E3B",
            corner_radius=8,
            padx=10,
            pady=4
        )
        self.status_bd.pack(side="right")

        # Contenedor Principal (2 Columnas)
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # =============================================================
        # COLUMNA IZQUIERDA: Búsqueda, Filtros y Lista Dinámica
        # =============================================================
        left_frame = ctk.CTkFrame(main_frame, width=380, fg_color="#1E293B", corner_radius=12)
        left_frame.pack(side="left", fill="both", padx=(0, 10), pady=5)

        # --- Fila 1: Selector de Periodo ---
        top_left = ctk.CTkFrame(left_frame, fg_color="transparent")
        top_left.pack(fill="x", padx=15, pady=(15, 5))

        ctk.CTkLabel(
            top_left, 
            text="Periodo:", 
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#93C5FD"
        ).pack(side="left", padx=(0, 5))

        self.combo_periodo = ctk.CTkOptionMenu(
            top_left, 
            values=["Cargando..."], 
            command=self.al_cambiar_periodo,
            fg_color="#334155", 
            button_color="#0F172A", 
            button_hover_color="#2563EB",
            height=30
        )
        self.combo_periodo.pack(side="right", fill="x", expand=True)

        # --- Fila 2: Caja de Búsqueda por Texto ---
        self.entry_buscar = ctk.CTkEntry(
            left_frame,
            placeholder_text="🔎 Buscar maestro por nombre...",
            fg_color="#0F172A",
            text_color="#F3F4F6",
            border_color="#334155",
            height=35
        )
        self.entry_buscar.pack(fill="x", padx=15, pady=8)
        self.entry_buscar.bind("<KeyRelease>", lambda e: self.filtrar_lista_maestros())

        # --- Fila 3: Chips / Botones de Filtro Rápido ---
        frame_chips = ctk.CTkFrame(left_frame, fg_color="transparent")
        frame_chips.pack(fill="x", padx=15, pady=2)

        self.btn_f_todos = ctk.CTkButton(
            frame_chips, text="Todos", width=65, height=24, font=ctk.CTkFont(size=11),
            fg_color="#2563EB", hover_color="#1D4ED8", command=lambda: self.set_filtro("TODOS")
        )
        self.btn_f_todos.pack(side="left", padx=(0, 4))

        self.btn_f_sinturno = ctk.CTkButton(
            frame_chips, text="⚠️ Sin Turno", width=85, height=24, font=ctk.CTkFont(size=11),
            fg_color="#334155", hover_color="#D97706", command=lambda: self.set_filtro("SIN_TURNO")
        )
        self.btn_f_sinturno.pack(side="left", padx=(0, 4))

        self.btn_f_matutino = ctk.CTkButton(
            frame_chips, text="☀️ Matutino", width=80, height=24, font=ctk.CTkFont(size=11),
            fg_color="#334155", hover_color="#1E3A8A", command=lambda: self.set_filtro("MATUTINO")
        )
        self.btn_f_matutino.pack(side="left", padx=(0, 4))

        self.btn_f_vespertino = ctk.CTkButton(
            frame_chips, text="🌙 Vespert.", width=75, height=24, font=ctk.CTkFont(size=11),
            fg_color="#334155", hover_color="#312E81", command=lambda: self.set_filtro("VESPERTINO")
        )
        self.btn_f_vespertino.pack(side="left")

        # --- Fila 4: Switch de Modo (Individual vs Masivo) ---
        frame_mode = ctk.CTkFrame(left_frame, fg_color="#0F172A", corner_radius=8)
        frame_mode.pack(fill="x", padx=15, pady=8)

        self.switch_masivo_var = ctk.BooleanVar(value=False)
        self.switch_masivo = ctk.CTkSwitch(
            frame_mode,
            text="⚡ Modo Selección Masiva",
            variable=self.switch_masivo_var,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#F59E0B",
            progress_color="#D97706",
            command=self.al_cambiar_modo_switch
        )
        self.switch_masivo.pack(padx=10, pady=8, side="left")

        # --- Fila 5: Scrollable Frame con la Lista Dinámica ---
        self.scroll_maestros = ctk.CTkScrollableFrame(left_frame, fg_color="#0F172A", corner_radius=8)
        self.scroll_maestros.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # =============================================================
        # COLUMNA DERECHA: Ficha Técnica + Panel de Asignación Rápida
        # =============================================================
        right_frame = ctk.CTkFrame(main_frame, fg_color="#1E293B", corner_radius=12)
        right_frame.pack(side="right", fill="both", expand=True, pady=5)

        # 1. TARJETA VISUAL / FICHA TÉCNICA
        self.card_container = ctk.CTkFrame(right_frame, fg_color="#0F172A", corner_radius=10, border_width=1, border_color="#334155")
        self.card_container.pack(fill="x", padx=20, pady=(20, 10))

        self.build_card_ui()

        # 2. PANEL DE ACCIÓN Y ASIGNACIÓN DE TURNO
        action_box = ctk.CTkFrame(right_frame, fg_color="transparent")
        action_box.pack(fill="both", expand=True, padx=20, pady=(5, 20))

        ctk.CTkLabel(
            action_box, 
            text="Asignar / Cambiar Turno", 
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#93C5FD"
        ).pack(anchor="w", pady=(5, 5))

        ctk.CTkLabel(action_box, text="Seleccione el Turno a aplicar:", font=ctk.CTkFont(size=12), text_color="#9CA3AF").pack(anchor="w", pady=(2,0))
        
        self.combo_turno = ctk.CTkOptionMenu(
            action_box, 
            values=["Cargando..."],
            fg_color="#334155", 
            button_color="#0F172A", 
            button_hover_color="#2563EB",
            height=38
        )
        self.combo_turno.pack(fill="x", pady=8)

        # Botones de Acción (Individual y Masiva)
        self.btn_asignar_indiv = ctk.CTkButton(
            action_box,
            text="💾 Asignar Turno al Maestro Seleccionado",
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            command=self.guardar_asignacion_individual
        )
        self.btn_asignar_indiv.pack(fill="x", pady=5)

        self.btn_asignar_masivo = ctk.CTkButton(
            action_box,
            text="🚀 Aplicar Turno a Todos los Seleccionados (Masivo)",
            fg_color="#D97706",
            hover_color="#B45309",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            command=self.guardar_asignacion_masiva
        )
        # Oculto por defecto hasta activar el switch
        
    def build_card_ui(self):
        """Construye los elementos de la Ficha Técnica visual."""
        top_box = ctk.CTkFrame(self.card_container, fg_color="transparent")
        top_box.pack(fill="x", padx=20, pady=(15, 10))

        self.lbl_avatar = ctk.CTkLabel(
            top_box, text="--", font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#FFFFFF", fg_color="#2563EB", width=50, height=50, corner_radius=25
        )
        self.lbl_avatar.pack(side="left", padx=(0, 15))

        info_meta = ctk.CTkFrame(top_box, fg_color="transparent")
        info_meta.pack(side="left", fill="both", expand=True)

        self.lbl_nombre_docente = ctk.CTkLabel(
            info_meta, text="Seleccione un maestro de la lista",
            font=ctk.CTkFont(size=16, weight="bold"), text_color="#F3F4F6", anchor="w"
        )
        self.lbl_nombre_docente.pack(fill="x")

        self.lbl_periodo_tag = ctk.CTkLabel(
            info_meta, text="Periodo Lectivo: N/A",
            font=ctk.CTkFont(size=12), text_color="#9CA3AF", anchor="w"
        )
        self.lbl_periodo_tag.pack(fill="x")

        # Badges Box
        badges_box = ctk.CTkFrame(self.card_container, fg_color="transparent")
        badges_box.pack(fill="x", padx=20, pady=5)

        self.badge_turno = ctk.CTkLabel(
            badges_box, text="SIN TURNO", font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#F59E0B", fg_color="#451A03", corner_radius=6, padx=10, pady=3
        )
        self.badge_turno.pack(side="left", padx=(0, 10))

        self.badge_dias = ctk.CTkLabel(
            badges_box, text="📅 LUNES - VIERNES", font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#93C5FD", fg_color="#1E3A8A", corner_radius=6, padx=10, pady=3
        )
        self.badge_dias.pack(side="left")

        # Clock Box
        clock_box = ctk.CTkFrame(self.card_container, fg_color="#1E293B", corner_radius=8)
        clock_box.pack(fill="x", padx=20, pady=12)

        self.lbl_horario_big = ctk.CTkLabel(
            clock_box, text="-- : --   ➔   -- : --",
            font=ctk.CTkFont(size=22, weight="bold"), text_color="#38BDF8"
        )
        self.lbl_horario_big.pack(pady=10)

        self.lbl_status_footer = ctk.CTkLabel(
            self.card_container, text="🔴 Sin asignación para el periodo activo.",
            font=ctk.CTkFont(size=11), text_color="#EF4444"
        )
        self.lbl_status_footer.pack(pady=(0, 12))

    # =============================================================
    # CARGA Y FILTRADO AVANZADO DE DATOS
    # =============================================================

    def cargar_datos_bd(self):
        """Carga los datos iniciales desde SQLite."""
        # 1. Periodos
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

        # 2. Turnos
        turnos = obtener_turnos()
        if turnos:
            self.turnos_dict = {f"{t[1]} ({t[2]} - {t[3]})": t[0] for t in turnos}
            self.combo_turno.configure(values=list(self.turnos_dict.keys()))
            if not self.combo_turno.get() or self.combo_turno.get() not in self.turnos_dict:
                self.combo_turno.set(list(self.turnos_dict.keys())[0])

        # 3. Refrescar Maestros con Horarios Asignados
        self.refrescar_lista_maestros()

    def actualizar_datos(self):
        """Método público invocado tras procesar CSV."""
        self.cargar_datos_bd()

    def al_cambiar_periodo(self, _=None):
        """Al cambiar de cuatrimestre, se recargan las asignaciones."""
        self.refrescar_lista_maestros()

    def refrescar_lista_maestros(self):
        """Carga la lista completa de maestros cruzada con el turno del periodo activo."""
        nombre_p = self.combo_periodo.get()
        if nombre_p not in self.periodos_dict:
            return

        id_p = self.periodos_dict[nombre_p]
        maestros_raw = obtener_maestros()

        self.maestros_lista = []
        self.maestros_dict = {}

        for m in maestros_raw:
            id_m, nombre, tipo, activo = m
            self.maestros_dict[nombre] = id_m
            horario = obtener_horario_maestro(id_m, id_p)
            
            nombre_turno = horario[1] if horario else "SIN_TURNO"
            self.maestros_lista.append({
                "id": id_m,
                "nombre": nombre,
                "turno": nombre_turno,
                "horario": horario
            })

        self.filtrar_lista_maestros()

    def set_filtro(self, nuevo_filtro):
        """Aplica un filtro rápido (Chip) a la lista."""
        self.filtro_estado = nuevo_filtro
        
        # Resetear estilos de los botones de chip
        self.btn_f_todos.configure(fg_color="#334155")
        self.btn_f_sinturno.configure(fg_color="#334155")
        self.btn_f_matutino.configure(fg_color="#334155")
        self.btn_f_vespertino.configure(fg_color="#334155")

        if nuevo_filtro == "TODOS":
            self.btn_f_todos.configure(fg_color="#2563EB")
        elif nuevo_filtro == "SIN_TURNO":
            self.btn_f_sinturno.configure(fg_color="#D97706")
        elif nuevo_filtro == "MATUTINO":
            self.btn_f_matutino.configure(fg_color="#1E3A8A")
        elif nuevo_filtro == "VESPERTINO":
            self.btn_f_vespertino.configure(fg_color="#312E81")

        self.filtrar_lista_maestros()

    def filtrar_lista_maestros(self):
        """Filtra la lista por texto de búsqueda y chip activo, y redibuja la grilla."""
        texto_busqueda = self.entry_buscar.get().strip().lower()

        # Limpiar frame scrollable
        for w in self.scroll_maestros.winfo_children():
            w.destroy()

        self.checkboxes_vars.clear()
        modo_masivo = self.switch_masivo_var.get()

        maestros_filtrados = []

        for m in self.maestros_lista:
            # 1. Filtro por Búsqueda de Texto
            if texto_busqueda and texto_busqueda not in m["nombre"].lower():
                continue

            # 2. Filtro por Estado de Turno
            if self.filtro_estado == "SIN_TURNO" and m["turno"] != "SIN_TURNO":
                continue
            elif self.filtro_estado == "MATUTINO" and "matutino" not in m["turno"].lower():
                continue
            elif self.filtro_estado == "VESPERTINO" and "vespertino" not in m["turno"].lower():
                continue

            maestros_filtrados.append(m)

        if not maestros_filtrados:
            ctk.CTkLabel(
                self.scroll_maestros, 
                text="No se encontraron maestros...", 
                font=ctk.CTkFont(size=12), text_color="gray"
            ).pack(pady=20)
            return

        # Dibujar cada elemento según el modo activo
        for m in maestros_filtrados:
            nombre = m["nombre"]
            turno_str = m["turno"]

            row_frame = ctk.CTkFrame(self.scroll_maestros, fg_color="#1E293B", corner_radius=6)
            row_frame.pack(fill="x", pady=2, padx=2)

            if modo_masivo:
                # MODO MASIVO: Muestra Checkbox
                var = ctk.BooleanVar(value=False)
                chk = ctk.CTkCheckBox(
                    row_frame, text=nombre, variable=var,
                    font=ctk.CTkFont(size=11), text_color="#E2E8F0",
                    checkbox_width=18, checkbox_height=18
                )
                chk.pack(side="left", padx=8, pady=6)
                self.checkboxes_vars[nombre] = var
            else:
                # MODO INDIVIDUAL: Muestra Botón Seleccionable
                btn_m = ctk.CTkButton(
                    row_frame,
                    text=nombre,
                    anchor="w",
                    fg_color="transparent",
                    hover_color="#334155",
                    text_color="#F3F4F6",
                    font=ctk.CTkFont(size=12),
                    command=lambda n=nombre: self.seleccionar_maestro_individual(n)
                )
                btn_m.pack(side="left", fill="x", expand=True, padx=5, pady=2)

            # Badge pequeño de estado en la fila
            color_badge = "#059669" if turno_str != "SIN_TURNO" else "#D97706"
            lbl_b = ctk.CTkLabel(
                row_frame, text=turno_str[:12], font=ctk.CTkFont(size=9, weight="bold"),
                text_color="#FFFFFF", fg_color=color_badge, corner_radius=4, padx=6, pady=2
            )
            lbl_b.pack(side="right", padx=6)

        # Si hay maestro previamente seleccionado, refrescar su tarjeta
        if self.maestro_seleccionado_individual:
            self.seleccionar_maestro_individual(self.maestro_seleccionado_individual)
        elif maestros_filtrados and not modo_masivo:
            self.seleccionar_maestro_individual(maestros_filtrados[0]["nombre"])

    def al_cambiar_modo_switch(self):
        """Alterna entre el modo de consulta individual y asignación masiva."""
        modo_masivo = self.switch_masivo_var.get()

        if modo_masivo:
            self.btn_asignar_indiv.pack_forget()
            self.btn_asignar_masivo.pack(fill="x", pady=5)
        else:
            self.btn_asignar_masivo.pack_forget()
            self.btn_asignar_indiv.pack(fill="x", pady=5)

        self.filtrar_lista_maestros()

    def seleccionar_maestro_individual(self, nombre_m):
        """Actualiza la tarjeta Ficha Técnica al hacer clic en un maestro."""
        self.maestro_seleccionado_individual = nombre_m

        partes = nombre_m.strip().split()
        iniciales = "".join([p[0] for p in partes[:2]]).upper() if partes else "DO"
        self.lbl_avatar.configure(text=iniciales)
        self.lbl_nombre_docente.configure(text=nombre_m)

        nombre_p = self.combo_periodo.get()
        self.lbl_periodo_tag.configure(text=f"Periodo Lectivo: {nombre_p}")

        if nombre_m in self.maestros_dict and nombre_p in self.periodos_dict:
            id_m = self.maestros_dict[nombre_m]
            id_p = self.periodos_dict[nombre_p]

            horario = obtener_horario_maestro(id_m, id_p)

            if horario:
                _, nombre_turno, entrada, salida, dias = horario
                
                if "matutino" in nombre_turno.lower():
                    color_bg = "#1E3A8A"
                    color_txt = "#93C5FD"
                    icono = "☀️ "
                elif "vespertino" in nombre_turno.lower():
                    color_bg = "#312E81"
                    color_txt = "#C084FC"
                    icono = "🌙 "
                else:
                    color_bg = "#065F46"
                    color_txt = "#6EE7B7"
                    icono = "⚡ "

                self.badge_turno.configure(
                    text=f"{icono}{nombre_turno.upper()}",
                    fg_color=color_bg, text_color=color_txt
                )
                self.lbl_horario_big.configure(text=f"{entrada} HRS   ➔   {salida} HRS", text_color="#38BDF8")
                self.lbl_status_footer.configure(
                    text="🟢 Turno Asignado y Activo en la Base de Datos",
                    text_color="#10B981"
                )
                self.card_container.configure(border_color="#10B981")
            else:
                self.badge_turno.configure(text="SIN TURNO", fg_color="#451A03", text_color="#F59E0B")
                self.lbl_horario_big.configure(text="-- : --   ➔   -- : --", text_color="#64748B")
                self.lbl_status_footer.configure(
                    text="🔴 Sin asignación para este cuatrimestre.",
                    text_color="#EF4444"
                )
                self.card_container.configure(border_color="#334155")

    # =============================================================
    # ACCIONES DE GUARDADO
    # =============================================================

    def guardar_asignacion_individual(self):
        nombre_m = self.maestro_seleccionado_individual
        nombre_p = self.combo_periodo.get()
        nombre_t = self.combo_turno.get()

        if not nombre_m or nombre_m not in self.maestros_dict:
            messagebox.showwarning("Atención", "Selecciona un maestro válido de la lista.")
            return

        id_m = self.maestros_dict[nombre_m]
        id_p = self.periodos_dict[nombre_p]
        id_t = self.turnos_dict[nombre_t]

        asignar_horario_maestro(id_m, id_p, id_t)
        messagebox.showinfo("Éxito", f"Turno asignado correctamente a {nombre_m}.")
        self.refrescar_lista_maestros()

    def guardar_asignacion_masiva(self):
        nombre_p = self.combo_periodo.get()
        nombre_t = self.combo_turno.get()

        if nombre_p not in self.periodos_dict or nombre_t not in self.turnos_dict:
            messagebox.showwarning("Atención", "Selecciona un periodo y turno válidos.")
            return

        id_p = self.periodos_dict[nombre_p]
        id_t = self.turnos_dict[nombre_t]

        maestros_seleccionados = [
            nombre for nombre, var in self.checkboxes_vars.items() if var.get()
        ]

        if not maestros_seleccionados:
            messagebox.showwarning("Atención", "Marca al menos un maestro de la lista masiva.")
            return

        for nombre in maestros_seleccionados:
            id_m = self.maestros_dict[nombre]
            asignar_horario_maestro(id_m, id_p, id_t)

        messagebox.showinfo(
            "Carga Masiva Exitosa", 
            f"Se asignó el turno '{nombre_t}' a {len(maestros_seleccionados)} maestros seleccionados."
        )
        self.refrescar_lista_maestros()