"""
Generador de Ficha Técnica completa en PDF y HTML
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import json
import base64
from io import BytesIO

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    import matplotlib
    matplotlib.use('Agg')  # Backend sin GUI
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from modulos.utils.logger import Logger
from modulos.utils.config import Config
from modulos.ficha_tecnica_checklist.generador_informe import GeneradorInforme
from modulos.ficha_tecnica_checklist.generador_instrucciones import GeneradorInstrucciones


class GeneradorFicha:
    """Genera ficha técnica completa en PDF y HTML"""
    
    def __init__(self, config: Optional[Config] = None, logger: Optional[Logger] = None):
        """
        Inicializa el generador de ficha técnica
        
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
        self.generador_informe = GeneradorInforme(config, logger)
        self.generador_instrucciones = GeneradorInstrucciones(config, logger)
    
    def generar(self, expediente: Dict[str, Any], analisis: Dict[str, Any],
                cumplimiento: Dict[str, Any], formato: str = 'pdf') -> str:
        """
        Genera ficha técnica completa
        
        Args:
            expediente: Expediente completo
            analisis: Resultado del análisis
            cumplimiento: Resultado de evaluación de cumplimiento
            formato: Formato de salida ('pdf' o 'html')
            
        Returns:
            Ruta del archivo generado
        """
        self.logger.info(f"Generando ficha técnica en formato {formato}")
        
        # Generar informe e instrucciones
        informe = self.generador_informe.generar(expediente, analisis, cumplimiento)
        instrucciones = self.generador_instrucciones.generar(expediente, analisis, cumplimiento)
        
        if formato == 'pdf':
            return self._generar_pdf(expediente, analisis, cumplimiento, informe, instrucciones)
        elif formato == 'html':
            return self._generar_html(expediente, analisis, cumplimiento, informe, instrucciones)
        else:
            raise ValueError(f"Formato no soportado: {formato}")
    
    def _generar_pdf(self, expediente: Dict[str, Any], analisis: Dict[str, Any],
                    cumplimiento: Dict[str, Any], informe: Dict[str, Any],
                    instrucciones: Dict[str, Any]) -> str:
        """Genera ficha técnica en formato PDF"""
        if not REPORTLAB_AVAILABLE:
            self.logger.warning("reportlab no disponible, generando solo texto")
            return self._generar_texto(expediente, analisis, cumplimiento, informe, instrucciones)
        
        reclamo = expediente.get('reclamo', {})
        numero_reclamo = reclamo.get('numero_reclamo', 'N/A')
        fecha_str = datetime.now().strftime('%Y%m%d')
        
        # Crear directorio si no existe
        dir_expedientes = Path(self.rutas.get('expedientes', 'data/expedientes'))
        dir_expedientes.mkdir(parents=True, exist_ok=True)
        
        nombre_archivo = f"FICHA-{numero_reclamo}-{fecha_str}.pdf"
        ruta_archivo = dir_expedientes / nombre_archivo
        
        # Crear documento PDF
        doc = SimpleDocTemplate(str(ruta_archivo), pagesize=A4)
        story = []
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#283593'),
            spaceAfter=12,
            spaceBefore=20
        )
        
        # Título
        story.append(Paragraph("FICHA TÉCNICA - ANÁLISIS DE RECLAMO", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Resumen ejecutivo
        story.append(Paragraph("RESUMEN EJECUTIVO", heading_style))
        story.extend(self._generar_seccion_resumen_pdf(expediente, informe, styles))
        story.append(Spacer(1, 0.2*inch))
        
        # Análisis técnico
        story.append(PageBreak())
        story.append(Paragraph("ANÁLISIS TÉCNICO DETALLADO", heading_style))
        story.extend(self._generar_seccion_analisis_pdf(expediente, analisis, styles))
        story.append(Spacer(1, 0.2*inch))
        
        # Gráfico de consumo (si hay boletas)
        boletas = expediente.get('boletas', [])
        if boletas and MATPLOTLIB_AVAILABLE:
            try:
                grafico_path = self._generar_grafico_consumo(boletas, numero_reclamo)
                if grafico_path:
                    img = Image(grafico_path, width=6*inch, height=4*inch)
                    story.append(img)
                    story.append(Spacer(1, 0.2*inch))
            except Exception as e:
                self.logger.warning(f"No se pudo generar gráfico: {e}")
        
        # Evaluación de cumplimiento
        story.append(PageBreak())
        story.append(Paragraph("EVALUACIÓN DE CUMPLIMIENTO", heading_style))
        story.extend(self._generar_seccion_cumplimiento_pdf(cumplimiento, styles))
        story.append(Spacer(1, 0.2*inch))
        
        # Instrucciones
        story.append(PageBreak())
        story.append(Paragraph("INSTRUCCIONES PARA FUNCIONARIO", heading_style))
        story.extend(self._generar_seccion_instrucciones_pdf(instrucciones, styles))
        story.append(Spacer(1, 0.2*inch))
        
        # Recomendaciones
        story.append(PageBreak())
        story.append(Paragraph("RECOMENDACIONES Y CONCLUSIONES", heading_style))
        story.extend(self._generar_seccion_recomendaciones_pdf(informe, styles))
        
        # Construir PDF
        doc.build(story)
        
        self.logger.info(f"Ficha técnica PDF generada: {ruta_archivo}")
        return str(ruta_archivo)
    
    def _generar_seccion_resumen_pdf(self, expediente: Dict[str, Any],
                                     informe: Dict[str, Any], styles) -> List:
        """Genera sección de resumen para PDF"""
        story = []
        resumen = informe.get('resumen_ejecutivo', {})
        
        datos = [
            ['Número de Reclamo:', resumen.get('numero_reclamo', 'N/A')],
            ['Cliente:', resumen.get('cliente', 'N/A')],
            ['Distribuidora:', resumen.get('distribuidora', 'N/A')],
            ['Tipología:', resumen.get('tipologia', 'N/A')],
            ['Conclusión:', resumen.get('conclusion_principal', 'N/A')],
            ['Estado Cumplimiento:', resumen.get('estado_cumplimiento', 'N/A')]
        ]
        
        tabla = Table(datos, colWidths=[2*inch, 4*inch])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(tabla)
        return story
    
    def _generar_seccion_analisis_pdf(self, expediente: Dict[str, Any],
                                      analisis: Dict[str, Any], styles) -> List:
        """Genera sección de análisis para PDF"""
        story = []
        
        explicacion = analisis.get('explicacion_analisis', {})
        if not explicacion:
            # Generar explicación desde el informe
            from modulos.ficha_tecnica_checklist.generador_informe import GeneradorInforme
            generador = GeneradorInforme(self.config, self.logger)
            informe_completo = generador.generar(expediente, analisis, {})
            explicacion = informe_completo.get('explicacion_analisis', {})
        
        story.append(Paragraph(f"<b>Procedimiento Aplicado:</b> {analisis.get('procedimiento_aplicado', 'N/A')}", styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
        
        # Análisis de consumo si aplica
        analisis_consumo = analisis.get('analisis_consumo', {})
        if analisis_consumo:
            story.append(Paragraph("<b>Análisis de Consumo:</b>", styles['Normal']))
            datos_consumo = [
                ['Período Reclamado:', analisis_consumo.get('periodo_reclamado', 'N/A')],
                ['Consumo Reclamado:', f"{analisis_consumo.get('consumo_reclamado', 0):.2f} kWh"],
                ['Período Espejo:', analisis_consumo.get('periodo_espejo', 'N/A')],
                ['Consumo Espejo:', f"{analisis_consumo.get('consumo_espejo', 0):.2f} kWh"],
                ['Supera 2x Período Espejo:', 'Sí' if analisis_consumo.get('supera_2x_periodo_espejo') else 'No'],
                ['Factor:', f"{analisis_consumo.get('factor', 1.0):.2f}x"]
            ]
            
            tabla_consumo = Table(datos_consumo, colWidths=[2.5*inch, 3.5*inch])
            tabla_consumo.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            story.append(tabla_consumo)
            story.append(Spacer(1, 0.1*inch))
        
        # Causa raíz
        causa_raiz = analisis.get('causa_raiz', {})
        if causa_raiz:
            story.append(Paragraph(f"<b>Causa Raíz:</b> {causa_raiz.get('tipo', 'N/A')}", styles['Normal']))
            pasos = causa_raiz.get('pasos_sugeridos', [])
            if pasos:
                story.append(Paragraph("<b>Pasos Sugeridos:</b>", styles['Normal']))
                for paso in pasos:
                    story.append(Paragraph(f"• {paso}", styles['Normal']))
        
        return story
    
    def _generar_seccion_cumplimiento_pdf(self, cumplimiento: Dict[str, Any],
                                          styles) -> List:
        """Genera sección de cumplimiento para PDF"""
        story = []
        
        cumplimiento_general = cumplimiento.get('cumplimiento_general', False)
        story.append(Paragraph(f"<b>Cumplimiento General:</b> {'Sí' if cumplimiento_general else 'No'}", styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
        
        # Plazos
        plazos = cumplimiento.get('cumplimiento_plazos', {})
        cumple_plazos = plazos.get('cumple', False)
        story.append(Paragraph(f"<b>Plazos:</b> {'Cumple' if cumple_plazos else 'No cumple'}", styles['Normal']))
        if not cumple_plazos:
            story.append(Paragraph(f"Razón: {plazos.get('razon', 'N/A')}", styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
        
        # Medios probatorios
        medios = cumplimiento.get('medios_probatorios', {})
        completo = medios.get('completo', False)
        story.append(Paragraph(f"<b>Medios Probatorios:</b> {'Completo' if completo else 'Incompleto'}", styles['Normal']))
        if not completo:
            faltantes = medios.get('medios_faltantes', [])
            story.append(Paragraph(f"Faltantes: {', '.join(faltantes)}", styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
        
        # Incumplimientos
        incumplimientos = cumplimiento.get('incumplimientos', [])
        if incumplimientos:
            story.append(Paragraph("<b>Incumplimientos Detectados:</b>", styles['Normal']))
            for inc in incumplimientos:
                story.append(Paragraph(f"• {inc}", styles['Normal']))
        
        return story
    
    def _generar_seccion_instrucciones_pdf(self, instrucciones: Dict[str, Any],
                                           styles) -> List:
        """Genera sección de instrucciones para PDF"""
        story = []
        
        acciones = instrucciones.get('acciones_inmediatas', [])
        if acciones:
            story.append(Paragraph("<b>Acciones Inmediatas:</b>", styles['Normal']))
            for accion in acciones:
                prioridad = accion.get('prioridad', 'normal').upper()
                story.append(Paragraph(f"[{prioridad}] {accion.get('accion', '')}", styles['Normal']))
                story.append(Paragraph(f"  {accion.get('detalle', '')}", styles['Normal']))
                story.append(Spacer(1, 0.05*inch))
        
        pasos = instrucciones.get('pasos_siguientes', [])
        if pasos:
            story.append(Paragraph("<b>Pasos Siguientes:</b>", styles['Normal']))
            for i, paso in enumerate(pasos, 1):
                story.append(Paragraph(f"{i}. {paso}", styles['Normal']))
        
        return story
    
    def _generar_seccion_recomendaciones_pdf(self, informe: Dict[str, Any],
                                             styles) -> List:
        """Genera sección de recomendaciones para PDF"""
        story = []
        
        recomendaciones = informe.get('recomendaciones', [])
        if recomendaciones:
            for rec in recomendaciones:
                prioridad = rec.get('prioridad', 'normal').upper()
                story.append(Paragraph(f"[{prioridad}] {rec.get('recomendacion', '')}", styles['Normal']))
                story.append(Paragraph(f"  {rec.get('detalle', '')}", styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
        
        conclusiones = informe.get('conclusiones', {})
        if conclusiones:
            story.append(Paragraph("<b>Conclusión Principal:</b>", styles['Normal']))
            story.append(Paragraph(conclusiones.get('conclusion_principal', 'N/A'), styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph("<b>Siguiente Paso:</b>", styles['Normal']))
            story.append(Paragraph(conclusiones.get('siguiente_paso', 'N/A'), styles['Normal']))
        
        return story
    
    def _generar_grafico_consumo(self, boletas: List[Dict[str, Any]],
                                 numero_reclamo: str) -> Optional[str]:
        """Genera gráfico de consumo histórico"""
        if not MATPLOTLIB_AVAILABLE or not boletas:
            return None
        
        try:
            # Ordenar boletas por período
            boletas_ordenadas = sorted(boletas, key=lambda x: x.get('periodo_facturacion', ''))
            
            periodos = [b.get('periodo_facturacion', '') for b in boletas_ordenadas]
            consumos = [b.get('consumo_kwh', 0) for b in boletas_ordenadas]
            
            # Crear gráfico
            plt.figure(figsize=(10, 6))
            plt.plot(periodos, consumos, marker='o', linewidth=2, markersize=8)
            plt.title(f'Historial de Consumo - Reclamo {numero_reclamo}', fontsize=14, fontweight='bold')
            plt.xlabel('Período de Facturación', fontsize=12)
            plt.ylabel('Consumo (kWh)', fontsize=12)
            plt.xticks(rotation=45, ha='right')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            # Guardar temporalmente
            dir_temp = Path(self.rutas.get('expedientes', 'data/expedientes'))
            dir_temp.mkdir(parents=True, exist_ok=True)
            ruta_grafico = dir_temp / f"grafico_{numero_reclamo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(ruta_grafico, dpi=150, bbox_inches='tight')
            plt.close()
            
            return str(ruta_grafico)
        except Exception as e:
            self.logger.error(f"Error al generar gráfico: {e}")
            return None
    
    def _generar_html(self, expediente: Dict[str, Any], analisis: Dict[str, Any],
                     cumplimiento: Dict[str, Any], informe: Dict[str, Any],
                     instrucciones: Dict[str, Any]) -> str:
        """Genera ficha técnica en formato HTML"""
        # Cargar template HTML si existe
        template_path = Path(__file__).parent / 'templates' / 'ficha_tecnica.html'
        
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                html_template = f.read()
        else:
            # Template básico si no existe
            html_template = self._obtener_template_html_basico()
        
        # Reemplazar placeholders
        html = html_template.format(
            numero_reclamo=expediente.get('reclamo', {}).get('numero_reclamo', 'N/A'),
            fecha=datetime.now().strftime('%d/%m/%Y %H:%M'),
            resumen=self._formatear_resumen_html(informe),
            analisis=self._formatear_analisis_html(expediente, analisis),
            cumplimiento=self._formatear_cumplimiento_html(cumplimiento),
            instrucciones=self._formatear_instrucciones_html(instrucciones),
            recomendaciones=self._formatear_recomendaciones_html(informe)
        )
        
        # Guardar archivo
        reclamo = expediente.get('reclamo', {})
        numero_reclamo = reclamo.get('numero_reclamo', 'N/A')
        fecha_str = datetime.now().strftime('%Y%m%d')
        
        dir_expedientes = Path(self.rutas.get('expedientes', 'data/expedientes'))
        dir_expedientes.mkdir(parents=True, exist_ok=True)
        
        nombre_archivo = f"FICHA-{numero_reclamo}-{fecha_str}.html"
        ruta_archivo = dir_expedientes / nombre_archivo
        
        with open(ruta_archivo, 'w', encoding='utf-8') as f:
            f.write(html)
        
        self.logger.info(f"Ficha técnica HTML generada: {ruta_archivo}")
        return str(ruta_archivo)
    
    def _obtener_template_html_basico(self) -> str:
        """Retorna template HTML básico"""
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Ficha Técnica - {numero_reclamo}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #1a237e; }}
        h2 {{ color: #283593; border-bottom: 2px solid #283593; padding-bottom: 5px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #283593; color: white; }}
        .resumen {{ background-color: #f5f5f5; padding: 15px; margin: 10px 0; }}
    </style>
</head>
<body>
    <h1>FICHA TÉCNICA - ANÁLISIS DE RECLAMO</h1>
    <p><strong>Reclamo:</strong> {numero_reclamo}</p>
    <p><strong>Fecha:</strong> {fecha}</p>
    
    <h2>RESUMEN EJECUTIVO</h2>
    {resumen}
    
    <h2>ANÁLISIS TÉCNICO</h2>
    {analisis}
    
    <h2>EVALUACIÓN DE CUMPLIMIENTO</h2>
    {cumplimiento}
    
    <h2>INSTRUCCIONES</h2>
    {instrucciones}
    
    <h2>RECOMENDACIONES</h2>
    {recomendaciones}
</body>
</html>"""
    
    def _formatear_resumen_html(self, informe: Dict[str, Any]) -> str:
        """Formatea resumen para HTML"""
        resumen = informe.get('resumen_ejecutivo', {})
        return f"""
        <div class="resumen">
            <p><strong>Cliente:</strong> {resumen.get('cliente', 'N/A')}</p>
            <p><strong>Distribuidora:</strong> {resumen.get('distribuidora', 'N/A')}</p>
            <p><strong>Tipología:</strong> {resumen.get('tipologia', 'N/A')}</p>
            <p><strong>Conclusión:</strong> {resumen.get('conclusion_principal', 'N/A')}</p>
            <p><strong>Estado Cumplimiento:</strong> {resumen.get('estado_cumplimiento', 'N/A')}</p>
        </div>
        """
    
    def _formatear_analisis_html(self, expediente: Dict[str, Any],
                                 analisis: Dict[str, Any]) -> str:
        """Formatea análisis para HTML"""
        analisis_consumo = analisis.get('analisis_consumo', {})
        if analisis_consumo:
            return f"""
            <table>
                <tr><th>Concepto</th><th>Valor</th></tr>
                <tr><td>Período Reclamado</td><td>{analisis_consumo.get('periodo_reclamado', 'N/A')}</td></tr>
                <tr><td>Consumo Reclamado</td><td>{analisis_consumo.get('consumo_reclamado', 0):.2f} kWh</td></tr>
                <tr><td>Período Espejo</td><td>{analisis_consumo.get('periodo_espejo', 'N/A')}</td></tr>
                <tr><td>Consumo Espejo</td><td>{analisis_consumo.get('consumo_espejo', 0):.2f} kWh</td></tr>
                <tr><td>Supera 2x Período Espejo</td><td>{'Sí' if analisis_consumo.get('supera_2x_periodo_espejo') else 'No'}</td></tr>
            </table>
            """
        return "<p>Análisis en proceso.</p>"
    
    def _formatear_cumplimiento_html(self, cumplimiento: Dict[str, Any]) -> str:
        """Formatea cumplimiento para HTML"""
        cumplimiento_general = cumplimiento.get('cumplimiento_general', False)
        incumplimientos = cumplimiento.get('incumplimientos', [])
        
        html = f"<p><strong>Cumplimiento General:</strong> {'Sí' if cumplimiento_general else 'No'}</p>"
        if incumplimientos:
            html += "<ul>"
            for inc in incumplimientos:
                html += f"<li>{inc}</li>"
            html += "</ul>"
        return html
    
    def _formatear_instrucciones_html(self, instrucciones: Dict[str, Any]) -> str:
        """Formatea instrucciones para HTML"""
        acciones = instrucciones.get('acciones_inmediatas', [])
        html = "<ul>"
        for accion in acciones:
            html += f"<li><strong>[{accion.get('prioridad', 'normal').upper()}]</strong> {accion.get('accion', '')}</li>"
        html += "</ul>"
        return html
    
    def _formatear_recomendaciones_html(self, informe: Dict[str, Any]) -> str:
        """Formatea recomendaciones para HTML"""
        recomendaciones = informe.get('recomendaciones', [])
        html = "<ul>"
        for rec in recomendaciones:
            html += f"<li><strong>[{rec.get('prioridad', 'normal').upper()}]</strong> {rec.get('recomendacion', '')}</li>"
        html += "</ul>"
        return html
    
    def _generar_texto(self, expediente: Dict[str, Any], analisis: Dict[str, Any],
                      cumplimiento: Dict[str, Any], informe: Dict[str, Any],
                      instrucciones: Dict[str, Any]) -> str:
        """Genera ficha técnica en formato texto plano"""
        texto = []
        texto.append("=" * 80)
        texto.append("FICHA TÉCNICA - ANÁLISIS DE RECLAMO")
        texto.append("=" * 80)
        texto.append(f"\nFecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        texto.append("\n" + self.generador_informe.formatear_texto(informe))
        texto.append("\n" + self.generador_instrucciones.formatear_texto(instrucciones))
        texto.append("\n" + "=" * 80)
        
        # Guardar archivo
        reclamo = expediente.get('reclamo', {})
        numero_reclamo = reclamo.get('numero_reclamo', 'N/A')
        fecha_str = datetime.now().strftime('%Y%m%d')
        
        dir_expedientes = Path(self.rutas.get('expedientes', 'data/expedientes'))
        dir_expedientes.mkdir(parents=True, exist_ok=True)
        
        nombre_archivo = f"FICHA-{numero_reclamo}-{fecha_str}.txt"
        ruta_archivo = dir_expedientes / nombre_archivo
        
        with open(ruta_archivo, 'w', encoding='utf-8') as f:
            f.write('\n'.join(texto))
        
        self.logger.info(f"Ficha técnica TXT generada: {ruta_archivo}")
        return str(ruta_archivo)

