# frontend/views/vista_ponchadas.py
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import pandas as pd

from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from database.modelos import guardar_ponchadas_desde_df


class VistaPonchadas(ctk.CTkFrame):
    def __init__(self, parent, on_procesar_exito=None):
        super().__init__(parent)

        self.on_procesar_exito = on_procesar_exito
        self.ruta_archivo = None
        self.df_resumen = None

        self.crear_interfaz()

    def crear_interfaz(self):
        # -------------------------------------------------------------
        # 1. ENCABEZADO Y DASHBOARD DE ESTADÍSTICAS RÁPIDAS
        # -------------------------------------------------------------
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 5))

        title_label = ctk.CTkLabel(
            header_frame, 
            text="📁 Procesador de Ponchadora", 
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#F3F4F6"
        )
        title_label.pack(side="left")

        # Indicador BD y Estado
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
        # COLUMNA IZQUIERDA: Carga de Archivo y Panel de Acciones
        # =============================================================
        left_frame = ctk.CTkFrame(main_frame, width=380, fg_color="#1E293B", corner_radius=12)
        left_frame.pack(side="left", fill="both", padx=(0, 10), pady=5)

        ctk.CTkLabel(
            left_frame, 
            text="Cargar Archivo de Marcas", 
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#93C5FD"
        ).pack(pady=(15, 5), padx=15, anchor="w")

        ctk.CTkLabel(
            left_frame, 
            text="Seleccione el CSV generado por la ponchadora.", 
            font=ctk.CTkFont(size=11),
            text_color="#9CA3AF"
        ).pack(anchor="w", padx=15, pady=(0, 10))

        # Zona de Selección de Archivo
        file_box = ctk.CTkFrame(left_frame, fg_color="#0F172A", corner_radius=8)
        file_box.pack(fill="x", padx=15, pady=5)

        self.entry_ruta = ctk.CTkEntry(
            file_box,
            placeholder_text="Ningún archivo seleccionado...",
            fg_color="transparent",
            text_color="#F3F4F6",
            border_width=0,
            height=35
        )
        self.entry_ruta.pack(side="left", fill="x", expand=True, padx=10)

        self.btn_buscar = ctk.CTkButton(
            file_box,
            text="🔎 Buscar",
            width=80,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.seleccionar_archivo
        )
        self.btn_buscar.pack(side="right", padx=5, pady=5)

        # Divisor visual
        ctk.CTkFrame(left_frame, height=2, fg_color="#334155").pack(fill="x", padx=15, pady=15)

        # Botón Principal de Procesamiento
        self.btn_procesar = ctk.CTkButton(
            left_frame,
            text="🚀 Procesar y Generar Excel",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#10B981",
            hover_color="#059669",
            height=42,
            command=self.procesar_csv
        )
        self.btn_procesar.pack(fill="x", padx=15, pady=10)

        # Estado del Proceso
        self.label_estado = ctk.CTkLabel(
            left_frame, 
            text="Esperando archivo...", 
            font=ctk.CTkFont(size=12),
            text_color="#64748B"
        )
        self.label_estado.pack(pady=10)

        # =============================================================
        # COLUMNA DERECHA: Resumen Ejecutivo y Ficha Técnica de Carga
        # =============================================================
        right_frame = ctk.CTkFrame(main_frame, fg_color="#1E293B", corner_radius=12)
        right_frame.pack(side="right", fill="both", expand=True, pady=5)

        ctk.CTkLabel(
            right_frame, 
            text="Resumen de Carga y Sincronización", 
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#93C5FD"
        ).pack(pady=(15, 10), padx=20, anchor="w")

        # Tarjeta Ficha Informativa
        self.card_container = ctk.CTkFrame(right_frame, fg_color="#0F172A", corner_radius=10, border_width=1, border_color="#334155")
        self.card_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.build_card_ui()

    def build_card_ui(self):
        """Construye los elementos informativos de la tarjeta visual."""
        # Top Box: Avatar/Ícono de Archivo e Info
        top_box = ctk.CTkFrame(self.card_container, fg_color="transparent")
        top_box.pack(fill="x", padx=20, pady=(20, 10))

        self.lbl_icon = ctk.CTkLabel(
            top_box, text="📄", font=ctk.CTkFont(size=22),
            text_color="#FFFFFF", fg_color="#334155", width=50, height=50, corner_radius=25
        )
        self.lbl_icon.pack(side="left", padx=(0, 15))

        info_meta = ctk.CTkFrame(top_box, fg_color="transparent")
        info_meta.pack(side="left", fill="both", expand=True)

        self.lbl_nombre_archivo = ctk.CTkLabel(
            info_meta, text="Sin archivo cargado",
            font=ctk.CTkFont(size=16, weight="bold"), text_color="#F3F4F6", anchor="w"
        )
        self.lbl_nombre_archivo.pack(fill="x")

        self.lbl_peso_archivo = ctk.CTkLabel(
            info_meta, text="Ruta: N/A",
            font=ctk.CTkFont(size=11), text_color="#9CA3AF", anchor="w"
        )
        self.lbl_peso_archivo.pack(fill="x")

        # Middle Box: Métricas del CSV
        metrics_box = ctk.CTkFrame(self.card_container, fg_color="#1E293B", corner_radius=8)
        metrics_box.pack(fill="x", padx=20, pady=15)

        # Grid de 2 métricas
        m1 = ctk.CTkFrame(metrics_box, fg_color="transparent")
        m1.pack(side="left", fill="both", expand=True, padx=10, pady=12)

        ctk.CTkLabel(m1, text="REGISTROS DETECTADOS", font=ctk.CTkFont(size=10, weight="bold"), text_color="#64748B").pack()
        self.lbl_stat_filas = ctk.CTkLabel(m1, text="0", font=ctk.CTkFont(size=22, weight="bold"), text_color="#38BDF8")
        self.lbl_stat_filas.pack()

        m2 = ctk.CTkFrame(metrics_box, fg_color="transparent")
        m2.pack(side="right", fill="both", expand=True, padx=10, pady=12)

        ctk.CTkLabel(m2, text="DOCENTES ÚNICOS", font=ctk.CTkFont(size=10, weight="bold"), text_color="#64748B").pack()
        self.lbl_stat_docentes = ctk.CTkLabel(m2, text="0", font=ctk.CTkFont(size=22, weight="bold"), text_color="#38BDF8")
        self.lbl_stat_docentes.pack()

        # Footer Status
        self.lbl_status_footer = ctk.CTkLabel(
            self.card_container, 
            text="🔴 Ningún dato sincronizado con SQLite aún.",
            font=ctk.CTkFont(size=12), text_color="#EF4444"
        )
        self.lbl_status_footer.pack(pady=(5, 15))

    # =============================================================
    # LÓGICA DE PROCESAMIENTO
    # =============================================================

    def seleccionar_archivo(self):
        archivo = filedialog.askopenfilename(
            title="Selecciona el CSV de la ponchadora",
            filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")],
        )
        if archivo:
            self.ruta_archivo = archivo
            nombre = os.path.basename(archivo)
            self.entry_ruta.delete(0, tk.END)
            self.entry_ruta.insert(0, nombre)

            self.lbl_nombre_archivo.configure(text=nombre)
            self.lbl_peso_archivo.configure(text=f"Ruta: ...{archivo[-35:]}")
            self.label_estado.configure(text="Archivo listo para procesar.", text_color="#38BDF8")
            self.lbl_icon.configure(fg_color="#2563EB")

    def procesar_csv(self):
        if not self.ruta_archivo:
            messagebox.showwarning("Atención", "Por favor selecciona un archivo CSV primero.")
            return

        try:
            # 1. Cargar el CSV
            try:
                df = pd.read_csv(self.ruta_archivo, sep=";", encoding="utf-8-sig", on_bad_lines="skip")
            except Exception:
                df = pd.read_csv(self.ruta_archivo, sep=";", encoding="latin1", on_bad_lines="skip")

            if df.shape[1] < 4:
                messagebox.showerror("Error", "El archivo no tiene el formato esperado.")
                return

            # 2. Tomar Fecha_Hora (Col 0) y Nombre (Col 3)
            df_sub = df.iloc[:, [0, 3]].copy()
            df_sub.columns = ["Fecha_Hora_Raw", "Nombre"]
            df_sub["Nombre"] = df_sub["Nombre"].astype(str).str.strip()
            df_sub = df_sub.dropna(subset=["Fecha_Hora_Raw", "Nombre"])

            # 3. Parseo de fechas
            df_sub["Fecha_Hora"] = pd.to_datetime(
                df_sub["Fecha_Hora_Raw"].astype(str).str.strip(),
                format="%d/%m/%Y %H:%M:%S",
                errors="coerce"
            )
            df_sub = df_sub.dropna(subset=["Fecha_Hora"])
            df_sub["Fecha_Texto"] = df_sub["Fecha_Hora"].dt.strftime("%d/%m/%Y")

            # 4. Agrupación (Entrada mínima y Salida máxima)
            df_resumen = (
                df_sub.groupby(["Fecha_Texto", "Nombre"], sort=False)
                .agg(
                    Entrada=("Fecha_Hora", lambda x: x.min().strftime("%H:%M:%S")),
                    Salida=("Fecha_Hora", lambda x: x.max().strftime("%H:%M:%S")),
                )
                .reset_index()
            )

            df_resumen.rename(columns={"Fecha_Texto": "Fecha"}, inplace=True)
            df_resumen = df_resumen[["Nombre", "Fecha", "Entrada", "Salida"]]

            # Actualizar estadísticas en la Ficha Técnica
            total_filas = len(df_resumen)
            total_docentes = df_resumen["Nombre"].nunique()

            self.lbl_stat_filas.configure(text=str(total_filas))
            self.lbl_stat_docentes.configure(text=str(total_docentes))

            # 5. Persistencia en SQLite
            try:
                guardar_ponchadas_desde_df(df_resumen)
                
                self.lbl_status_footer.configure(
                    text="🟢 Ponchadas y maestros sincronizados con la Base de Datos.",
                    text_color="#10B981"
                )
                self.card_container.configure(border_color="#10B981")

                # Disparar callback para refrescar la vista de Horarios
                if self.on_procesar_exito:
                    self.on_procesar_exito()

            except Exception as e:
                print(f"Error al guardar en BD: {e}")

            # 6. Guardar Reporte Excel Formateado
            nombre_base = os.path.splitext(os.path.basename(self.ruta_archivo))[0]
            ruta_salida = filedialog.asksaveasfilename(
                title="Guardar Excel Formateado como...",
                initialfile=f"Reporte_Asistencia_{nombre_base}.xlsx",
                defaultextension=".xlsx",
                filetypes=[("Archivos de Excel", "*.xlsx")],
            )

            if not ruta_salida:
                return

            with pd.ExcelWriter(ruta_salida, engine="openpyxl") as writer:
                df_resumen.to_excel(writer, sheet_name="Asistencia", index=False, startrow=3)
                ws = writer.sheets["Asistencia"]
                ws.views.sheetView[0].showGridLines = True

                # Estilos Ejecutivos
                font_banner = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
                font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
                font_data = Font(name="Calibri", size=11, color="1F2937")

                fill_banner = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
                fill_header = PatternFill(start_color="2F5597", end_color="2F5597", fill_type="solid")
                fill_zebra = PatternFill(start_color="F2F5F9", end_color="F2F5F9", fill_type="solid")
                fill_white = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")

                align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
                align_left = Alignment(horizontal="left", vertical="center", wrap_text=True)

                border_thin = Side(border_style="thin", color="D9D9D9")
                cell_border = Border(left=border_thin, right=border_thin, top=border_thin, bottom=border_thin)

                # BANNER DE ENCABEZADO
                ws.merge_cells("A1:D2")
                banner_cell = ws["A1"]
                banner_cell.value = "REPORTE CONSOLIDADO DE ASISTENCIA Y PONCHADAS"
                banner_cell.font = font_banner
                banner_cell.fill = fill_banner
                banner_cell.alignment = align_center

                # ENCABEZADOS
                for col_idx in range(1, 5):
                    c = ws.cell(row=4, column=col_idx)
                    c.font = font_header
                    c.fill = fill_header
                    c.alignment = align_center
                    c.border = cell_border

                # DATOS
                start_row = 5
                for row_idx in range(start_row, start_row + len(df_resumen)):
                    row_fill = fill_zebra if (row_idx % 2 == 0) else fill_white
                    for col_idx in range(1, 5):
                        c = ws.cell(row=row_idx, column=col_idx)
                        c.font = font_data
                        c.fill = row_fill
                        c.border = cell_border
                        if col_idx == 2:
                            c.number_format = "@"
                        c.alignment = align_left if col_idx == 1 else align_center

                # AUTO-AJUSTE ANCHO DE COLUMNAS
                for col in ws.columns:
                    max_len = 0
                    col_letter = get_column_letter(col[0].column)
                    for cell in col:
                        if cell.row in [1, 2]:
                            continue
                        val_str = str(cell.value or "")
                        if len(val_str) > max_len:
                            max_len = len(val_str)
                    ws.column_dimensions[col_letter].width = max(max_len + 5, 14)

            self.label_estado.configure(text="¡Excel generado con éxito!", text_color="#10B981")
            messagebox.showinfo("Éxito", f"Reporte formateado guardado en:\n{ruta_salida}")

        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al procesar el archivo:\n{str(e)}")