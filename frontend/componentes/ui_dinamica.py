import customtkinter as ctk

class NotificacionToast:
    def __init__(self, parent, mensaje, tipo="exito"):
        self.parent = parent.winfo_toplevel()
        self.mensaje = mensaje
        
        colores = {
            "exito": {"fondo": "#064E3B", "borde": "#10B981", "icono": "✅"},
            "error": {"fondo": "#7F1D1D", "borde": "#EF4444", "icono": "❌"},
            "info":  {"fondo": "#1E3A8A", "borde": "#3B82F6", "icono": "ℹ️"}
        }
        
        tema = colores.get(tipo, colores["info"])
        
        self.frame = ctk.CTkFrame(
            self.parent, 
            fg_color=tema["fondo"], 
            corner_radius=12, 
            border_width=2, 
            border_color=tema["borde"]
        )
        
        self.lbl = ctk.CTkLabel(
            self.frame, 
            text=f"{tema['icono']}  {self.mensaje}", 
            text_color="#FFFFFF", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.lbl.pack(padx=25, pady=15)
        
        self.parent.update_idletasks()
        ancho_app = self.parent.winfo_width()
        alto_app = self.parent.winfo_height()
        
        if ancho_app < 100: ancho_app = 1000
        if alto_app < 100: alto_app = 700
        
        self.width = 350
        self.x_pos = (ancho_app // 2) - (self.width // 2)
        
        self.y_escondido = alto_app + 20 
        self.y_visible = alto_app - 80 
        
        self.pos_actual = self.y_escondido
        self.frame.place(x=self.x_pos, y=self.pos_actual)
        
        self.animar_entrada()

    def animar_entrada(self):
        try:
            if self.pos_actual > self.y_visible:
                self.pos_actual -= 8
                self.frame.place(y=self.pos_actual)
                self.parent.after(15, self.animar_entrada)
            else:
                self.parent.after(3000, self.animar_salida)
        except Exception:
            pass
            
    def animar_salida(self):
        try:
            if self.pos_actual < self.y_escondido:
                self.pos_actual += 8
                self.frame.place(y=self.pos_actual)
                self.parent.after(15, self.animar_salida)
            else:
                self.frame.destroy()
        except Exception:
            pass