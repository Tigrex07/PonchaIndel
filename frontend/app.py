import customtkinter as ctk
from frontend.views.vista_ponchadas import VistaPonchadas
from frontend.views.vista_horarios import VistaHorarios

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class AppLimpiador(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("PonchaIndel 2026 - Sistema de Gestión de Asistencia y Horarios")
        self.geometry("850x620")
        self.resizable(True, True)

        # Contenedor de Pestañas
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # Crear las dos pestañas
        self.tab_csv = self.tabview.add("📁 Procesador CSV")
        self.tab_horarios = self.tabview.add("📅 Gestor de Horarios PA")

        # Cargar Vista 1: Procesador CSV
        self.vista_csv = VistaPonchadas(self.tab_csv)
        self.vista_csv.pack(fill="both", expand=True)

        # Cargar Vista 2: Gestor de Horarios
        self.vista_horarios = VistaHorarios(self.tab_horarios)
        self.vista_horarios.pack(fill="both", expand=True)


if __name__ == "__main__":
    app = AppLimpiador()
    app.mainloop()