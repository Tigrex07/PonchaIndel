# main.py
from database.scripts.init_db import inicializar_bd
from frontend.app import AppLimpiador

if __name__ == "__main__":
  # Inicializa la BD si no existe el archivo ponchaindel.db
  inicializar_bd()

  # Arranca la aplicación de CustomTkinter
  app = AppLimpiador()
  app.mainloop()