import customtkinter as ctk
from tkinter import messagebox
from database.modelos import (
    obtener_periodos, obtener_turnos, obtener_maestros, 
    asignar_horario_maestro, obtener_horario_maestro, crear_turno
)
from frontend.tema import COLORES
from frontend.componentes.ui_dinamica import NotificacionToast

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
        header_frame.pack(fill="x", padx=20, pady=(10, 0))

        ctk.CTkLabel(
            header_frame, text="📅 Gestor de Horarios Épico", 
            font=ctk.CTkFont(size=26, weight="bold"), text_color=COLORES["texto_principal"]
        ).pack(side="left")

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=5)

        # PANEL IZQUIERDO
        left_frame = ctk.CTkFrame(main_frame, width=380, fg_color=COLORES["panel_secundario"], corner_radius=15, border_color=COLORES["borde_acento"], border_width=2)
        left_frame.pack(side="left", fill="both", padx=(0, 15), pady=5)

        top_left = ctk.CTkFrame(left_frame, fg_color="transparent")
        top_left.pack(fill="x", padx=15, pady=(15, 5))
        ctk.CTkLabel(top_left, text="🎓 Periodo:", font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORES["texto_secundario"]).pack(side="left", padx=(0, 10))
        
        self.combo_periodo = ctk.CTkOptionMenu(
            top_left, values=["Cargando..."], command=self.al_cambiar_periodo,
            fg_color=COLORES["fondo_principal"], button_color=COLORES["panel_terciario"], 
            button_hover_color=COLORES["primario_hover"], height=35, text_color=COLORES["texto_principal"], font=ctk.CTkFont(size=12, weight="bold")
        )
        self.combo_periodo.pack(side="right", fill="x", expand=True)

        self.entry_buscar = ctk.CTkEntry(
            left_frame, placeholder_text="🔎 Buscar maestro...", fg_color=COLORES["fondo_principal"], 
            text_color=COLORES["texto_principal"], border_color=COLORES["bordes"], height=35, font=ctk.CTkFont(size=12)
        )
        self.entry_buscar.pack(fill="x", padx=15, pady=5)
        self.entry_buscar.bind("<KeyRelease>", lambda e: self.filtrar_lista_maestros())

        scroll_chips = ctk.CTkScrollableFrame(left_frame, fg_color="transparent", height=40, orientation="horizontal")
        scroll_chips.pack(fill="x", padx=10, pady=0)
        
        self.btn_f_todos = ctk.CTkButton(scroll_chips, text="Todos", width=60, height=26, font=ctk.CTkFont(size=11, weight="bold"), fg_color=COLORES["primario"], corner_radius=6, command=lambda: self.set_filtro("TODOS"))
        self.btn_f_todos.pack(side="left", padx=3)
        self.btn_f_matutino = ctk.CTkButton(scroll_chips, text="☀️ Mat", width=60, height=26, font=ctk.CTkFont(size=11, weight="bold"), fg_color=COLORES["panel_terciario"], hover_color="#1E3A8A", corner_radius=6, command=lambda: self.set_filtro("MATUTINO"))
        self.btn_f_matutino.pack(side="left", padx=3)
        self.btn_f_vespertino = ctk.CTkButton(scroll_chips, text="🌙 Vesp", width=60, height=26, font=ctk.CTkFont(size=11, weight="bold"), fg_color=COLORES["panel_terciario"], hover_color="#312E81", corner_radius=6, command=lambda: self.set_filtro("VESPERTINO"))
        self.btn_f_vespertino.pack(side="left", padx=3)
        self.btn_f_mixto = ctk.CTkButton(scroll_chips, text="⚡ Mixto", width=60, height=26, font=ctk.CTkFont(size=11, weight="bold"), fg_color=COLORES["panel_terciario"], hover_color="#047857", corner_radius=6, command=lambda: self.set_filtro("MIXTO"))
        self.btn_f_mixto.pack(side="left", padx=3)
        self.btn_f_sinturno = ctk.CTkButton(scroll_chips, text="⚠️ Sin Turno", width=75, height=26, font=ctk.CTkFont(size=11, weight="bold"), fg_color=COLORES["panel_terciario"], hover_color=COLORES["alerta"], corner_radius=6, command=lambda: self.set_filtro("SIN_TURNO"))
        self.btn_f_sinturno.pack(side="left", padx=3)

        self.scroll_maestros = ctk.CTkScrollableFrame(left_frame, fg_color=COLORES["fondo_principal"], corner_radius=10, border_color=COLORES["bordes"], border_width=1)
        self.scroll_maestros.pack(side="top", fill="both", expand=True, padx=15, pady=(10, 15))

        # PANEL DERECHO
        right_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        right_frame.pack(side="right", fill="both", expand=True, pady=5)

        self.card_container = ctk.CTkFrame(right_frame, fg_color=COLORES["panel_secundario"], corner_radius=16, border_width=2, border_color=COLORES["bordes"])
        self.card_container.pack(side="top", fill="x", padx=(5, 0), pady=(0, 10))
        self.build_card_ui()

        action_box = ctk.CTkFrame(right_frame, fg_color=COLORES["panel_secundario"], corner_radius=16, border_width=1, border_color=COLORES["bordes"])
        action_box.pack(side="top", fill="x", padx=(5, 0), pady=(0, 10))
        
        inner_action = ctk.CTkFrame(action_box, fg_color="transparent")
        inner_action.pack(fill="both", expand=True, padx=20, pady=15)

        top_act = ctk.CTkFrame(inner_action, fg_color="transparent")
        top_act.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(top_act, text="⚙️ Asignar Turno", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORES["texto_principal"]).pack(side="left")
        
        self.switch_masivo_var = ctk.BooleanVar(value=False)
        self.switch_masivo = ctk.CTkSwitch(
            top_act, text="Selección Múltiple", variable=self.switch_masivo_var,
            font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORES["alerta"], command=self.al_cambiar_modo_switch
        )
        self.switch_masivo.pack(side="right")

        combo_row = ctk.CTkFrame(inner_action, fg_color="transparent")
        combo_row.pack(fill="x", pady=(0, 15))

        self.combo_turno = ctk.CTkOptionMenu(
            combo_row, values=["Cargando..."], fg_color=COLORES["fondo_principal"], button_color=COLORES["panel_terciario"], 
            button_hover_color=COLORES["primario_hover"], height=40, text_color=COLORES["texto_principal"], font=ctk.CTkFont(size=13, weight="bold")
        )
        self.combo_turno.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_crear_turno = ctk.CTkButton(
            combo_row, text="➕ Nuevo Turno", width=110, height=40, fg_color="#10B981", hover_color="#059669", 
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#FFFFFF", corner_radius=8, command=self.abrir_modal_crear_turno
        )
        self.btn_crear_turno.pack(side="right")

        self.btn_asignar_indiv = ctk.CTkButton(
            inner_action, text="💾 Guardar Turno y Sincronizar", fg_color=COLORES["primario"], hover_color=COLORES["primario_hover"],
            font=ctk.CTkFont(size=14, weight="bold"), height=45, corner_radius=10, text_color="#FFFFFF", command=self.guardar_asignacion_individual
        )
        self.btn_asignar_indiv.pack(fill="x")
        
        self.btn_asignar_masivo = ctk.CTkButton(
            inner_action, text="🚀 Aplicar a Múltiples Seleccionados", fg_color=COLORES["alerta"], hover_color="#B45309",
            font=ctk.CTkFont(size=14, weight="bold"), height=45, corner_radius=10, text_color="#FFFFFF", command=self.guardar_asignacion_masiva
        )
        self.btn_asignar_masivo.pack_forget()

    def build_card_ui(self):
        top_box = ctk.CTkFrame(self.card_container, fg_color="transparent")
        top_box.pack(fill="x", padx=20, pady=(20, 10))
        
        self.lbl_avatar = ctk.CTkLabel(top_box, text="--", font=ctk.CTkFont(size=22, weight="bold"), text_color="#FFFFFF", fg_color=COLORES["primario"], width=60, height=60, corner_radius=30)
        self.lbl_avatar.pack(side="left", padx=(0, 15))
        
        info_meta = ctk.CTkFrame(top_box, fg_color="transparent")
        info_meta.pack(side="left", fill="both", expand=True)
        self.lbl_nombre_docente = ctk.CTkLabel(info_meta, text="Seleccione un maestro", font=ctk.CTkFont(size=20, weight="bold"), text_color=COLORES["texto_principal"], anchor="w")
        self.lbl_nombre_docente.pack(fill="x")
        self.lbl_periodo_tag = ctk.CTkLabel(info_meta, text="Periodo: N/A", font=ctk.CTkFont(size=12), text_color=COLORES["texto_secundario"], anchor="w")
        self.lbl_periodo_tag.pack(fill="x")

        badges_box = ctk.CTkFrame(info_meta, fg_color="transparent")
        badges_box.pack(fill="x", pady=(5, 0))
        self.badge_turno = ctk.CTkLabel(badges_box, text="SIN TURNO", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLORES["alerta"], fg_color="#451A03", corner_radius=6, padx=10, pady=3)
        self.badge_turno.pack(side="left")

        ctk.CTkLabel(self.card_container, text="Mapeo Semanal de Entradas y Salidas", font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORES["texto_secundario"]).pack(anchor="w", padx=20, pady=(10, 0))
        
        self.grid_semanal = ctk.CTkFrame(self.card_container, fg_color=COLORES["fondo_principal"], corner_radius=12)
        self.grid_semanal.pack(fill="both", expand=True, padx=20, pady=(5, 15))
        
        self.dias_frames = {}
        nombres_dias = ["LUN", "MAR", "MIE", "JUE", "VIE"]
        
        for d in nombres_dias:
            col = ctk.CTkFrame(self.grid_semanal, fg_color="transparent")
            col.pack(side="left", fill="both", expand=True, padx=4, pady=8)
            ctk.CTkLabel(col, text=d, font=ctk.CTkFont(size=11, weight="bold"), text_color=COLORES["texto_secundario"]).pack(pady=(0, 4))
            
            bloque = ctk.CTkFrame(col, fg_color=COLORES["panel_terciario"], corner_radius=6, height=50)
            bloque.pack(fill="both", expand=True)
            bloque.pack_propagate(False)
            
            lbl_h = ctk.CTkLabel(bloque, text="--:--\n--:--", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLORES["texto_secundario"])
            lbl_h.place(relx=0.5, rely=0.5, anchor="center")
            
            self.dias_frames[d] = {"frame": bloque, "label": lbl_h}

    def cargar_datos_bd(self):
        periodos = obtener_periodos()
        if periodos:
            self.periodos_dict = {p[1]: p[0] for p in periodos}
            self.combo_periodo.configure(values=list(self.periodos_dict.keys()))
            if not self.combo_periodo.get() or self.combo_periodo.get() not in self.periodos_dict: self.combo_periodo.set(list(self.periodos_dict.keys())[0])
        self.refrescar_combo_turnos()
        self.refrescar_lista_maestros()

    def refrescar_combo_turnos(self):
        turnos = obtener_turnos()
        if turnos:
            self.turnos_dict = {f"{t[1]} ({t[2]} a {t[3]})": t[0] for t in turnos}
            self.combo_turno.configure(values=list(self.turnos_dict.keys()))
            if not self.combo_turno.get() or self.combo_turno.get() not in self.turnos_dict: 
                self.combo_turno.set(list(self.turnos_dict.keys())[0])
        else:
            self.combo_turno.configure(values=["Sin turnos creados"])
            self.combo_turno.set("Sin turnos creados")

    def abrir_modal_crear_turno(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Crear Nuevo Turno")
        modal.geometry("400x450")
        modal.configure(fg_color=COLORES["fondo_principal"])
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        ctk.CTkLabel(modal, text="✨ Configurar Turno", font=ctk.CTkFont(size=22, weight="bold"), text_color=COLORES["texto_principal"]).pack(pady=(20, 10))
        
        ctk.CTkLabel(modal, text="Nombre (Ej. Matutino, Vespertino 2):", text_color=COLORES["texto_secundario"]).pack(anchor="w", padx=30, pady=(10, 0))
        e_nombre = ctk.CTkEntry(modal, height=40, fg_color=COLORES["panel_secundario"])
        e_nombre.pack(fill="x", padx=30, pady=5)

        ctk.CTkLabel(modal, text="Hora Entrada (HH:MM:SS):", text_color=COLORES["texto_secundario"]).pack(anchor="w", padx=30, pady=(10, 0))
        e_entrada = ctk.CTkEntry(modal, placeholder_text="08:00:00", height=40, fg_color=COLORES["panel_secundario"])
        e_entrada.pack(fill="x", padx=30, pady=5)

        ctk.CTkLabel(modal, text="Hora Salida (HH:MM:SS):", text_color=COLORES["texto_secundario"]).pack(anchor="w", padx=30, pady=(10, 0))
        e_salida = ctk.CTkEntry(modal, placeholder_text="16:00:00", height=40, fg_color=COLORES["panel_secundario"])
        e_salida.pack(fill="x", padx=30, pady=5)

        def guardar_nuevo_turno():
            nom = e_nombre.get().strip()
            ent = e_entrada.get().strip()
            sal = e_salida.get().strip()
            if not nom or not ent or not sal:
                return messagebox.showwarning("Faltan datos", "Llena todos los campos.")
            if ":" not in ent or ":" not in sal:
                return messagebox.showwarning("Formato", "Usa formato HH:MM:SS (Ej. 08:00:00)")
            if len(ent.split(":")) == 2: ent += ":00"
            if len(sal.split(":")) == 2: sal += ":00"

            crear_turno(nom, ent, sal)
            self.refrescar_combo_turnos()
            NotificacionToast(self, f"Turno {nom} creado con éxito.", "exito")
            modal.destroy()

        ctk.CTkButton(modal, text="Guardar Turno", height=45, corner_radius=10, fg_color=COLORES["primario"], command=guardar_nuevo_turno).pack(fill="x", padx=30, pady=25)

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
        botones = [self.btn_f_todos, self.btn_f_matutino, self.btn_f_vespertino, self.btn_f_mixto, self.btn_f_sinturno]
        for b in botones: b.configure(fg_color=COLORES["panel_terciario"])
        
        if nuevo_filtro == "TODOS": self.btn_f_todos.configure(fg_color=COLORES["primario"])
        elif nuevo_filtro == "MATUTINO": self.btn_f_matutino.configure(fg_color="#1E3A8A")
        elif nuevo_filtro == "VESPERTINO": self.btn_f_vespertino.configure(fg_color="#312E81")
        elif nuevo_filtro == "MIXTO": self.btn_f_mixto.configure(fg_color="#047857")
        elif nuevo_filtro == "SIN_TURNO": self.btn_f_sinturno.configure(fg_color=COLORES["alerta"])
        self.filtrar_lista_maestros()

    def filtrar_lista_maestros(self):
        texto_busqueda = self.entry_buscar.get().strip().lower()
        for w in self.scroll_maestros.winfo_children(): w.destroy()
        self.checkboxes_vars.clear()
        modo_masivo = self.switch_masivo_var.get()
        
        maestros_filtrados = []
        for m in self.maestros_lista:
            if texto_busqueda and texto_busqueda not in m["nombre"].lower(): continue
            t_low = m["turno"].lower()
            if self.filtro_estado == "SIN_TURNO" and m["turno"] != "SIN_TURNO": continue
            if self.filtro_estado == "MATUTINO" and "matutino" not in t_low: continue
            if self.filtro_estado == "VESPERTINO" and "vespertino" not in t_low: continue
            if self.filtro_estado == "MIXTO" and ("mixto" not in t_low and "quebrado" not in t_low): continue
            maestros_filtrados.append(m)
        
        for m in maestros_filtrados:
            row_frame = ctk.CTkFrame(self.scroll_maestros, fg_color="transparent", corner_radius=8)
            row_frame.pack(fill="x", pady=1, padx=4)
            
            def on_enter(e, f=row_frame): f.configure(fg_color=COLORES["panel_secundario"])
            def on_leave(e, f=row_frame): f.configure(fg_color="transparent")
            row_frame.bind("<Enter>", on_enter)
            row_frame.bind("<Leave>", on_leave)

            if modo_masivo:
                var = ctk.BooleanVar(value=False)
                chk = ctk.CTkCheckBox(row_frame, text=m["nombre"], variable=var, font=ctk.CTkFont(size=12), text_color=COLORES["texto_principal"], fg_color=COLORES["primario"], hover_color=COLORES["primario_hover"])
                chk.pack(side="left", padx=10, pady=8)
                self.checkboxes_vars[m["nombre"]] = var
            else:
                btn_m = ctk.CTkButton(row_frame, text=m["nombre"], anchor="w", fg_color="transparent", hover_color=COLORES["panel_terciario"], text_color=COLORES["texto_principal"], font=ctk.CTkFont(size=12, weight="bold"), command=lambda n=m["nombre"]: self.seleccionar_maestro_individual(n))
                btn_m.pack(side="left", fill="x", expand=True, padx=6, pady=4)
                btn_m.bind("<Enter>", on_enter)
                btn_m.bind("<Leave>", on_leave)
            
            color_punto = COLORES["alerta"]
            if m["turno"] != "SIN_TURNO":
                if "matutino" in m["turno"].lower(): color_punto = "#3B82F6"
                elif "vespertino" in m["turno"].lower(): color_punto = "#8B5CF6"
                else: color_punto = "#10B981"
                
            punto = ctk.CTkLabel(row_frame, text="●", text_color=color_punto, font=ctk.CTkFont(size=16))
            punto.pack(side="right", padx=10)
        
        if self.maestro_seleccionado_individual: self.seleccionar_maestro_individual(self.maestro_seleccionado_individual)
        elif maestros_filtrados and not modo_masivo: self.seleccionar_maestro_individual(maestros_filtrados[0]["nombre"])

    def al_cambiar_modo_switch(self):
        if self.switch_masivo_var.get():
            self.btn_asignar_indiv.pack_forget()
            self.btn_asignar_masivo.pack(fill="x")
        else:
            self.btn_asignar_masivo.pack_forget()
            self.btn_asignar_indiv.pack(fill="x")
        self.filtrar_lista_maestros()

    def seleccionar_maestro_individual(self, nombre_m):
        self.maestro_seleccionado_individual = nombre_m
        self.lbl_avatar.configure(text="".join([p[0] for p in nombre_m.strip().split()[:2]]).upper() if nombre_m.strip() else "DO")
        self.lbl_nombre_docente.configure(text=nombre_m)
        self.lbl_periodo_tag.configure(text=f"Periodo: {self.combo_periodo.get()}")

        for f in self.dias_frames.values():
            f["frame"].configure(fg_color=COLORES["panel_terciario"])
            f["label"].configure(text="--:--\n--:--", text_color=COLORES["texto_secundario"])

        if nombre_m in self.maestros_dict and self.combo_periodo.get() in self.periodos_dict:
            horario = obtener_horario_maestro(self.maestros_dict[nombre_m], self.periodos_dict[self.combo_periodo.get()])
            if horario:
                t_nombre = horario[1].lower()
                # Colores en Hexadecimal, no RGBA
                if "matutino" in t_nombre:
                    color_bg = "#1E3A8A"
                    color_texto = "#93C5FD"
                    self.badge_turno.configure(text="MATUTINO", fg_color="#1E3A8A", text_color=color_texto)
                elif "vespertino" in t_nombre:
                    color_bg = "#4C1D95"
                    color_texto = "#C4B5FD"
                    self.badge_turno.configure(text="VESPERTINO", fg_color="#4C1D95", text_color=color_texto)
                else:
                    color_bg = "#064E3B"
                    color_texto = "#6EE7B7"
                    self.badge_turno.configure(text="TURNO MIXTO", fg_color="#064E3B", text_color=color_texto)

                dias_bd = horario[4].upper() if len(horario) > 4 and horario[4] else "LUN, MAR, MIE, JUE, VIE"
                for d in self.dias_frames.keys():
                    if d in dias_bd:
                        self.dias_frames[d]["frame"].configure(fg_color=color_bg)
                        self.dias_frames[d]["label"].configure(text=f"{horario[2][:5]}\n|\n{horario[3][:5]}", text_color=color_texto)
            else:
                self.badge_turno.configure(text="SIN TURNO", fg_color="#451A03", text_color=COLORES["alerta"])

    def guardar_asignacion_individual(self):
        if not self.maestro_seleccionado_individual or self.maestro_seleccionado_individual not in self.maestros_dict: 
            return NotificacionToast(self, "Selecciona un maestro primero.", "error")
        if self.combo_turno.get() == "Sin turnos creados":
            return NotificacionToast(self, "Crea un turno primero.", "error")
            
        asignar_horario_maestro(self.maestros_dict[self.maestro_seleccionado_individual], self.periodos_dict[self.combo_periodo.get()], self.turnos_dict[self.combo_turno.get()])
        NotificacionToast(self, f"Turno configurado para {self.maestro_seleccionado_individual[:15]}.", "exito")
        self.refrescar_lista_maestros()

    def guardar_asignacion_masiva(self):
        seleccionados = [n for n, v in self.checkboxes_vars.items() if v.get()]
        if not seleccionados: 
            return NotificacionToast(self, "Marca casillas en la lista.", "error")
        if self.combo_turno.get() == "Sin turnos creados":
            return NotificacionToast(self, "Crea un turno primero.", "error")
            
        for n in seleccionados: 
            asignar_horario_maestro(self.maestros_dict[n], self.periodos_dict[self.combo_periodo.get()], self.turnos_dict[self.combo_turno.get()])
            
        NotificacionToast(self, f"¡Sincronizado! Tolerancia ajustada para {len(seleccionados)} docentes.", "exito")
        self.refrescar_lista_maestros()