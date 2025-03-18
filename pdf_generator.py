import os
import io
import base64
from datetime import datetime
from fpdf import FPDF
import streamlit as st
import pandas as pd
import utils

class ActivityReport(FPDF):
    """Clase para generar reportes PDF de actividades"""
    
    def __init__(self, orientation='P', unit='mm', format='A4'):
        super().__init__(orientation=orientation, unit=unit, format=format)
        self.set_auto_page_break(auto=True, margin=15)
        
    def header(self):
        # Logo de la Policía Local de Vigo (podría ser un croissant como placeholder)
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, '🥐 Policía Local de Vigo', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 6, 'Informe de Actividad', 0, 1, 'C')
        self.ln(4)
        
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')
        self.cell(0, 10, f'Generado el {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 0, 'R')
        
    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 7, title, 0, 1, 'L', True)
        self.ln(4)
        
    def chapter_body(self, body, is_list=False):
        if not is_list:
            self.set_font('Arial', '', 11)
            self.multi_cell(0, 5, body)
            self.ln()
        else:
            # Para listas, recibimos una lista de tuplas (texto, negrita)
            self.set_font('Arial', '', 11)
            for item, bold in body:
                font_style = 'B' if bold else ''
                self.set_font('Arial', font_style, 11)
                self.cell(0, 6, item, 0, 1)
            self.ln(2)
            
    def add_participant_table(self, participants):
        self.set_font('Arial', 'B', 11)
        
        # Calcular ancho de columnas y encabezados
        col_width = 45  # Ancho de las columnas
        self.cell(10, 7, '#', 1, 0, 'C')
        self.cell(col_width, 7, 'NIP', 1, 0, 'C')
        self.cell(col_width*2, 7, 'Nombre', 1, 0, 'C')
        self.cell(col_width, 7, 'Sección', 1, 1, 'C')
        
        # Añadir datos de participantes
        self.set_font('Arial', '', 10)
        for i, participant in enumerate(participants, 1):
            self.cell(10, 6, str(i), 1, 0, 'C')
            self.cell(col_width, 6, str(participant.get('nip', '')), 1, 0, 'L')
            self.cell(col_width*2, 6, participant.get('nombre', ''), 1, 0, 'L')
            self.cell(col_width, 6, participant.get('seccion', ''), 1, 1, 'L')
        self.ln(4)

def generate_activity_report(activity_id):
    """
    Genera un reporte PDF para una actividad específica
    
    Args:
        activity_id: ID de la actividad
    
    Returns:
        bytes: PDF generado en memoria
    """
    try:
        # Obtener datos de la actividad de Supabase
        activity_data = utils.get_activity_details(activity_id)
        if not activity_data:
            return None
            
        course_name = utils.get_course_name(activity_data.get('curso_id', '')) or "Sin curso asignado"
        monitor_name = utils.get_agent_name(activity_data.get('monitor_nip', '')) or "Sin monitor asignado"
        fecha = utils.format_date(activity_data.get('fecha', ''))
        turno = activity_data.get('turno', '')
        comentarios = activity_data.get('comentarios', '') or "Sin comentarios"
        
        # Obtener participantes
        participants = utils.get_activity_participants(activity_id)
        
        # Crear PDF
        pdf = ActivityReport()
        pdf.add_page()
        
        # Título y detalles
        pdf.chapter_title(f"Actividad: {course_name}")
        
        # Información de la actividad
        activity_info = [
            (f"Fecha: {fecha}", True),
            (f"Turno: {turno}", True),
            (f"Monitor: {monitor_name}", True),
            (f"Curso: {course_name}", True),
        ]
        pdf.chapter_body(activity_info, is_list=True)
        
        # Comentarios
        pdf.chapter_title("Comentarios")
        pdf.chapter_body(comentarios)
        
        # Tabla de participantes
        pdf.chapter_title(f"Participantes ({len(participants)})")
        if participants:
            pdf.add_participant_table(participants)
        else:
            pdf.chapter_body("No hay participantes registrados en esta actividad.")
            
        # Firma
        pdf.ln(20)
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 10, "Firma del monitor:", 0, 1, 'L')
        pdf.line(20, pdf.get_y() + 15, 80, pdf.get_y() + 15)
        
        # Devolver PDF en memoria
        return pdf.output(dest='S')
    
    except Exception as e:
        st.error(f"Error al generar el PDF: {str(e)}")
        return None

def get_pdf_download_link(pdf_bytes, filename="reporte_actividad.pdf", text="Descargar Reporte PDF"):
    """
    Crea un enlace de descarga para un PDF generado
    
    Args:
        pdf_bytes: Bytes del PDF generado
        filename: Nombre del archivo
        text: Texto del enlace
    
    Returns:
        str: HTML con el enlace de descarga
    """
    if pdf_bytes:
        b64 = base64.b64encode(pdf_bytes).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}"><button style="color: white; background-color: #0066cc; padding: 0.5rem 1rem; border: none; border-radius: 4px; margin-top: 1rem; cursor: pointer;">{text}</button></a>'
        return href
    return None