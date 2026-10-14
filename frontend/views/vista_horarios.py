import customtkinter as ctk
from tkinter import messagebox
from database.modelos import (
    obtener_periodos, crear_periodo, obtener_turnos,
    obtener_maestros, asignar_horario_maestro, obtener_horario_maestro
)
from frontend.tema import COLORES

class VistaHorarios(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORES["fondo_principal"])
        self.periodos_dict, self.maestros_dict, self.turnos_dict = {}, {}, {}
        self.maestros_lista, self.checkboxes_vars = [], {}
        self.filtro_estado = "TODOS"
        self.maestro_seleccionado_individual = None
        self.crear_interfaz()
        self.cargar_datos_bd()

    def crear_interfaz(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 5))

        ctk.CTkLabel(header_frame, text="📅 Gestor de Horarios PA", font=ctk.CTkFont(size=26, weight="bold"), text_color=COLORES["texto_principal"]).pack(side="left")

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # PANEL IZQUIERDO
        left_frame = ctk.CTkFrame(main_frame, width=400, fg_color=COLORES["panel_secundario"], corner_radius=15, border_color=COLORES["borde_acento"], border_width=2)
        left_frame.pack(side="left", fill="both", padx=(0, 15), pady=5)

        top_left = ctk.CTkFrame(left_frame, fg_color="transparent")
        top_left.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(top_left, text="🎓 Periodo:", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORES["texto_secundario"]).pack(side="left", padx=(0, 10))
        self.combo_periodo = ctk.CTkOptionMenu(
            top_left, values=["Cargando..."], command=self.al_cambiar_periodo,
            fg_color=COLORES["panel_terciario"], button_color=COLORES["panel_terciario"], 
            button_hover_color=COLORES["primario_hover"], height=38, text_color=COLORES["texto_principal"], font=ctk.CTkFont(size=13, weight="bold")
        )
        self.combo_periodo.pack(side="right", fill="x", expand=True)

        self.entry_buscar = ctk.CTkEntry(
            left_frame, placeholder_text="🔎 Buscar maestro...", fg_color=COLORES["fondo_principal"], 
            text_color=COLORES["texto_principal"], border_color=COLORES["bordes"], height=40, font=ctk.CTkFont(size=13)
        )
        self.entry_buscar.pack(fill="x", padx=20, pady=10)
        self.entry_buscar.bind("<KeyRelease>", lambda e: self.filtrar_lista_maestros())

        frame_chips = ctk.CTkFrame(left_frame, fg_color="transparent")
        frame_chips.pack(fill="x", padx=20, pady=5)
        self.btn_f_todos = ctk.CTkButton(frame_chips, text="Todos", width=70, height=28, font=ctk.CTkFont(size=12, weight="bold"), fg_color=COLORES["primario"], hover_color=COLORES["primario_hover"], corner_radius=6, command=lambda: self.set_filtro("TODOS"))
        self.btn_f_todos.pack(side="left", padx=(0, 5))
        self.btn_f_sinturno = ctk.CTkButton(frame_chips, text="⚠️ Sin Turno", width=95, height=28, font=ctk.CTkFont(size=12, weight="bold"), fg_color=COLORES["panel_terciario"], hover_color=COLORES["alerta"], corner_radius=6, command=lambda: self.set_filtro("SIN_TURNO"))
        self.btn_f_sinturno.pack(side="left", padx=(0, 5))
        self.btn_f_matutino = ctk.CTkButton(frame_chips, text="☀️ Mat.", width=75, height=28, font=ctk.CTkFont(size=12, weight="bold"), fg_color=COLORES["panel_terciario"], hover_color="#1E3A8A", corner_radius=6, command=lambda: self.set_filtro("MATUTINO"))
        self.btn_f_matutino.pack(side="left", padx=(0, 5))
        self.btn_f_vespertino = ctk.CTkButton(frame_chips, text="🌙 Vesp.", width=75, height=28, font=ctk.CTkFont(size=12, weight="bold"), fg_color=COLORES["panel_terciario"], hover_color="#312E81", corner_radius=6, command=lambda: self.set_filtro("VESPERTINO"))
        self.btn_f_vespertino.pack(side="left")

        # ANCLAMOS EL SWITCH AL FONDO
        frame_mode = ctk.CTkFrame(left_frame, fg_color=COLORES["panel_terciario"], corner_radius=10)
        frame_mode.pack(side="bottom", fill="x", padx=20, pady=(0, 20))
        self.switch_masivo_var = ctk.BooleanVar(value=False)
        self.switch_masivo = ctk.CTkSwitch(
            frame_mode, text="⚡ Activar Selección Masiva", variable=self.switch_masivo_var,
            font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORES["alerta"], progress_color=COLORES["alerta"], command=self.al_cambiar_modo_switch
        )
        self.switch_masivo.pack(padx=15, pady=12, side="left")

        self.scroll_maestros = ctk.CTkScrollableFrame(left_frame, fg_color=COLORES["fondo_principal"], corner_radius=10, border_color=COLORES["bordes"], border_width=1)
        self.scroll_maestros.pack(side="top", fill="both", expand=True, padx=20, pady=(0, 15))

        # PANEL DERECHO
        right_frame = ctk.CTkFrame(main_frame, fg_color=COLORES["panel_secundario"], corner_radius=15, border_color=COLORES["bordes"], border_width=1)
        right_frame.pack(side="right", fill="both", expand=True, pady=5)

        # ANCLAMOS EL MENÚ DE ACCIONES AL FONDO
        action_box = ctk.CTkFrame(right_frame, fg_color="transparent")
        action_box.pack(side="bottom", fill="x", padx=25, pady=(10, 25))
        
        ctk.CTkLabel(action_box, text="⚙️ Asignar / Cambiar Turno", font=ctk.CTkFont(size=18, weight="bold"), text_color=COLORES["texto_principal"]).pack(anchor="w", pady=(5, 5))
        ctk.CTkLabel(action_box, text="Seleccione el nuevo turno:", font=ctk.CTkFont(size=13), text_color=COLORES["texto_secundario"]).pack(anchor="w", pady=(5,0))
        
        self.combo_turno = ctk.CTkOptionMenu(
            action_box, values=["Cargando..."], fg_color=COLORES["fondo_principal"], button_color=COLORES["panel_terciario"], 
            button_hover_color=COLORES["primario_hover"], height=45, text_color=COLORES["texto_principal"], font=ctk.CTkFont(size=14, weight="bold")
        )
        self.combo_turno.pack(fill="x", pady=10)

        self.btn_asignar_indiv = ctk.CTkButton(
            action_box, text="💾 Guardar Turno Individual", fg_color=COLORES["primario"], hover_color=COLORES["primario_hover"],
            font=ctk.CTkFont(size=15, weight="bold"), height=50, corner_radius=10, text_color="#FFFFFF", command=self.guardar_asignacion_individual
        )
        self.btn_asignar_indiv.pack(fill="x", pady=5)
        self.btn_asignar_masivo = ctk.CTkButton(
            action_box, text="🚀 Aplicar Turno a Todos los Seleccionados", fg_color=COLORES["alerta"], hover_color="#B45309",
            font=ctk.CTkFont(size=15, weight="bold"), height=50, corner_radius=10, text_color="#FFFFFF", command=self.guardar_asignacion_masiva
        )
        
        # LA TARJETA OCUPA EL ESPACIO RESTANTE ARRIBA
        self.card_container = ctk.CTkFrame(right_frame, fg_color=COLORES["panel_terciario"], corner_radius=12, border_width=2, border_color=COLORES["bordes"])
        self.card_container.pack(side="top", fill="both", expand=True, padx=25, pady=(25, 10))
        self.build_card_ui()

    def build_card_ui(self):
        top_box = ctk.CTkFrame(self.card_container, fg_color="transparent")
        top_box.pack(fill="x", padx=20, pady=(20, 10))
        self.lbl_avatar = ctk.CTkLabel(top_box, text="--", font=ctk.CTkFont(size=22, weight="bold"), text_color="#FFFFFF", fg_color=COLORES["primario"], width=60, height=60, corner_radius=30)
        self.lbl_avatar.pack(side="left", padx=(0, 20))
        info_meta = ctk.CTkFrame(top_box, fg_color="transparent")
        info_meta.pack(side="left", fill="both", expand=True)
        self.lbl_nombre_docente = ctk.CTkLabel(info_meta, text="Seleccione un maestro", font=ctk.CTkFont(size=20, weight="bold"), text_color=COLORES["texto_principal"], anchor="w")
        self.lbl_nombre_docente.pack(fill="x")
        self.lbl_periodo_tag = ctk.CTkLabel(info_meta, text="Periodo Lectivo: N/A", font=ctk.CTkFont(size=13), text_color=COLORES["texto_secundario"], anchor="w")
        self.lbl_periodo_tag.pack(fill="x")
        badges_box = ctk.CTkFrame(self.card_container, fg_color="transparent")
        badges_box.pack(fill="x", padx=20, pady=10)
        self.badge_turno = ctk.CTkLabel(badges_box, text="SIN TURNO", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORES["alerta"], fg_color="#451A03", corner_radius=8, padx=12, pady=5)
        self.badge_turno.pack(side="left", padx=(0, 15))
        self.badge_dias = ctk.CTkLabel(badges_box, text="📅 LUNES - VIERNES", font=ctk.CTkFont(size=12, weight="bold"), text_color="#93C5FD", fg_color="#1E3A8A", corner_radius=8, padx=12, pady=5)
        self.badge_dias.pack(side="left")
        clock_box = ctk.CTkFrame(self.card_container, fg_color=COLORES["fondo_principal"], corner_radius=10)
        clock_box.pack(fill="x", padx=20, pady=15)
        self.lbl_horario_big = ctk.CTkLabel(clock_box, text="-- : --   ➔   -- : --", font=ctk.CTkFont(size=26, weight="bold"), text_color=COLORES["texto_secundario"])
        self.lbl_horario_big.pack(pady=15)
        self.lbl_status_footer = ctk.CTkLabel(self.card_container, text="🔴 Sin asignación", font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORES["peligro"])
        self.lbl_status_footer.pack(pady=(0, 20))

    def cargar_datos_bd(self):
        periodos = obtener_periodos()
        if periodos:
            self.periodos_dict = {p[1]: p[0] for p in periodos}
            self.combo_periodo.configure(values=list(self.periodos_dict.keys()))
            if not self.combo_periodo.get() or self.combo_periodo.get() not in self.periodos_dict: self.combo_periodo.set(list(self.periodos_dict.keys())[0])
        turnos = obtener_turnos()
        if turnos:
            self.turnos_dict = {f"{t[1]} ({t[2]} - {t[3]})": t[0] for t in turnos}
            self.combo_turno.configure(values=list(self.turnos_dict.keys()))
            if not self.combo_turno.get() or self.combo_turno.get() not in self.turnos_dict: self.combo_turno.set(list(self.turnos_dict.keys())[0])
        self.refrescar_lista_maestros()

    def actualizar_datos(self): self.cargar_datos_bd()
    def al_cambiar_periodo(self, _=None): self.refrescar_lista_maestros()

    def refrescar_lista_maestros(self):
        nombre_p = self.combo_periodo.get()
        if nombre_p not in self.periodos_dict: return
        self.maestros_lista, self.maestros_dict = [], {}
        for m in obtener_maestros():
            id_m, nombre = m[0], m[1]
            self.maestros_dict[nombre] = id_m
            horario = obtener_horario_maestro(id_m, self.periodos_dict[nombre_p])
            self.maestros_lista.append({"id": id_m, "nombre": nombre, "turno": horario[1] if horario else "SIN_TURNO", "horario": horario})
        self.filtrar_lista_maestros()

    def set_filtro(self, nuevo_filtro):
        self.filtro_estado = nuevo_filtro
        self.btn_f_todos.configure(fg_color=COLORES["panel_terciario"])
        self.btn_f_sinturno.configure(fg_color=COLORES["panel_terciario"])
        self.btn_f_matutino.configure(fg_color=COLORES["panel_terciario"])
        self.btn_f_vespertino.configure(fg_color=COLORES["panel_terciario"])
        if nuevo_filtro == "TODOS": self.btn_f_todos.configure(fg_color=COLORES["primario"])
        elif nuevo_filtro == "SIN_TURNO": self.btn_f_sinturno.configure(fg_color=COLORES["alerta"])
        elif nuevo_filtro == "MATUTINO": self.btn_f_matutino.configure(fg_color="#1E3A8A")
        elif nuevo_filtro == "VESPERTINO": self.btn_f_vespertino.configure(fg_color="#312E81")
        self.filtrar_lista_maestros()

    def filtrar_lista_maestros(self):
        texto_busqueda = self.entry_buscar.get().strip().lower()
        for w in self.scroll_maestros.winfo_children(): w.destroy()
        self.checkboxes_vars.clear()
        modo_masivo = self.switch_masivo_var.get()
        maestros_filtrados = [m for m in self.maestros_lista if not (texto_busqueda and texto_busqueda not in m["nombre"].lower()) and not (self.filtro_estado == "SIN_TURNO" and m["turno"] != "SIN_TURNO") and not (self.filtro_estado == "MATUTINO" and "matutino" not in m["turno"].lower()) and not (self.filtro_estado == "VESPERTINO" and "vespertino" not in m["turno"].lower())]
        
        for m in maestros_filtrados:
            row_frame = ctk.CTkFrame(self.scroll_maestros, fg_color=COLORES["panel_secundario"], corner_radius=8)
            row_frame.pack(fill="x", pady=3, padx=3)
            if modo_masivo:
                var = ctk.BooleanVar(value=False)
                chk = ctk.CTkCheckBox(row_frame, text=m["nombre"], variable=var, font=ctk.CTkFont(size=13), text_color=COLORES["texto_principal"], fg_color=COLORES["primario"], hover_color=COLORES["primario_hover"])
                chk.pack(side="left", padx=12, pady=10)
                self.checkboxes_vars[m["nombre"]] = var
            else:
                btn_m = ctk.CTkButton(row_frame, text=m["nombre"], anchor="w", fg_color="transparent", hover_color=COLORES["panel_terciario"], text_color=COLORES["texto_principal"], font=ctk.CTkFont(size=13, weight="bold"), command=lambda n=m["nombre"]: self.seleccionar_maestro_individual(n))
                btn_m.pack(side="left", fill="x", expand=True, padx=8, pady=4)
            
            lbl_b = ctk.CTkLabel(row_frame, text=m["turno"][:12], font=ctk.CTkFont(size=10, weight="bold"), text_color="#FFFFFF", fg_color=COLORES["exito"] if m["turno"] != "SIN_TURNO" else COLORES["alerta"], corner_radius=6, padx=8, pady=4)
            lbl_b.pack(side="right", padx=10)
        
        if self.maestro_seleccionado_individual: self.seleccionar_maestro_individual(self.maestro_seleccionado_individual)
        elif maestros_filtrados and not modo_masivo: self.seleccionar_maestro_individual(maestros_filtrados[0]["nombre"])

    def al_cambiar_modo_switch(self):
        if self.switch_masivo_var.get():
            self.btn_asignar_indiv.pack_forget()
            self.btn_asignar_masivo.pack(fill="x", pady=5)
        else:
            self.btn_asignar_masivo.pack_forget()
            self.btn_asignar_indiv.pack(fill="x", pady=5)
        self.filtrar_lista_maestros()

    def seleccionar_maestro_individual(self, nombre_m):
        self.maestro_seleccionado_individual = nombre_m
        self.lbl_avatar.configure(text="".join([p[0] for p in nombre_m.strip().split()[:2]]).upper() if nombre_m.strip() else "DO")
        self.lbl_nombre_docente.configure(text=nombre_m)
        self.lbl_periodo_tag.configure(text=f"Periodo Lectivo: {self.combo_periodo.get()}")

        if nombre_m in self.maestros_dict and self.combo_periodo.get() in self.periodos_dict:
            horario = obtener_horario_maestro(self.maestros_dict[nombre_m], self.periodos_dict[self.combo_periodo.get()])
            if horario:
                self.badge_turno.configure(text=f"{'☀️ ' if 'matutino' in horario[1].lower() else '🌙 '}{horario[1].upper()}", fg_color="#1E3A8A" if "matutino" in horario[1].lower() else "#312E81", text_color="#93C5FD" if "matutino" in horario[1].lower() else "#C084FC")
                self.lbl_horario_big.configure(text=f"{horario[2]} HRS   ➔   {horario[3]} HRS", text_color=COLORES["primario"])
                self.lbl_status_footer.configure(text="🟢 Turno Asignado y Activo", text_color=COLORES["exito"])
                self.card_container.configure(border_color=COLORES["exito"])
            else:
                self.badge_turno.configure(text="SIN TURNO", fg_color="#451A03", text_color=COLORES["alerta"])
                self.lbl_horario_big.configure(text="-- : --   ➔   -- : --", text_color=COLORES["texto_secundario"])
                self.lbl_status_footer.configure(text="🔴 Sin asignación", text_color=COLORES["peligro"])
                self.card_container.configure(border_color=COLORES["bordes"])

    def guardar_asignacion_individual(self):
        if not self.maestro_seleccionado_individual or self.maestro_seleccionado_individual not in self.maestros_dict: return messagebox.showwarning("Atención", "Selecciona un maestro.")
        asignar_horario_maestro(self.maestros_dict[self.maestro_seleccionado_individual], self.periodos_dict[self.combo_periodo.get()], self.turnos_dict[self.combo_turno.get()])
        messagebox.showinfo("Éxito", f"Turno guardado.")
        self.refrescar_lista_maestros()

    def guardar_asignacion_masiva(self):
        seleccionados = [n for n, v in self.checkboxes_vars.items() if v.get()]
        if not seleccionados: return messagebox.showwarning("Atención", "Marca maestros de la lista.")
        for n in seleccionados: asignar_horario_maestro(self.maestros_dict[n], self.periodos_dict[self.combo_periodo.get()], self.turnos_dict[self.combo_turno.get()])
        messagebox.showinfo("Éxito", f"Turno asignado a {len(seleccionados)} maestros.")
        self.refrescar_lista_maestros()