"""
Generador de informe ejecutivo con explicación del análisis
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from modulos.utils.logger import Logger
from modulos.utils.config import Config


class GeneradorInforme:
    """Genera informe ejecutivo con explicación del análisis, resultados y recomendaciones"""
    
    def __init__(self, config: Optional[Config] = None, logger: Optional[Logger] = None):
        """
        Inicializa el generador de informes
        
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
    
    def generar(self, expediente: Dict[str, Any], analisis: Dict[str, Any],
                cumplimiento: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera informe ejecutivo completo
        
        Args:
            expediente: Expediente completo
            analisis: Resultado del análisis
            cumplimiento: Resultado de evaluación de cumplimiento
            
        Returns:
            Diccionario con informe estructurado
        """
        self.logger.info("Generando informe ejecutivo")
        
        reclamo = expediente.get('reclamo', {})
        clasificacion = expediente.get('clasificacion', {})
        
        informe = {
            'metadata': {
                'fecha_generacion': datetime.now().isoformat(),
                'numero_reclamo': reclamo.get('numero_reclamo'),
                'version': '1.0'
            },
            'resumen_ejecutivo': self._generar_resumen_ejecutivo(expediente, analisis, cumplimiento),
            'explicacion_analisis': self._generar_explicacion_analisis(expediente, analisis),
            'resultados': self._generar_resultados(analisis, cumplimiento),
            'justificacion_tecnica': self._generar_justificacion_tecnica(expediente, analisis),
            'recomendaciones': self._generar_recomendaciones_informe(expediente, analisis, cumplimiento),
            'conclusiones': self._generar_conclusiones(expediente, analisis, cumplimiento)
        }
        
        return informe
    
    def _generar_resumen_ejecutivo(self, expediente: Dict[str, Any],
                                   analisis: Dict[str, Any],
                                   cumplimiento: Dict[str, Any]) -> Dict[str, Any]:
        """Genera resumen ejecutivo"""
        reclamo = expediente.get('reclamo', {})
        clasificacion = expediente.get('clasificacion', {})
        
        return {
            'numero_reclamo': reclamo.get('numero_reclamo'),
            'cliente': reclamo.get('numero_cliente'),
            'distribuidora': reclamo.get('distribuidora'),
            'tipologia': clasificacion.get('tipologia_principal'),
            'confianza_clasificacion': clasificacion.get('confianza', 0),
            'conclusion_principal': self._obtener_conclusion_principal(analisis, cumplimiento),
            'estado_cumplimiento': 'Cumple' if cumplimiento.get('cumplimiento_general', False) else 'No cumple',
            'fecha_ingreso': reclamo.get('fecha_ingreso')
        }
    
    def _obtener_conclusion_principal(self, analisis: Dict[str, Any],
                                     cumplimiento: Dict[str, Any]) -> str:
        """Obtiene conclusión principal del análisis"""
        if analisis.get('tipologia') == 'facturacion_excesiva':
            analisis_consumo = analisis.get('analisis_consumo', {})
            if analisis_consumo.get('supera_2x_periodo_espejo'):
                return 'Consumo excesivo detectado. Requiere verificación de medidor.'
            else:
                return 'Consumo dentro de rangos normales.'
        
        causa_raiz = analisis.get('causa_raiz', {})
        if causa_raiz:
            tipo = causa_raiz.get('tipo', '')
            if tipo == 'requiere_verificacion':
                return 'Requiere verificación técnica adicional.'
            elif tipo == 'justificado':
                return 'El reclamo está justificado según análisis técnico.'
            elif tipo == 'no_justificado':
                return 'El reclamo no está justificado según análisis técnico.'
        
        return 'En análisis'
    
    def _generar_explicacion_analisis(self, expediente: Dict[str, Any],
                                     analisis: Dict[str, Any]) -> Dict[str, Any]:
        """Genera explicación detallada del análisis realizado"""
        tipologia = analisis.get('tipologia', '')
        procedimiento = analisis.get('procedimiento_aplicado', '')
        pasos = analisis.get('pasos_completados', [])
        
        explicacion = {
            'tipologia_analizada': tipologia,
            'procedimiento_aplicado': procedimiento,
            'pasos_completados': pasos,
            'metodologia': self._obtener_metodologia(tipologia),
            'descarte_causas_comunes': analisis.get('descarte_causas_comunes', {}),
            'analisis_especifico': self._generar_analisis_especifico(analisis)
        }
        
        return explicacion
    
    def _obtener_metodologia(self, tipologia: str) -> str:
        """Obtiene descripción de metodología según tipología"""
        metodologias = {
            'facturacion_excesiva': '''
            Metodología aplicada según Anexo N°1 del Manual SEC:
            1. Descarte de causas comunes (CNR, facturación provisoria, cobros indebidos)
            2. Análisis de consumo comparando con período espejo (mismo mes año anterior)
            3. Aplicación de umbral 2x período espejo
            4. Árbol de decisión según resultado del análisis
            ''',
            'facturacion_provisoria': '''
            Metodología aplicada según Anexo N°2 del Manual SEC:
            1. Verificación de accesibilidad al medidor
            2. Análisis de lecturas contiguas
            3. Validación de cálculo de facturación provisoria
            ''',
            'cnr': '''
            Metodología aplicada según Resolución Exenta 1952:
            1. Validación de notificación del cliente
            2. Cálculo de CIM (Consumo Índice Mensual)
            3. Determinación de período máximo aplicable
            4. Validación de medios probatorios
            '''
        }
        
        return metodologias.get(tipologia, 'Metodología según procedimiento SEC aplicable.')
    
    def _generar_analisis_especifico(self, analisis: Dict[str, Any]) -> Dict[str, Any]:
        """Genera análisis específico según tipología"""
        tipologia = analisis.get('tipologia', '')
        
        if tipologia == 'facturacion_excesiva':
            analisis_consumo = analisis.get('analisis_consumo', {})
            return {
                'tipo': 'analisis_consumo',
                'consumo_reclamado': analisis_consumo.get('consumo_reclamado'),
                'consumo_espejo': analisis_consumo.get('consumo_espejo'),
                'periodo_reclamado': analisis_consumo.get('periodo_reclamado'),
                'periodo_espejo': analisis_consumo.get('periodo_espejo'),
                'supera_2x': analisis_consumo.get('supera_2x_periodo_espejo'),
                'factor': analisis_consumo.get('factor'),
                'interpretacion': self._interpretar_analisis_consumo(analisis_consumo)
            }
        
        return {}
    
    def _interpretar_analisis_consumo(self, analisis_consumo: Dict[str, Any]) -> str:
        """Interpreta el análisis de consumo"""
        if not analisis_consumo:
            return 'No hay análisis de consumo disponible.'
        
        consumo_reclamado = analisis_consumo.get('consumo_reclamado', 0)
        consumo_espejo = analisis_consumo.get('consumo_espejo', 0)
        supera_2x = analisis_consumo.get('supera_2x_periodo_espejo', False)
        factor = analisis_consumo.get('factor', 1.0)
        
        if supera_2x:
            return f'El consumo reclamado ({consumo_reclamado:.2f} kWh) supera en {factor:.2f}x el consumo del período espejo ({consumo_espejo:.2f} kWh). Esto indica un consumo anormalmente alto que requiere investigación adicional.'
        else:
            return f'El consumo reclamado ({consumo_reclamado:.2f} kWh) está dentro de rangos normales comparado con el período espejo ({consumo_espejo:.2f} kWh).'
    
    def _generar_resultados(self, analisis: Dict[str, Any],
                          cumplimiento: Dict[str, Any]) -> Dict[str, Any]:
        """Genera sección de resultados"""
        return {
            'analisis': {
                'tipologia_detectada': analisis.get('tipologia'),
                'causa_raiz': analisis.get('causa_raiz', {}),
                'recomendaciones_analisis': analisis.get('recomendaciones', [])
            },
            'cumplimiento': {
                'cumplimiento_general': cumplimiento.get('cumplimiento_general', False),
                'cumplimiento_plazos': cumplimiento.get('cumplimiento_plazos', {}).get('cumple', False),
                'medios_probatorios': cumplimiento.get('medios_probatorios', {}).get('completo', False),
                'consistencia': cumplimiento.get('consistencia_informacion', {}).get('consistente', False),
                'incumplimientos': cumplimiento.get('incumplimientos', [])
            }
        }
    
    def _generar_justificacion_tecnica(self, expediente: Dict[str, Any],
                                      analisis: Dict[str, Any]) -> Dict[str, Any]:
        """Genera justificación técnica de las conclusiones"""
        tipologia = analisis.get('tipologia', '')
        causa_raiz = analisis.get('causa_raiz', {})
        
        justificacion = {
            'base_normativa': self._obtener_base_normativa(tipologia),
            'criterios_aplicados': self._obtener_criterios_aplicados(analisis),
            'evidencia_considerada': self._obtener_evidencia_considerada(expediente, analisis),
            'razonamiento': self._generar_razonamiento(analisis, causa_raiz)
        }
        
        return justificacion
    
    def _obtener_base_normativa(self, tipologia: str) -> str:
        """Obtiene base normativa según tipología"""
        bases = {
            'facturacion_excesiva': 'Manual de Procedimiento de Resolución de Reclamos SEC 2025 - Anexo N°1',
            'facturacion_provisoria': 'Manual de Procedimiento de Resolución de Reclamos SEC 2025 - Anexo N°2',
            'cnr': 'Resolución Exenta 1952 - Procedimiento para determinación, valorización y facturación de consumos no registrados',
            'cobros_indebidos': 'Manual de Procedimiento de Resolución de Reclamos SEC 2025 - Anexo N°3'
        }
        
        return bases.get(tipologia, 'Manual de Procedimiento de Resolución de Reclamos SEC 2025')
    
    def _obtener_criterios_aplicados(self, analisis: Dict[str, Any]) -> List[str]:
        """Obtiene criterios aplicados en el análisis"""
        criterios = []
        
        if analisis.get('tipologia') == 'facturacion_excesiva':
            criterios.append('Umbral 2x período espejo para consumo excesivo')
            criterios.append('Comparación con mismo mes del año anterior')
            criterios.append('Descarte de causas comunes (CNR, facturación provisoria)')
        
        return criterios
    
    def _obtener_evidencia_considerada(self, expediente: Dict[str, Any],
                                      analisis: Dict[str, Any]) -> List[str]:
        """Obtiene evidencia considerada en el análisis"""
        evidencia = []
        
        boletas = expediente.get('boletas', [])
        if boletas:
            evidencia.append(f'Historial de {len(boletas)} boletas de consumo')
        
        medios = expediente.get('medios_probatorios', [])
        if medios:
            evidencia.extend(medios)
        
        return evidencia
    
    def _generar_razonamiento(self, analisis: Dict[str, Any],
                             causa_raiz: Dict[str, Any]) -> str:
        """Genera razonamiento técnico"""
        if analisis.get('tipologia') == 'facturacion_excesiva':
            analisis_consumo = analisis.get('analisis_consumo', {})
            if analisis_consumo.get('supera_2x_periodo_espejo'):
                return '''
                El análisis comparativo muestra que el consumo reclamado supera significativamente 
                (más de 2 veces) el consumo del mismo período del año anterior. Esta discrepancia 
                justifica una investigación adicional para determinar la causa raíz, que puede 
                incluir: error de lectura, falla en el medidor, cambio en hábitos de consumo, 
                o consumo no registrado. Se recomienda verificación del medidor y solicitud de 
                lectura al cliente.
                '''
        
        tipo_causa = causa_raiz.get('tipo', '')
        if tipo_causa == 'requiere_verificacion':
            return 'El análisis indica que se requiere verificación técnica adicional para determinar la causa raíz del reclamo.'
        elif tipo_causa == 'justificado':
            return 'El análisis técnico justifica el reclamo presentado por el cliente.'
        elif tipo_causa == 'no_justificado':
            return 'El análisis técnico no justifica el reclamo presentado por el cliente.'
        
        return 'El análisis se encuentra en proceso.'
    
    def _generar_recomendaciones_informe(self, expediente: Dict[str, Any],
                                        analisis: Dict[str, Any],
                                        cumplimiento: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Genera recomendaciones para el informe"""
        recomendaciones = []
        
        # Recomendaciones según cumplimiento
        if not cumplimiento.get('cumplimiento_general', True):
            recomendaciones.append({
                'tipo': 'accion',
                'prioridad': 'alta',
                'recomendacion': 'Resolver incumplimientos detectados antes de emitir resolución',
                'detalle': 'Se detectaron incumplimientos en plazos, medios probatorios o consistencia de información.'
            })
        
        # Recomendaciones según análisis
        causa_raiz = analisis.get('causa_raiz', {})
        if causa_raiz.get('tipo') == 'requiere_verificacion':
            recomendaciones.append({
                'tipo': 'accion',
                'prioridad': 'alta',
                'recomendacion': 'Solicitar verificación técnica del medidor',
                'detalle': 'El análisis indica que se requiere verificación del medidor para determinar la causa raíz.'
            })
        
        # Recomendaciones según medios probatorios
        medios_info = cumplimiento.get('medios_probatorios', {})
        if not medios_info.get('completo', True):
            faltantes = medios_info.get('medios_faltantes', [])
            recomendaciones.append({
                'tipo': 'accion',
                'prioridad': 'media',
                'recomendacion': f'Solicitar {len(faltantes)} medios probatorios faltantes',
                'detalle': f'Medios faltantes: {", ".join(faltantes[:3])}'
            })
        
        return recomendaciones
    
    def _generar_conclusiones(self, expediente: Dict[str, Any],
                              analisis: Dict[str, Any],
                              cumplimiento: Dict[str, Any]) -> Dict[str, Any]:
        """Genera conclusiones finales"""
        return {
            'conclusion_principal': self._obtener_conclusion_principal(analisis, cumplimiento),
            'estado_cumplimiento': 'Cumple' if cumplimiento.get('cumplimiento_general', False) else 'No cumple',
            'siguiente_paso': self._obtener_siguiente_paso(analisis, cumplimiento),
            'observaciones': self._generar_observaciones_informe(expediente, analisis, cumplimiento)
        }
    
    def _obtener_siguiente_paso(self, analisis: Dict[str, Any],
                                cumplimiento: Dict[str, Any]) -> str:
        """Obtiene siguiente paso recomendado"""
        if not cumplimiento.get('cumplimiento_general', True):
            return 'Resolver incumplimientos detectados y solicitar información faltante'
        
        causa_raiz = analisis.get('causa_raiz', {})
        if causa_raiz.get('tipo') == 'requiere_verificacion':
            return 'Solicitar verificación técnica del medidor'
        
        return 'Proceder con la resolución del reclamo según procedimiento'
    
    def _generar_observaciones_informe(self, expediente: Dict[str, Any],
                                      analisis: Dict[str, Any],
                                      cumplimiento: Dict[str, Any]) -> List[str]:
        """Genera observaciones para el informe"""
        observaciones = []
        
        clasificacion = expediente.get('clasificacion', {})
        confianza = clasificacion.get('confianza', 1.0)
        if confianza < 0.5:
            observaciones.append(f'La clasificación tiene baja confianza ({confianza*100:.0f}%). Se recomienda revisión manual.')
        
        respuesta_info = cumplimiento.get('respuesta_primera_instancia', {})
        if respuesta_info.get('es_analisis_automatico', False):
            observaciones.append('Este es un análisis automático. No hay respuesta de empresa disponible aún.')
        
        return observaciones
    
    def formatear_texto(self, informe: Dict[str, Any]) -> str:
        """
        Formatea el informe como texto legible
        
        Args:
            informe: Diccionario con informe
            
        Returns:
            Texto formateado
        """
        texto = []
        texto.append("=" * 80)
        texto.append("INFORME EJECUTIVO - ANÁLISIS DE RECLAMO")
        texto.append("=" * 80)
        
        metadata = informe.get('metadata', {})
        texto.append(f"\nReclamo: {metadata.get('numero_reclamo', 'N/A')}")
        texto.append(f"Fecha: {metadata.get('fecha_generacion', 'N/A')}")
        
        # Resumen ejecutivo
        resumen = informe.get('resumen_ejecutivo', {})
        texto.append("\n" + "-" * 80)
        texto.append("RESUMEN EJECUTIVO")
        texto.append("-" * 80)
        texto.append(f"Cliente: {resumen.get('cliente', 'N/A')}")
        texto.append(f"Distribuidora: {resumen.get('distribuidora', 'N/A')}")
        texto.append(f"Tipología: {resumen.get('tipologia', 'N/A')}")
        texto.append(f"Conclusión: {resumen.get('conclusion_principal', 'N/A')}")
        texto.append(f"Estado Cumplimiento: {resumen.get('estado_cumplimiento', 'N/A')}")
        
        # Explicación del análisis
        explicacion = informe.get('explicacion_analisis', {})
        texto.append("\n" + "-" * 80)
        texto.append("EXPLICACIÓN DEL ANÁLISIS")
        texto.append("-" * 80)
        texto.append(f"Procedimiento: {explicacion.get('procedimiento_aplicado', 'N/A')}")
        texto.append(f"Metodología: {explicacion.get('metodologia', 'N/A').strip()}")
        
        # Resultados
        resultados = informe.get('resultados', {})
        texto.append("\n" + "-" * 80)
        texto.append("RESULTADOS")
        texto.append("-" * 80)
        texto.append(f"Cumplimiento General: {'Sí' if resultados.get('cumplimiento', {}).get('cumplimiento_general') else 'No'}")
        
        # Justificación técnica
        justificacion = informe.get('justificacion_tecnica', {})
        texto.append("\n" + "-" * 80)
        texto.append("JUSTIFICACIÓN TÉCNICA")
        texto.append("-" * 80)
        texto.append(f"Base Normativa: {justificacion.get('base_normativa', 'N/A')}")
        texto.append(f"Razonamiento: {justificacion.get('razonamiento', 'N/A').strip()}")
        
        # Recomendaciones
        recomendaciones = informe.get('recomendaciones', [])
        if recomendaciones:
            texto.append("\n" + "-" * 80)
            texto.append("RECOMENDACIONES")
            texto.append("-" * 80)
            for i, rec in enumerate(recomendaciones, 1):
                texto.append(f"\n{i}. [{rec.get('prioridad', 'normal').upper()}] {rec.get('recomendacion', '')}")
                texto.append(f"   {rec.get('detalle', '')}")
        
        # Conclusiones
        conclusiones = informe.get('conclusiones', {})
        texto.append("\n" + "-" * 80)
        texto.append("CONCLUSIONES")
        texto.append("-" * 80)
        texto.append(f"Conclusión Principal: {conclusiones.get('conclusion_principal', 'N/A')}")
        texto.append(f"Siguiente Paso: {conclusiones.get('siguiente_paso', 'N/A')}")
        
        observaciones = conclusiones.get('observaciones', [])
        if observaciones:
            texto.append("\nObservaciones:")
            for obs in observaciones:
                texto.append(f"- {obs}")
        
        texto.append("\n" + "=" * 80)
        
        return "\n".join(texto)

