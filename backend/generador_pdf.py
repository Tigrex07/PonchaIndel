# backend/generador_pdf.py
from datetime import datetime, timedelta, time
import os
import subprocess
import sys

from reportlab.lib.pagesizes import legal, landscape
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import pandas as pd


class GeneradorPDFPaginado:
    def __init__(self):
        pass

    def generar_control_quincenal_pdf(
        self,
        departamento,
        periodo_texto,
        fecha_inicio_str,
        fecha_fin_str,
        df_registros,
        ruta_salida,
    ):
        # CAMBIO CLAVE: Usar tamaño OFICIO (Legal) en Horizontal para ganar 30% más de ancho real
        doc = SimpleDocTemplate(
            ruta_salida,
            pagesize=landscape(legal),
            rightMargin=15,
            leftMargin=15,
            topMargin=18,
            bottomMargin=18,
        )

        styles = getSampleStyleSheet()
        
        estilo_titulo = ParagraphStyle(
            'TituloInstitucional',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=12,
            alignment=1,
            textColor=colors.HexColor('#1F2937')
        )

        # Tipografía optimizada y ultra compacta (5.5pt) para perfecta lectura en celdas de días
        estilo_celda = ParagraphStyle(
            'CeldaTabla',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=5.5,
            leading=6.5,
            alignment=1
        )

        estilo_nombre = ParagraphStyle(
            'CeldaNombre',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=6.5,
            leading=7.5,
            alignment=0
        )

        estilo_alerta = ParagraphStyle(
            'CeldaAlerta',
            parent=estilo_celda,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#990000')
        )

        estilo_notas = ParagraphStyle(
            'NotasPie',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=6,
            leading=7.5,
            textColor=colors.HexColor('#374151')
        )

        estilo_simbologia = ParagraphStyle(
            'SimbologiaPie',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=5.5,
            leading=7,
            textColor=colors.HexColor('#1F2937'),
            alignment=1
        )

        dt_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d")
        dt_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d")

        dias_quincena = []
        actual = dt_inicio
        while actual <= dt_fin:
            dias_quincena.append(actual)
            actual += timedelta(days=1)

        maestros_unicos = []
        if df_registros is not None and not df_registros.empty:
            if "Nombre" in df_registros.columns:
                maestros_unicos = df_registros["Nombre"].unique().tolist()

        elementos = []
        
        # Bloques eficientes de 16 docentes por página en tamaño Oficio
        TAMANO_BLOQUE = 16
        bloques_maestros = [
            maestros_unicos[i:i + TAMANO_BLOQUE] 
            for i in range(0, len(maestros_unicos), TAMANO_BLOQUE)
        ]
        if not bloques_maestros:
            bloques_maestros = [[]]

        ruta_logo_utn = "assets/logos/logo-utn.png"
        ruta_logo_iqs = "assets/logos/logo-iqs.png"

        total_paginas = len(bloques_maestros)

        for num_pag, grupo_docentes in enumerate(bloques_maestros, 1):
            # 1. Cabecera con Logotipos
            img_l = RLImage(ruta_logo_utn, width=75, height=32) if os.path.exists(ruta_logo_utn) else Paragraph("", styles['Normal'])
            img_r = RLImage(ruta_logo_iqs, width=32, height=32) if os.path.exists(ruta_logo_iqs) else Paragraph("", styles['Normal'])

            header_texto = Paragraph(
                f"<b>Control Quincenal de Asistencia Administrativo y PTC</b><br/>"
                f"<font size=8>Area/Dirección: {departamento}</font><br/>"
                f"<font size=8 color='#2563EB'>Quincena del: {periodo_texto}</font>",
                estilo_titulo
            )

            # Ancho total de Oficio Landscape = 1008 pt. Márgenes de 15 izq/der = 978 pt útiles.
            tabla_header = Table([[img_l, header_texto, img_r]], colWidths=[90, 798, 90])
            tabla_header.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('ALIGN', (0,0), (0,0), 'LEFT'),
                ('ALIGN', (2,0), (2,0), 'RIGHT'),
            ]))
            elementos.append(tabla_header)
            elementos.append(Spacer(1, 5))

            # 2. Construcción de la Tabla de Asistencia
            fila_dias = ["NOMBRE"]
            for d in dias_quincena:
                fila_dias.extend([str(d.day), ""])
            fila_dias.append("TOTAL")

            fila_sub = [""]
            for _ in dias_quincena:
                fila_sub.extend(["Ent", "Sal"])
            fila_sub.append("HRS")

            tabla_datos = [fila_dias, fila_sub]

            for nombre_docente in grupo_docentes:
                partes_nombre = nombre_docente.split(" ")
                if len(partes_nombre) > 2:
                    mitad = len(partes_nombre) // 2
                    nombre_formateado = f"{' '.join(partes_nombre[:mitad])}<br/>{' '.join(partes_nombre[mitad:])}"
                else:
                    nombre_formateado = nombre_docente

                fila_doc = [Paragraph(nombre_formateado, estilo_nombre)]
                df_docente = df_registros[df_registros["Nombre"] == nombre_docente] if not df_registros.empty else pd.DataFrame()

                minutos_totales_trabajados = 0

                for dt_dia in dias_quincena:
                    sub_dia = df_docente[df_docente["fecha"].apply(lambda x: self._es_mismo_dia(x, dt_dia))] if not df_docente.empty else pd.DataFrame()
                    entradas = sub_dia[sub_dia["tipo"] == "ENTRADA"]["hora"].values if not sub_dia.empty else []
                    salidas = sub_dia[sub_dia["tipo"] == "SALIDA"]["hora"].values if not sub_dia.empty else []

                    es_fin_de_semana = dt_dia.weekday() >= 5
                    t_ing, t_sal = None, None
                    val_e, val_s = "", ""

                    if len(entradas) > 0:
                        h_ent_raw = str(entradas[0])
                        try:
                            t_ing = datetime.strptime(h_ent_raw, "%H:%M:%S").time()
                            h_ent = t_ing.strftime("%H:%M")
                            t_tol = time(8, 10, 0)
                            if t_ing > t_tol:
                                dt_tol = datetime.combine(datetime.today(), t_tol)
                                dt_ing_val = datetime.combine(datetime.today(), t_ing)
                                min_ret = int((dt_ing_val - dt_tol).total_seconds() / 60)
                                # Formato en línea ultra limpio para evitar saltos extraños
                                val_e = f"{h_ent} <font color='#990000'><b>(+{min_ret}m)</b></font>"
                            else:
                                val_e = h_ent
                        except ValueError:
                            val_e = h_ent_raw[:5]
                    else:
                        val_e = "" if es_fin_de_semana else "FI"

                    if len(salidas) > 0:
                        h_sal_raw = str(salidas[0])
                        try:
                            t_sal = datetime.strptime(h_sal_raw, "%H:%M:%S").time()
                            val_s = t_sal.strftime("%H:%M")
                        except ValueError:
                            val_s = h_sal_raw[:5]
                    else:
                        if len(entradas) > 0 and not es_fin_de_semana:
                            val_s = "FIS"

                    if t_ing and t_sal:
                        dt_i = datetime.combine(datetime.today(), t_ing)
                        dt_s = datetime.combine(datetime.today(), t_sal)
                        diff = (dt_s - dt_i).total_seconds()
                        if diff > 0:
                            minutos_totales_trabajados += int(diff / 60)

                    est_e = estilo_alerta if ("FI" in val_e or "+" in val_e) else estilo_celda
                    est_s = estilo_alerta if ("FIS" in val_s) else estilo_celda

                    fila_doc.append(Paragraph(val_e, est_e))
                    fila_doc.append(Paragraph(val_s, est_s))

                hrs = minutos_totales_trabajados // 60
                mins = minutos_totales_trabajados % 60
                fila_doc.append(Paragraph(f"<b>{hrs}h {mins}m</b>", estilo_celda))
                tabla_datos.append(fila_doc)

            # Cálculo exacto de anchos para Oficio Landscape (978 pt útiles)
            ancho_nombre = 110
            ancho_total = 48
            ancho_disponible = 978 - ancho_nombre - ancho_total
            ancho_dia = ancho_disponible / (len(dias_quincena) * 2)
            anchos_col = [ancho_nombre] + [ancho_dia] * (len(dias_quincena) * 2) + [ancho_total]

            t = Table(tabla_datos, colWidths=anchos_col, repeatRows=2)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,1), colors.HexColor('#1F2937')),
                ('TEXTCOLOR', (0,0), (-1,1), colors.white),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('GRID', (0,0), (-1,-1), 0.4, colors.HexColor('#CCCCCC')),
                ('FONTNAME', (0,0), (-1,1), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
                ('TOPPADDING', (0,0), (-1,-1), 3.5),
            ]))

            elementos.append(t)
            elementos.append(Spacer(1, 4))

            # 3. Leyendas, Notas y Simbología obligatorias en TODAS las hojas
            texto_simb_str = (
                "<b>FI</b> = Falta Injustificada &nbsp;|&nbsp; "
                "<b>FIS</b> = Falta, Salida No Registrada &nbsp;|&nbsp; "
                "<b>FIE</b> = Falta, Entrada No Registrada &nbsp;|&nbsp; "
                "<b>I</b> = Incapacidad &nbsp;|&nbsp; <b>AM</b> = Atención Médica &nbsp;|&nbsp; "
                "<b>P</b> = Permiso &nbsp;|&nbsp; <b>C</b> = Comisión &nbsp;|&nbsp; <b>PS</b> = Permiso Sin Goce"
            )
            tabla_simb = Table([[Paragraph(texto_simb_str, estilo_simbologia)]], colWidths=[978])
            tabla_simb.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F3F4F6')),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#D1D5DB')),
                ('TOPPADDING', (0,0), (-1,-1), 3),
                ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ]))
            elementos.append(tabla_simb)
            elementos.append(Spacer(1, 3))

            txt_notas = Paragraph(
                "• <b>Tolerancia:</b> 10 minutos en Entradas según CCT. Los minutos de retardo se muestran en línea (Ej. <b>08:24 (+14m)</b>).<br/>"
                f"<b>F01PGRRH02.01</b> — Página {num_pag} de {total_paginas}",
                estilo_notas
            )
            elementos.append(txt_notas)

            if num_pag < total_paginas:
                elementos.append(PageBreak())

        doc.build(elementos)
        return ruta_salida

    def _es_mismo_dia(self, fecha_db, dt_ref):
        if not fecha_db:
            return False
        try:
            f_str = str(fecha_db).strip().split(" ")[0]
            dt = datetime.strptime(f_str, "%Y-%m-%d")
            return dt.date() == dt_ref.date()
        except ValueError:
            return False

    def abrir_documento_generado(self, ruta_archivo):
        if sys.platform == "win32":
            os.startfile(ruta_archivo)
        elif sys.platform == "darwin":
            subprocess.call(["open", ruta_archivo])
        else:
            subprocess.call(["xdg-open", ruta_archivo])