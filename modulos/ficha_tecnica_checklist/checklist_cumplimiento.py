"""
Checklist de cumplimiento verificable punto por punto
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import json

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from modulos.utils.logger import Logger
from modulos.utils.config import Config


class ChecklistCumplimiento:
    """Genera checklist verificable de cumplimiento normativo"""
    
    def __init__(self, config: Optional[Config] = None, logger: Optional[Logger] = None):
        """
        Inicializa el generador de checklist
        
        Args:
            config: Instancia de Config
            logger: Instancia de Logger
        """
        if config is None:
            from modulos.utils.config import Config
            config = Config()
        if logger is None:
            from modulos.utils.logger import Logger
            logger = Logger(config)
        
        self.config = config
        self.logger = logger
        self.rutas = config.get_rutas()
    
    def generar(self, expediente: Dict[str, Any], cumplimiento: Dict[str, Any],
                formato: str = 'pdf') -> str:
        """
        Genera checklist de cumplimiento
        
        Args:
            expediente: Expediente completo
            cumplimiento: Resultado de evaluación de cumplimiento
            formato: Formato de salida ('pdf', 'html' o 'json')
            
        Returns:
            Ruta del archivo generado
        """
        self.logger.info(f"Generando checklist de cumplimiento en formato {formato}")
        
        checklist = self._construir_checklist(expediente, cumplimiento)
        
        if formato == 'pdf':
            return self._generar_pdf(checklist, expediente)
        elif formato == 'html':
            return self._generar_html(checklist, expediente)
        elif formato == 'json':
            return self._generar_json(checklist, expediente)
        else:
            raise ValueError(f"Formato no soportado: {formato}")
    
    def _construir_checklist(self, expediente: Dict[str, Any],
                            cumplimiento: Dict[str, Any]) -> Dict[str, Any]:
        """Construye estructura de checklist"""
        reclamo = expediente.get('reclamo', {})
        tipologia = expediente.get('clasificacion', {}).get('tipologia_principal', '')
        
        checklist = {
            'metadata': {
                'numero_reclamo': reclamo.get('numero_reclamo'),
                'fecha_generacion': datetime.now().isoformat(),
                'tipologia': tipologia
            },
            'items': []
        }
        
        # Item 1: Plazos
        plazos_info = cumplimiento.get('cumplimiento_plazos', {})
        checklist['items'].append({
            'categoria': 'Plazos',
            'item': 'Cumplimiento de plazo de resolución (30 días)',
            'cumple': plazos_info.get('cumple', False),
            'observaciones': plazos_info.get('razon', ''),
            'requisito': 'El reclamo debe resolverse dentro de 30 días hábiles según manual SEC',
            'evidencia_requerida': 'Fecha de ingreso y fecha de resolución'
        })
        
        # Item 2: Medios probatorios
        medios_info = cumplimiento.get('medios_probatorios', {})
        medios_requeridos = medios_info.get('medios_requeridos', [])
        medios_encontrados = medios_info.get('medios_encontrados', [])
        medios_faltantes = medios_info.get('medios_faltantes', [])
        
        checklist['items'].append({
            'categoria': 'Medios Probatorios',
            'item': 'Medios probatorios completos según tipología',
            'cumple': medios_info.get('completo', False),
            'observaciones': f"Presentes: {len(medios_encontrados)}/{len(medios_requeridos)}. Faltantes: {', '.join(medios_faltantes) if medios_faltantes else 'Ninguno'}",
            'requisito': f'Se requieren los siguientes medios probatorios para tipología {tipologia}',
            'evidencia_requerida': ', '.join(medios_requeridos),
            'detalle': {
                'medios_requeridos': medios_requeridos,
                'medios_encontrados': medios_encontrados,
                'medios_faltantes': medios_faltantes
            }
        })
        
        # Item 3: Consistencia de información
        consistencia_info = cumplimiento.get('consistencia_informacion', {})
        checklist['items'].append({
            'categoria': 'Consistencia de Información',
            'item': 'Consistencia entre boletas y análisis',
            'cumple': consistencia_info.get('consistente', False),
            'observaciones': ', '.join(consistencia_info.get('inconsistencias', [])) if not consistencia_info.get('consistente', True) else 'Información consistente',
            'requisito': 'Los datos de boletas deben ser consistentes con el análisis realizado',
            'evidencia_requerida': 'Boletas y análisis técnico'
        })
        
        # Item 4: Respuesta de primera instancia (si aplica)
        respuesta_info = cumplimiento.get('respuesta_primera_instancia', {})
        if not respuesta_info.get('es_analisis_automatico', False):
            elementos_requeridos = respuesta_info.get('elementos_requeridos', [])
            elementos_presentes = respuesta_info.get('elementos_presentes', [])
            elementos_faltantes = respuesta_info.get('elementos_faltantes', [])
            
            checklist['items'].append({
                'categoria': 'Respuesta de Primera Instancia',
                'item': 'Respuesta completa de la distribuidora',
                'cumple': respuesta_info.get('completa', False),
                'observaciones': f"Elementos presentes: {len(elementos_presentes)}/{len(elementos_requeridos)}. Faltantes: {', '.join(elementos_faltantes) if elementos_faltantes else 'Ninguno'}",
                'requisito': 'La respuesta debe incluir revisión del caso, conclusiones y recomendaciones',
                'evidencia_requerida': ', '.join(elementos_requeridos)
            })
        else:
            checklist['items'].append({
                'categoria': 'Respuesta de Primera Instancia',
                'item': 'Respuesta completa de la distribuidora',
                'cumple': False,
                'observaciones': 'No hay respuesta de empresa disponible. Este es un análisis automático.',
                'requisito': 'La respuesta debe incluir revisión del caso, conclusiones y recomendaciones',
                'evidencia_requerida': 'Carta respuesta de la distribuidora'
            })
        
        # Item 5: Cumplimiento general
        checklist['items'].append({
            'categoria': 'Cumplimiento General',
            'item': 'Cumplimiento normativo general',
            'cumple': cumplimiento.get('cumplimiento_general', False),
            'observaciones': '; '.join(cumplimiento.get('incumplimientos', [])) if not cumplimiento.get('cumplimiento_general', True) else 'Todos los requisitos cumplidos',
            'requisito': 'El expediente debe cumplir con todos los requisitos normativos',
            'evidencia_requerida': 'Expediente completo con todos los elementos requeridos'
        })
        
        return checklist
    
    def _generar_pdf(self, checklist: Dict[str, Any], expediente: Dict[str, Any]) -> str:
        """Genera checklist en formato PDF"""
        if not REPORTLAB_AVAILABLE:
            self.logger.warning("reportlab no disponible, generando solo texto")
            return self._generar_texto(checklist, expediente)
        
        reclamo = expediente.get('reclamo', {})
        numero_reclamo = reclamo.get('numero_reclamo', 'N/A')
        fecha_str = datetime.now().strftime('%Y%m%d')
        
        # Crear directorio si no existe
        dir_expedientes = Path(self.rutas.get('expedientes', 'data/expedientes'))
        dir_expedientes.mkdir(parents=True, exist_ok=True)
        
        nombre_archivo = f"CHECKLIST-{numero_reclamo}-{fecha_str}.pdf"
        ruta_archivo = dir_expedientes / nombre_archivo
        
        # Crear documento PDF
        doc = SimpleDocTemplate(str(ruta_archivo), pagesize=A4)
        story = []
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=20,
            alignment=1  # Centrado
        )
        
        # Título
        story.append(Paragraph("CHECKLIST DE CUMPLIMIENTO NORMATIVO", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Información del reclamo
        metadata = checklist.get('metadata', {})
        info_reclamo = [
            ['Número de Reclamo:', metadata.get('numero_reclamo', 'N/A')],
            ['Tipología:', metadata.get('tipologia', 'N/A')],
            ['Fecha:', datetime.now().strftime('%d/%m/%Y %H:%M')]
        ]
        
        tabla_info = Table(info_reclamo, colWidths=[2*inch, 4*inch])
        tabla_info.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(tabla_info)
        story.append(Spacer(1, 0.3*inch))
        
        # Items del checklist
        items = checklist.get('items', [])
        for i, item in enumerate(items, 1):
            categoria = item.get('categoria', '')
            descripcion = item.get('item', '')
            cumple = item.get('cumple', False)
            observaciones = item.get('observaciones', '')
            requisito = item.get('requisito', '')
            
            # Título del item
            story.append(Paragraph(f"<b>{i}. {categoria}: {descripcion}</b>", styles['Heading3']))
            story.append(Spacer(1, 0.1*inch))
            
            # Tabla con información del item
            datos_item = [
                ['Estado:', '✓ CUMPLE' if cumple else '✗ NO CUMPLE'],
                ['Requisito:', requisito],
                ['Observaciones:', observaciones]
            ]
            
            color_fondo = colors.lightgreen if cumple else colors.lightcoral
            tabla_item = Table(datos_item, colWidths=[1.5*inch, 4.5*inch])
            tabla_item.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('BACKGROUND', (1, 0), (1, 0), color_fondo),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP')
            ]))
            story.append(tabla_item)
            story.append(Spacer(1, 0.2*inch))
        
        # Resumen final
        items_cumplen = sum(1 for item in items if item.get('cumple', False))
        total_items = len(items)
        porcentaje = (items_cumplen / total_items * 100) if total_items > 0 else 0
        
        story.append(PageBreak())
        story.append(Paragraph("<b>RESUMEN</b>", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        datos_resumen = [
            ['Items que cumplen:', f"{items_cumplen}/{total_items}"],
            ['Porcentaje de cumplimiento:', f"{porcentaje:.1f}%"],
            ['Cumplimiento General:', 'SÍ' if items_cumplen == total_items else 'NO']
        ]
        
        tabla_resumen = Table(datos_resumen, colWidths=[3*inch, 3*inch])
        tabla_resumen.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(tabla_resumen)
        
        # Construir PDF
        doc.build(story)
        
        self.logger.info(f"Checklist PDF generado: {ruta_archivo}")
        return str(ruta_archivo)
    
    def _generar_html(self, checklist: Dict[str, Any], expediente: Dict[str, Any]) -> str:
        """Genera checklist en formato HTML"""
        # Cargar template HTML si existe
        template_path = Path(__file__).parent / 'templates' / 'checklist.html'
        
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                html_template = f.read()
        else:
            html_template = self._obtener_template_html_basico()
        
        # Formatear items
        items_html = self._formatear_items_html(checklist.get('items', []))
        
        # Reemplazar placeholders
        metadata = checklist.get('metadata', {})
        html = html_template.format(
            numero_reclamo=metadata.get('numero_reclamo', 'N/A'),
            fecha=datetime.now().strftime('%d/%m/%Y %H:%M'),
            tipologia=metadata.get('tipologia', 'N/A'),
            items=items_html,
            resumen=self._formatear_resumen_html(checklist)
        )
        
        # Guardar archivo
        reclamo = expediente.get('reclamo', {})
        numero_reclamo = reclamo.get('numero_reclamo', 'N/A')
        fecha_str = datetime.now().strftime('%Y%m%d')
        
        dir_expedientes = Path(self.rutas.get('expedientes', 'data/expedientes'))
        dir_expedientes.mkdir(parents=True, exist_ok=True)
        
        nombre_archivo = f"CHECKLIST-{numero_reclamo}-{fecha_str}.html"
        ruta_archivo = dir_expedientes / nombre_archivo
        
        with open(ruta_archivo, 'w', encoding='utf-8') as f:
            f.write(html)
        
        self.logger.info(f"Checklist HTML generado: {ruta_archivo}")
        return str(ruta_archivo)
    
    def _formatear_items_html(self, items: List[Dict[str, Any]]) -> str:
        """Formatea items para HTML"""
        html = ""
        for i, item in enumerate(items, 1):
            cumple = item.get('cumple', False)
            estado = '✓ CUMPLE' if cumple else '✗ NO CUMPLE'
            clase_estado = 'cumple' if cumple else 'no-cumple'
            
            html += f"""
            <div class="item-checklist">
                <h3>{i}. {item.get('categoria', '')}: {item.get('item', '')}</h3>
                <p class="estado {clase_estado}">{estado}</p>
                <p><strong>Requisito:</strong> {item.get('requisito', '')}</p>
                <p><strong>Observaciones:</strong> {item.get('observaciones', '')}</p>
            </div>
            """
        return html
    
    def _formatear_resumen_html(self, checklist: Dict[str, Any]) -> str:
        """Formatea resumen para HTML"""
        items = checklist.get('items', [])
        items_cumplen = sum(1 for item in items if item.get('cumple', False))
        total_items = len(items)
        porcentaje = (items_cumplen / total_items * 100) if total_items > 0 else 0
        
        return f"""
        <div class="resumen-checklist">
            <h3>RESUMEN</h3>
            <p><strong>Items que cumplen:</strong> {items_cumplen}/{total_items}</p>
            <p><strong>Porcentaje de cumplimiento:</strong> {porcentaje:.1f}%</p>
            <p><strong>Cumplimiento General:</strong> {'SÍ' if items_cumplen == total_items else 'NO'}</p>
        </div>
        """
    
    def _obtener_template_html_basico(self) -> str:
        """Retorna template HTML básico"""
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Checklist - {numero_reclamo}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #1a237e; }}
        h2 {{ color: #283593; }}
        .item-checklist {{ border: 1px solid #ddd; padding: 15px; margin: 10px 0; }}
        .estado {{ font-weight: bold; font-size: 14px; }}
        .cumple {{ color: green; }}
        .no-cumple {{ color: red; }}
        .resumen-checklist {{ background-color: #f5f5f5; padding: 15px; margin: 20px 0; }}
    </style>
</head>
<body>
    <h1>CHECKLIST DE CUMPLIMIENTO NORMATIVO</h1>
    <p><strong>Reclamo:</strong> {numero_reclamo}</p>
    <p><strong>Tipología:</strong> {tipologia}</p>
    <p><strong>Fecha:</strong> {fecha}</p>
    
    <h2>ITEMS DE VERIFICACIÓN</h2>
    {items}
    
    {resumen}
</body>
</html>"""
    
    def _generar_json(self, checklist: Dict[str, Any], expediente: Dict[str, Any]) -> str:
        """Genera checklist en formato JSON"""
        reclamo = expediente.get('reclamo', {})
        numero_reclamo = reclamo.get('numero_reclamo', 'N/A')
        fecha_str = datetime.now().strftime('%Y%m%d')
        
        dir_expedientes = Path(self.rutas.get('expedientes', 'data/expedientes'))
        dir_expedientes.mkdir(parents=True, exist_ok=True)
        
        nombre_archivo = f"CHECKLIST-{numero_reclamo}-{fecha_str}.json"
        ruta_archivo = dir_expedientes / nombre_archivo
        
        with open(ruta_archivo, 'w', encoding='utf-8') as f:
            json.dump(checklist, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Checklist JSON generado: {ruta_archivo}")
        return str(ruta_archivo)
    
    def _generar_texto(self, checklist: Dict[str, Any], expediente: Dict[str, Any]) -> str:
        """Genera checklist en formato texto"""
        texto = []
        texto.append("=" * 80)
        texto.append("CHECKLIST DE CUMPLIMIENTO NORMATIVO")
        texto.append("=" * 80)
        
        metadata = checklist.get('metadata', {})
        texto.append(f"\nReclamo: {metadata.get('numero_reclamo', 'N/A')}")
        texto.append(f"Tipología: {metadata.get('tipologia', 'N/A')}")
        texto.append(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        texto.append("\n" + "-" * 80)
        
        items = checklist.get('items', [])
        for i, item in enumerate(items, 1):
            texto.append(f"\n{i}. {item.get('categoria', '')}: {item.get('item', '')}")
            texto.append(f"   Estado: {'✓ CUMPLE' if item.get('cumple', False) else '✗ NO CUMPLE'}")
            texto.append(f"   Requisito: {item.get('requisito', '')}")
            texto.append(f"   Observaciones: {item.get('observaciones', '')}")
            texto.append("")
        
        # Resumen
        items_cumplen = sum(1 for item in items if item.get('cumple', False))
        total_items = len(items)
        porcentaje = (items_cumplen / total_items * 100) if total_items > 0 else 0
        
        texto.append("-" * 80)
        texto.append("RESUMEN")
        texto.append("-" * 80)
        texto.append(f"Items que cumplen: {items_cumplen}/{total_items}")
        texto.append(f"Porcentaje de cumplimiento: {porcentaje:.1f}%")
        texto.append(f"Cumplimiento General: {'SÍ' if items_cumplen == total_items else 'NO'}")
        texto.append("=" * 80)
        
        # Guardar archivo
        reclamo = expediente.get('reclamo', {})
        numero_reclamo = reclamo.get('numero_reclamo', 'N/A')
        fecha_str = datetime.now().strftime('%Y%m%d')
        
        dir_expedientes = Path(self.rutas.get('expedientes', 'data/expedientes'))
        dir_expedientes.mkdir(parents=True, exist_ok=True)
        
        nombre_archivo = f"CHECKLIST-{numero_reclamo}-{fecha_str}.txt"
        ruta_archivo = dir_expedientes / nombre_archivo
        
        with open(ruta_archivo, 'w', encoding='utf-8') as f:
            f.write('\n'.join(texto))
        
        self.logger.info(f"Checklist TXT generado: {ruta_archivo}")
        return str(ruta_archivo)

