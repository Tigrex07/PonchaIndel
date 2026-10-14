import customtkinter as ctk
from frontend.views.vista_ponchadas import VistaPonchadas
from frontend.views.vista_reportes import VistaReportes
from frontend.views.vista_horarios import VistaHorarios
from frontend.tema import COLORES

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AppLimpiador(ctk.CTk):

  def __init__(self):
    super().__init__()

    self.title("PonchaIndel 2026 🚀 - Panel de Control Integral")
    self.geometry("1150x780") # Un poco más despacio para respirar
    self.resizable(True, True)
    
    self.configure(fg_color=COLORES["fondo_principal"])

    # Tabview con diseño moderno
    self.tabview = ctk.CTkTabview(
        self,
        fg_color=COLORES["panel_secundario"],
        segmented_button_fg_color=COLORES["panel_terciario"],
        segmented_button_selected_color=COLORES["primario"],
        segmented_button_selected_hover_color=COLORES["primario_hover"],
        text_color=COLORES["texto_principal"],
        corner_radius=15,
        border_width=0
    )
    self.tabview.pack(fill="both", expand=True, padx=20, pady=20)

    # Nombres más amigables
    self.tab_ingesta = self.tabview.add("📁 1. Sincronización")
    self.tab_reportes = self.tabview.add("📊 2. Reportes")
    self.tab_horarios = self.tabview.add("📅 3. Horarios")

    self.tab_ingesta.configure(fg_color=COLORES["fondo_principal"])
    self.tab_reportes.configure(fg_color=COLORES["fondo_principal"])
    self.tab_horarios.configure(fg_color=COLORES["fondo_principal"])

    self.vista_horarios = VistaHorarios(self.tab_horarios)
    self.vista_horarios.pack(fill="both", expand=True)

    self.vista_reportes = VistaReportes(self.tab_reportes)
    self.vista_reportes.pack(fill="both", expand=True)

    self.vista_ingesta = VistaPonchadas(
        self.tab_ingesta, on_procesar_exito=self.refrescar_vistas_dependientes
    )
    self.vista_ingesta.pack(fill="both", expand=True)

  def refrescar_vistas_dependientes(self):
    if hasattr(self.vista_reportes, "actualizar_datos"):
      self.vista_reportes.actualizar_datos()
    if hasattr(self.vista_horarios, "actualizar_datos"):
      self.vista_horarios.actualizar_datos()

if __name__ == "__main__":
  app = AppLimpiador()
  app.mainloop()