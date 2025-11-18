"""
Evaluador de cumplimiento normativo según Manual SEC 2025
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from modulos.utils.logger import Logger
from modulos.utils.config import Config


class EvaluadorCumplimiento:
    """Evalúa cumplimiento de procedimientos normativos"""
    
    PLAZO_RESOLUCION_DIAS = 30  # Según manual
    
    def __init__(self, config: Optional[Config] = None, logger: Optional[Logger] = None):
        """
        Inicializa el evaluador
        
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
    
    def evaluar(self, expediente: Dict[str, Any], tipologia: str) -> Dict[str, Any]:
        """
        Evalúa cumplimiento normativo de un expediente
        
        Args:
            expediente: Datos del expediente
            tipologia: ID de la tipología
            
        Returns:
            Diccionario con evaluación de cumplimiento
        """
        self.logger.info(f"Evaluando cumplimiento para tipología: {tipologia}")
        
        evaluacion = {
            'cumplimiento_plazos': self._evaluar_plazos(expediente),
            'medios_probatorios': self._evaluar_medios_probatorios(expediente, tipologia),
            'consistencia_informacion': self._evaluar_consistencia(expediente),
            'respuesta_primera_instancia': self._evaluar_respuesta(expediente),
            'cumplimiento_general': True,
            'incumplimientos': []
        }
        
        # Determinar cumplimiento general
        # Nota: No penalizar si es análisis automático (no hay respuesta de empresa)
        es_analisis_automatico = evaluacion['respuesta_primera_instancia'].get('es_analisis_automatico', False)
        
        if not evaluacion['cumplimiento_plazos']['cumple']:
            evaluacion['cumplimiento_general'] = False
            evaluacion['incumplimientos'].append(f"Plazos: {evaluacion['cumplimiento_plazos'].get('razon', 'No cumplidos')}")
        
        if not evaluacion['medios_probatorios']['completo']:
            evaluacion['cumplimiento_general'] = False
            faltantes = ', '.join(evaluacion['medios_probatorios'].get('medios_faltantes', []))
            evaluacion['incumplimientos'].append(f"Medios probatorios: Faltan {faltantes}")
        
        if not evaluacion['consistencia_informacion']['consistente']:
            evaluacion['cumplimiento_general'] = False
            inconsistencias = ', '.join(evaluacion['consistencia_informacion'].get('inconsistencias', []))
            evaluacion['incumplimientos'].append(f"Consistencia: {inconsistencias}")
        
        # Si es análisis automático, agregar nota
        if es_analisis_automatico:
            evaluacion['nota'] = 'Este es un análisis automático. La evaluación de respuesta de empresa no aplica.'
        
        return evaluacion
    
    def _evaluar_plazos(self, expediente: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evalúa cumplimiento de plazos (30 días según manual)
        
        Returns:
            Diccionario con evaluación de plazos
        """
        # La fecha_ingreso está en expediente['reclamo']['fecha_ingreso']
        reclamo = expediente.get('reclamo', {})
        fecha_ingreso = reclamo.get('fecha_ingreso') or expediente.get('fecha_ingreso')
        fecha_resolucion = expediente.get('fecha_resolucion')
        
        if not fecha_ingreso:
            return {
                'cumple': False,
                'razon': 'Fecha de ingreso no disponible'
            }
        
        try:
            fecha_ingreso_dt = self._parsear_fecha(fecha_ingreso)
            
            if fecha_resolucion:
                fecha_resolucion_dt = self._parsear_fecha(fecha_resolucion)
                dias_transcurridos = (fecha_resolucion_dt - fecha_ingreso_dt).days
            else:
                # Si no hay resolución, calcular días desde ingreso
                dias_transcurridos = (datetime.now() - fecha_ingreso_dt).days
            
            cumple = dias_transcurridos <= self.PLAZO_RESOLUCION_DIAS
            
            return {
                'cumple': cumple,
                'dias_transcurridos': dias_transcurridos,
                'plazo_maximo': self.PLAZO_RESOLUCION_DIAS,
                'dias_restantes': max(0, self.PLAZO_RESOLUCION_DIAS - dias_transcurridos) if cumple else 0,
                'razon': 'Plazo cumplido' if cumple else f'Plazo excedido en {dias_transcurridos - self.PLAZO_RESOLUCION_DIAS} días'
            }
        except Exception as e:
            return {
                'cumple': False,
                'razon': f'Error al evaluar plazos: {str(e)}'
            }
    
    def _evaluar_medios_probatorios(self, expediente: Dict[str, Any],
                                    tipologia: str) -> Dict[str, Any]:
        """
        Evalúa medios probatorios requeridos según tipología
        
        Returns:
            Diccionario con evaluación de medios probatorios
        """
        medios_requeridos = self._obtener_medios_requeridos(tipologia)
        medios_presentes = expediente.get('medios_probatorios', [])
        
        # Matching flexible de medios probatorios
        medios_encontrados = []
        medios_faltantes = []
        
        for medio_requerido in medios_requeridos:
            encontrado = False
            # Buscar coincidencia exacta o flexible
            for medio_presente in medios_presentes:
                if self._coincide_medio(medio_requerido, medio_presente):
                    medios_encontrados.append(medio_requerido)
                    encontrado = True
                    break
            
            if not encontrado:
                medios_faltantes.append(medio_requerido)
        
        return {
            'completo': len(medios_faltantes) == 0,
            'medios_requeridos': medios_requeridos,
            'medios_presentes': medios_presentes,
            'medios_encontrados': medios_encontrados,
            'medios_faltantes': medios_faltantes,
            'porcentaje_completitud': len(medios_encontrados) / len(medios_requeridos) * 100 if medios_requeridos else 0
        }
    
    def _coincide_medio(self, requerido: str, presente: str) -> bool:
        """
        Verifica si un medio presente coincide con uno requerido (matching flexible)
        
        Args:
            requerido: Medio probatorio requerido
            presente: Medio probatorio presente
            
        Returns:
            True si coinciden, False en caso contrario
        """
        # Coincidencia exacta
        if requerido.lower() == presente.lower():
            return True
        
        # Normalizar strings para comparación
        req_norm = requerido.lower().strip()
        pres_norm = presente.lower().strip()
        
        # Coincidencia parcial (uno contiene al otro)
        if req_norm in pres_norm or pres_norm in req_norm:
            return True
        
        # Matching flexible para casos comunes
        equivalencias = {
            'historial de consumo': ['historial de consumo', 'historial consumo', 'boletas'],
            'cartola de consumo': ['cartola de consumo', 'cartola consumo'],
            'cartola de cuenta corriente': ['cartola de cuenta corriente', 'cartola cuenta corriente', 'cuenta corriente'],
            '24 meses': ['24 meses', '24 boletas', '24 periodos'],
            'carta respuesta': ['carta respuesta', 'respuesta', 'carta']
        }
        
        # Verificar equivalencias
        for clave, variantes in equivalencias.items():
            if clave in req_norm:
                for variante in variantes:
                    if variante in pres_norm:
                        return True
            if clave in pres_norm:
                for variante in variantes:
                    if variante in req_norm:
                        return True
        
        return False
    
    def _evaluar_consistencia(self, expediente: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evalúa consistencia de información
        
        Returns:
            Diccionario con evaluación de consistencia
        """
        inconsistencias = []
        
        # Verificar que los datos del expediente sean consistentes
        analisis = expediente.get('analisis', {})
        boletas = expediente.get('boletas', [])
        
        # Verificar que los consumos en el análisis coincidan con las boletas
        if 'analisis_consumo' in analisis:
            consumo_analisis = analisis['analisis_consumo'].get('consumo_reclamado')
            if consumo_analisis:
                # Buscar consumo en boletas
                consumo_boletas = None
                for boleta in boletas:
                    if boleta.get('periodo_facturacion') == analisis['analisis_consumo'].get('periodo_reclamado'):
                        consumo_boletas = boleta.get('consumo_kwh')
                        break
                
                if consumo_boletas and abs(consumo_analisis - consumo_boletas) > 0.1:
                    inconsistencias.append(
                        f"Discrepancia en consumo: análisis={consumo_analisis}, boleta={consumo_boletas}"
                    )
        
        return {
            'consistente': len(inconsistencias) == 0,
            'inconsistencias': inconsistencias
        }
    
    def _evaluar_respuesta(self, expediente: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evalúa calidad de respuesta de primera instancia
        
        Nota: Distingue entre análisis automático y respuesta real de empresa
        
        Returns:
            Diccionario con evaluación de respuesta
        """
        respuesta = expediente.get('respuesta_empresa', {})
        
        # Si no hay respuesta de empresa, esto es solo análisis automático
        if not respuesta:
            return {
                'completa': False,
                'es_analisis_automatico': True,
                'razon': 'No hay respuesta de empresa disponible. Este es un análisis automático.',
                'elementos_requeridos': [
                    'revision_caso',
                    'conclusiones',
                    'recomendaciones'
                ],
                'elementos_presentes': [],
                'elementos_faltantes': [
                    'revision_caso',
                    'conclusiones',
                    'recomendaciones'
                ]
            }
        
        # Si hay respuesta, evaluarla normalmente
        elementos_requeridos = [
            'revision_caso',
            'conclusiones',
            'recomendaciones'
        ]
        
        elementos_presentes = []
        for elemento in elementos_requeridos:
            if respuesta.get(elemento):
                elementos_presentes.append(elemento)
        
        return {
            'completa': len(elementos_presentes) == len(elementos_requeridos),
            'es_analisis_automatico': False,
            'elementos_requeridos': elementos_requeridos,
            'elementos_presentes': elementos_presentes,
            'elementos_faltantes': [e for e in elementos_requeridos if e not in elementos_presentes]
        }
    
    def _obtener_medios_requeridos(self, tipologia: str) -> List[str]:
        """
        Obtiene medios probatorios requeridos según tipología
        
        Args:
            tipologia: ID de la tipología
            
        Returns:
            Lista de medios probatorios requeridos
        """
        medios_por_tipologia = {
            'facturacion_excesiva': [
                'Historial de consumo (24 meses)',
                'Cartola de consumo',
                'Cartola de cuenta corriente',
                'Informe de verificación de medidor (si aplica)',
                'Carta respuesta'
            ],
            'facturacion_provisoria': [
                'Tabla histórica de lecturas',
                'Lecturas contiguas (3 puntos)',
                'Fotografía de inaccesibilidad',
                'Boleta con registro provisorio',
                'Carta respuesta'
            ],
            'error_lectura': [
                'Lectura aportada por cliente',
                'Verificación de lectura',
                'Historial de lecturas'
            ],
            'cnr': [
                'Medio de prueba (notificación, reconocimiento, constancia, fotografías, informe)',
                'Historial de consumos (2 años)',
                'Memoria de cálculo CIM'
            ],
            'cobros_indebidos': [
                'Cartola de facturación',
                'Detalle de cargos',
                'Solicitud del cliente (si servicio asociado)',
                'Carta respuesta'
            ]
        }
        
        return medios_por_tipologia.get(tipologia, ['Documentación del reclamo'])
    
    def _parsear_fecha(self, fecha: str) -> datetime:
        """Parsea fecha en diferentes formatos"""
        formatos = ['%Y-%m-%d', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']
        
        for formato in formatos:
            try:
                return datetime.strptime(fecha, formato)
            except ValueError:
                continue
        
        raise ValueError(f"No se pudo parsear fecha: {fecha}")

