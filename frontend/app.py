# frontend/app.py
import customtkinter as ctk
from frontend.views.vista_ponchadas import VistaPonchadas
from frontend.views.vista_reportes import VistaReportes
from frontend.views.vista_horarios import VistaHorarios

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class AppLimpiador(ctk.CTk):

  def __init__(self):
    super().__init__()

    self.title(
        "PonchaIndel 2026 - Sistema de Gestión de Asistencia, Reportes y"
        " Horarios"
    )
    self.geometry("1050x720")
    self.resizable(True, True)

    # Contenedor de Pestañas Principal (3 Módulos)
    self.tabview = ctk.CTkTabview(self)
    self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

    # Definir las 3 Páginas/Pestañas
    self.tab_ingesta = self.tabview.add("📁 1. Carga y Sincronización CSV")
    self.tab_reportes = self.tabview.add(
        "📊 2. Incidencias y Reportes Quincenales"
    )
    self.tab_horarios = self.tabview.add("📅 3. Gestor de Horarios PA")

    # 1. Cargar Vista 3: Gestor de Horarios
    self.vista_horarios = VistaHorarios(self.tab_horarios)
    self.vista_horarios.pack(fill="both", expand=True)

    # 2. Cargar Vista 2: Reportes, Incidencias y KPIs
    self.vista_reportes = VistaReportes(self.tab_reportes)
    self.vista_reportes.pack(fill="both", expand=True)

    # 3. Cargar Vista 1: Ingesta CSV (Notifica cambio a las vistas 2 y 3)
    self.vista_ingesta = VistaPonchadas(
        self.tab_ingesta, on_procesar_exito=self.refrescar_vistas_dependientes
    )
    self.vista_ingesta.pack(fill="both", expand=True)

  def refrescar_vistas_dependientes(self):
    """Notifica a los Módulos 2 y 3 que hay datos nuevos en SQLite para refrescar estadísticas y listas."""
    if hasattr(self.vista_reportes, "actualizar_datos"):
      self.vista_reportes.actualizar_datos()
    if hasattr(self.vista_horarios, "actualizar_datos"):
      self.vista_horarios.actualizar_datos()


if __name__ == "__main__":
  app = AppLimpiador()
  app.mainloop()