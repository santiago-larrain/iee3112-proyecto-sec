"""
Utilidad para generar PDF de resolución con template
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pathlib import Path
from typing import Optional
from datetime import datetime
import re

def generate_resolucion_pdf(resolucion_content: str, case_id: str, output_path: Path, 
                           client_name: str = "N/A", rut_client: str = "N/A", 
                           empresa: str = "N/A", materia: str = "N/A") -> bool:
    """
    Genera un PDF de resolución con template formal
    
    Args:
        resolucion_content: Contenido de la resolución
        case_id: ID del caso
        output_path: Ruta donde guardar el PDF
        client_name: Nombre del cliente
        rut_client: RUT del cliente
        empresa: Nombre de la empresa
        materia: Materia del caso
        
    Returns:
        True si se generó correctamente, False en caso contrario
    """
    try:
        # Crear documento PDF
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        
        # Estilo para título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor='#000000',
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        # Estilo para encabezado
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Normal'],
            fontSize=10,
            textColor='#666666',
            alignment=TA_LEFT,
            spaceAfter=12
        )
        
        # Estilo para cuerpo
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            textColor='#000000',
            alignment=TA_JUSTIFY,
            spaceAfter=12,
            leading=14
        )
        
        # Construir contenido
        story = []
        
        # Encabezado con logo placeholder
        header_text = f"""
        <b>SUPERINTENDENCIA DE ELECTRICIDAD Y COMBUSTIBLES</b><br/>
        <b>SUPERINTENDENCIA REGIONAL</b><br/>
        <i>Casilla {case_id}</i>
        """
        story.append(Paragraph(header_text, header_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Fecha
        fecha_actual = datetime.now().strftime("%d de %B de %Y").replace("January", "enero").replace("February", "febrero").replace("March", "marzo").replace("April", "abril").replace("May", "mayo").replace("June", "junio").replace("July", "julio").replace("August", "agosto").replace("September", "septiembre").replace("October", "octubre").replace("November", "noviembre").replace("December", "diciembre")
        fecha_text = f"<b>Fecha:</b> {fecha_actual}"
        story.append(Paragraph(fecha_text, header_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Información del caso
        caso_text = f"""
        <b>Caso SEC:</b> {case_id}<br/>
        <b>Cliente:</b> {client_name}<br/>
        <b>RUT:</b> {rut_client}<br/>
        <b>Empresa:</b> {empresa}<br/>
        <b>Materia:</b> {materia}
        """
        story.append(Paragraph(caso_text, header_style))
        story.append(Spacer(1, 0.4*inch))
        
        # Título de la resolución
        # Detectar tipo de resolución del contenido
        if "INSTRUCCIÓN" in resolucion_content.upper():
            titulo = "INSTRUCCIÓN A LA EMPRESA"
        elif "IMPROCEDENTE" in resolucion_content.upper():
            titulo = "RESOLUCIÓN IMPROCEDENTE"
        else:
            titulo = "RESOLUCIÓN"
        
        story.append(Paragraph(titulo, title_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Procesar contenido de la resolución
        # Dividir en párrafos y secciones
        lines = resolucion_content.split('\n')
        current_paragraph = []
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_paragraph:
                    para_text = ' '.join(current_paragraph)
                    # Escapar HTML y convertir saltos de línea
                    para_text = para_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    story.append(Paragraph(para_text, body_style))
                    story.append(Spacer(1, 0.15*inch))
                    current_paragraph = []
                continue
            
            # Detectar títulos/secciones (líneas en mayúsculas o que terminan en :)
            if line.isupper() or (line.endswith(':') and len(line) < 100):
                if current_paragraph:
                    para_text = ' '.join(current_paragraph)
                    para_text = para_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    story.append(Paragraph(para_text, body_style))
                    story.append(Spacer(1, 0.15*inch))
                    current_paragraph = []
                
                # Título de sección
                section_style = ParagraphStyle(
                    'SectionTitle',
                    parent=styles['Heading2'],
                    fontSize=12,
                    textColor='#000000',
                    spaceAfter=12,
                    spaceBefore=12,
                    fontName='Helvetica-Bold'
                )
                line_escaped = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(line_escaped, section_style))
            else:
                current_paragraph.append(line)
        
        # Agregar último párrafo si existe
        if current_paragraph:
            para_text = ' '.join(current_paragraph)
            para_text = para_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(para_text, body_style))
        
        # Pie de página con firma
        story.append(Spacer(1, 0.5*inch))
        firma_text = """
        <br/><br/>
        _________________________<br/>
        <b>FUNCIONARIO SEC</b><br/>
        <i>Superintendencia de Electricidad y Combustibles</i>
        """
        story.append(Paragraph(firma_text, body_style))
        
        # Construir PDF
        doc.build(story)
        return True
        
    except Exception as e:
        print(f"Error generando PDF de resolución: {e}")
        import traceback
        traceback.print_exc()
        return False

