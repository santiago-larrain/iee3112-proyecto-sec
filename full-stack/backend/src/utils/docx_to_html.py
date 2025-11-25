"""
Utilidad para convertir DOCX a HTML para previsualización completa y robusta
Procesa todos los elementos del documento en el orden correcto
"""

from pathlib import Path
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from typing import Optional
import html

def docx_to_html(file_path: Path) -> Optional[str]:
    """
    Convierte un archivo DOCX a HTML para previsualización completa
    Procesa todos los elementos (párrafos, tablas) en el orden correcto
    
    Args:
        file_path: Ruta al archivo DOCX
        
    Returns:
        HTML completo como string o None si hay error
    """
    try:
        doc = Document(file_path)
        
        # HTML completo con estilos embebidos
        html_parts = ['''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vista Previa DOCX</title>
    <style>
        body {
            font-family: 'Times New Roman', Times, serif;
            max-width: 8.5in;
            margin: 0 auto;
            padding: 1in;
            line-height: 1.6;
            color: #000;
            background: #fff;
        }
        .docx-preview {
            background: white;
            min-height: 100vh;
        }
        h1 { font-size: 24pt; margin-top: 12pt; margin-bottom: 6pt; font-weight: bold; }
        h2 { font-size: 18pt; margin-top: 10pt; margin-bottom: 5pt; font-weight: bold; }
        h3 { font-size: 14pt; margin-top: 8pt; margin-bottom: 4pt; font-weight: bold; }
        h4 { font-size: 12pt; margin-top: 6pt; margin-bottom: 3pt; font-weight: bold; }
        h5 { font-size: 11pt; margin-top: 5pt; margin-bottom: 2pt; font-weight: bold; }
        h6 { font-size: 10pt; margin-top: 4pt; margin-bottom: 2pt; font-weight: bold; }
        p {
            margin: 6pt 0;
            text-align: justify;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 12pt 0;
            border: 1px solid #000;
        }
        td, th {
            border: 1px solid #000;
            padding: 4pt 8pt;
            text-align: left;
        }
        th {
            background-color: #f0f0f0;
            font-weight: bold;
        }
        strong { font-weight: bold; }
        em { font-style: italic; }
        u { text-decoration: underline; }
        .page-break {
            page-break-after: always;
            border-top: 2px dashed #ccc;
            margin: 20pt 0;
            padding-top: 20pt;
        }
    </style>
</head>
<body>
    <div class="docx-preview">''']
        
        # Procesar elementos en el orden correcto usando el body del documento
        # Esto asegura que párrafos y tablas se procesen en el orden en que aparecen
        body = doc.element.body
        
        # Iterar sobre todos los elementos del body en orden
        for element in body.iterchildren():
            # Detectar tipo de elemento por su tag XML
            tag = element.tag
            
            # Párrafo: w:p
            if '}p' in tag or tag.endswith('p'):
                try:
                    paragraph = Paragraph(element, doc)
                    _process_paragraph(paragraph, html_parts)
                except Exception as e:
                    print(f"Error procesando párrafo: {e}")
                    continue
            
            # Tabla: w:tbl
            elif '}tbl' in tag or tag.endswith('tbl'):
                try:
                    table = Table(element, doc)
                    _process_table(table, html_parts)
                except Exception as e:
                    print(f"Error procesando tabla: {e}")
                    continue
        
        html_parts.append('''    </div>
</body>
</html>''')
        return ''.join(html_parts)
        
    except Exception as e:
        print(f"Error convirtiendo DOCX a HTML: {e}")
        import traceback
        traceback.print_exc()
        return None


def _process_paragraph(paragraph: Paragraph, html_parts: list):
    """Procesa un párrafo y lo agrega al HTML"""
    text = paragraph.text.strip()
    
    # Si el párrafo tiene texto o tiene runs (puede tener solo formato)
    if text or paragraph.runs:
        # Detectar estilos básicos
        style = "normal"
        style_name = paragraph.style.name if paragraph.style else ""
        
        if style_name.startswith('Heading'):
            level = style_name.replace('Heading ', '')
            try:
                level_num = int(level)
                style = f"h{min(level_num, 6)}"
            except:
                style = "h2"
        elif style_name.startswith('Title'):
            style = "h1"
        elif style_name.startswith('Subtitle'):
            style = "h2"
        
        # Extraer formato del texto con formato inline
        text_content = ""
        for run in paragraph.runs:
            run_text = html.escape(run.text)
            if run.bold:
                run_text = f"<strong>{run_text}</strong>"
            if run.italic:
                run_text = f"<em>{run_text}</em>"
            if run.underline:
                run_text = f"<u>{run_text}</u>"
            text_content += run_text
        
        # Si no hay contenido pero hay runs, puede ser un espacio
        if not text_content.strip() and paragraph.runs:
            text_content = "&nbsp;"
        
        if text_content:
            if style.startswith('h'):
                html_parts.append(f"<{style}>{text_content}</{style}>")
            else:
                html_parts.append(f"<p>{text_content}</p>")
    else:
        # Párrafo completamente vacío - agregar espacio
        html_parts.append("<p>&nbsp;</p>")


def _process_table(table: Table, html_parts: list):
    """Procesa una tabla y la agrega al HTML"""
    html_parts.append('<table>')
    
    # Procesar todas las filas
    for row_idx, row in enumerate(table.rows):
        html_parts.append('<tr>')
        
        for cell in row.cells:
            # Procesar contenido de la celda (puede tener múltiples párrafos)
            cell_content = []
            for paragraph in cell.paragraphs:
                para_text = ""
                for run in paragraph.runs:
                    run_text = html.escape(run.text)
                    if run.bold:
                        run_text = f"<strong>{run_text}</strong>"
                    if run.italic:
                        run_text = f"<em>{run_text}</em>"
                    if run.underline:
                        run_text = f"<u>{run_text}</u>"
                    para_text += run_text
                
                if para_text.strip():
                    cell_content.append(para_text)
                elif paragraph.runs:
                    cell_content.append("&nbsp;")
            
            # Si la celda está vacía, agregar espacio
            cell_text = "<br>".join(cell_content) if cell_content else "&nbsp;"
            
            # Primera fila como encabezado
            tag = 'th' if row_idx == 0 else 'td'
            html_parts.append(f'<{tag}>{cell_text}</{tag}>')
        
        html_parts.append('</tr>')
    
    html_parts.append('</table>')
