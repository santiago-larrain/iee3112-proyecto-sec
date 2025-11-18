"""
Generador de instrucciones automáticas para funcionarios SEC
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from modulos.utils.logger import Logger
from modulos.utils.config import Config


class GeneradorInstrucciones:
    """Genera instrucciones automáticas según tipología, análisis y cumplimiento"""
    
    def __init__(self, config: Optional[Config] = None, logger: Optional[Logger] = None):
        """
        Inicializa el generador de instrucciones
        
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
        Genera instrucciones automáticas para el funcionario
        
        Args:
            expediente: Expediente completo
            analisis: Resultado del análisis
            cumplimiento: Resultado de evaluación de cumplimiento
            
        Returns:
            Diccionario con instrucciones estructuradas
        """
        self.logger.info("Generando instrucciones automáticas")
        
        tipologia = expediente.get('clasificacion', {}).get('tipologia_principal', '')
        reclamo = expediente.get('reclamo', {})
        
        instrucciones = {
            'fecha_generacion': datetime.now().isoformat(),
            'numero_reclamo': reclamo.get('numero_reclamo'),
            'tipologia': tipologia,
            'acciones_inmediatas': self._generar_acciones_inmediatas(expediente, analisis, cumplimiento),
            'medios_probatorios_solicitar': self._generar_medios_solicitar(cumplimiento, tipologia),
            'pasos_siguientes': self._generar_pasos_siguientes(tipologia, analisis, cumplimiento),
            'recomendaciones': self._generar_recomendaciones(expediente, analisis, cumplimiento),
            'observaciones': self._generar_observaciones(expediente, analisis, cumplimiento)
        }
        
        return instrucciones
    
    def _generar_acciones_inmediatas(self, expediente: Dict[str, Any], 
                                     analisis: Dict[str, Any],
                                     cumplimiento: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Genera lista de acciones inmediatas requeridas"""
        acciones = []
        
        # Verificar cumplimiento de plazos
        if not cumplimiento.get('cumplimiento_plazos', {}).get('cumple', True):
            plazo_info = cumplimiento.get('cumplimiento_plazos', {})
            dias_transcurridos = plazo_info.get('dias_transcurridos', 0)
            plazo_maximo = plazo_info.get('plazo_maximo', 30)
            
            if dias_transcurridos > plazo_maximo:
                acciones.append({
                    'prioridad': 'alta',
                    'accion': 'URGENTE: Reclamo excede plazo de resolución',
                    'detalle': f'El reclamo lleva {dias_transcurridos} días, excediendo el plazo de {plazo_maximo} días.',
                    'siguiente_paso': 'Revisar inmediatamente y emitir resolución'
                })
            else:
                acciones.append({
                    'prioridad': 'media',
                    'accion': 'Monitorear plazo de resolución',
                    'detalle': f'El reclamo lleva {dias_transcurridos} días de {plazo_maximo} días disponibles.',
                    'siguiente_paso': 'Asegurar resolución dentro del plazo'
                })
        
        # Verificar medios probatorios faltantes
        medios_info = cumplimiento.get('medios_probatorios', {})
        if not medios_info.get('completo', True):
            faltantes = medios_info.get('medios_faltantes', [])
            if faltantes:
                acciones.append({
                    'prioridad': 'alta',
                    'accion': 'Solicitar medios probatorios faltantes',
                    'detalle': f'Faltan {len(faltantes)} medios probatorios requeridos.',
                    'siguiente_paso': 'Contactar a la distribuidora para solicitar: ' + ', '.join(faltantes[:3])
                })
        
        # Verificar análisis de consumo (para facturación excesiva)
        if analisis.get('tipologia') == 'facturacion_excesiva':
            analisis_consumo = analisis.get('analisis_consumo', {})
            if analisis_consumo.get('supera_2x_periodo_espejo'):
                acciones.append({
                    'prioridad': 'alta',
                    'accion': 'Verificar consumo excesivo detectado',
                    'detalle': f'El consumo ({analisis_consumo.get("consumo_reclamado", 0):.2f} kWh) supera 2x el período espejo.',
                    'siguiente_paso': 'Revisar análisis técnico y solicitar verificación de medidor si corresponde'
                })
        
        # Si no hay acciones críticas, agregar acción genérica
        if not acciones:
            acciones.append({
                'prioridad': 'normal',
                'accion': 'Revisar expediente completo',
                'detalle': 'El reclamo está en proceso normal.',
                'siguiente_paso': 'Continuar con el análisis según procedimiento'
            })
        
        return acciones
    
    def _generar_medios_solicitar(self, cumplimiento: Dict[str, Any], 
                                  tipologia: str) -> List[Dict[str, Any]]:
        """Genera lista de medios probatorios a solicitar"""
        medios_info = cumplimiento.get('medios_probatorios', {})
        medios_faltantes = medios_info.get('medios_faltantes', [])
        
        medios_solicitar = []
        for medio in medios_faltantes:
            # Determinar prioridad según el medio
            prioridad = 'alta' if 'verificación' in medio.lower() or 'informe' in medio.lower() else 'media'
            
            medios_solicitar.append({
                'medio': medio,
                'prioridad': prioridad,
                'justificacion': self._obtener_justificacion_medio(medio, tipologia),
                'plazo_sugerido': '5 días hábiles' if prioridad == 'alta' else '10 días hábiles'
            })
        
        return medios_solicitar
    
    def _obtener_justificacion_medio(self, medio: str, tipologia: str) -> str:
        """Obtiene justificación para solicitar un medio probatorio"""
        justificaciones = {
            'facturacion_excesiva': {
                'historial de consumo': 'Necesario para comparar consumo actual con histórico',
                'cartola de cuenta corriente': 'Requerida para verificar estado de pagos',
                'verificación de medidor': 'Requerida cuando el consumo supera 2x período espejo'
            },
            'facturacion_provisoria': {
                'lecturas contiguas': 'Necesarias para validar facturación provisoria',
                'fotografía inaccesibilidad': 'Requerida para justificar facturación provisoria'
            },
            'cnr': {
                'notificación': 'Requerida según Resolución 1952',
                'fotografías': 'Necesarias para identificar irregularidad',
                'informe': 'Requerido para comprobar el hecho denunciado'
            }
        }
        
        medio_lower = medio.lower()
        justificaciones_tipologia = justificaciones.get(tipologia, {})
        
        for clave, justificacion in justificaciones_tipologia.items():
            if clave in medio_lower:
                return justificacion
        
        return f'Requerido según manual SEC para tipología {tipologia}'
    
    def _generar_pasos_siguientes(self, tipologia: str, analisis: Dict[str, Any],
                                 cumplimiento: Dict[str, Any]) -> List[str]:
        """Genera pasos siguientes según tipología y estado"""
        pasos = []
        
        # Pasos generales
        if not cumplimiento.get('cumplimiento_general', True):
            pasos.append('Revisar incumplimientos detectados')
            pasos.append('Solicitar información faltante a la distribuidora')
        
        # Pasos específicos por tipología
        if tipologia == 'facturacion_excesiva':
            analisis_consumo = analisis.get('analisis_consumo', {})
            if analisis_consumo.get('supera_2x_periodo_espejo'):
                pasos.append('Indagar por cambios en hábitos de consumo del cliente')
                pasos.append('Solicitar lectura al cliente')
                pasos.append('Ofrecer verificación de medidor sin costo')
            
            causa_raiz = analisis.get('causa_raiz', {})
            if causa_raiz.get('tipo') == 'requiere_verificacion':
                pasos.extend(causa_raiz.get('pasos_sugeridos', []))
        
        elif tipologia == 'facturacion_provisoria':
            pasos.append('Verificar accesibilidad al medidor')
            pasos.append('Solicitar lecturas contiguas (3 puntos)')
            pasos.append('Validar cálculo de facturación provisoria')
        
        elif tipologia == 'cnr':
            pasos.append('Validar notificación del cliente')
            pasos.append('Revisar cálculo de CIM (Consumo Índice Mensual)')
            pasos.append('Verificar período máximo aplicable (12 meses o 3 meses)')
        
        elif tipologia == 'cobros_indebidos':
            pasos.append('Revisar detalle de cargos facturados')
            pasos.append('Validar justificación de cada cargo')
            pasos.append('Verificar si corresponde reembolso')
        
        # Si no hay pasos específicos, agregar genéricos
        if not pasos:
            pasos.append('Revisar análisis técnico completo')
            pasos.append('Validar medios probatorios presentados')
            pasos.append('Emitir resolución según procedimiento')
        
        return pasos
    
    def _generar_recomendaciones(self, expediente: Dict[str, Any], 
                                 analisis: Dict[str, Any],
                                 cumplimiento: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Genera recomendaciones específicas"""
        recomendaciones = []
        
        # Recomendaciones según cumplimiento
        if cumplimiento.get('cumplimiento_general', True):
            recomendaciones.append({
                'tipo': 'positiva',
                'mensaje': 'El expediente cumple con los requisitos normativos',
                'accion': 'Proceder con la resolución del reclamo'
            })
        else:
            recomendaciones.append({
                'tipo': 'atencion',
                'mensaje': 'Se detectaron incumplimientos que deben ser resueltos',
                'accion': 'Revisar incumplimientos antes de emitir resolución'
            })
        
        # Recomendaciones según análisis
        causa_raiz = analisis.get('causa_raiz', {})
        if causa_raiz.get('prioridad') == 'alta':
            recomendaciones.append({
                'tipo': 'urgente',
                'mensaje': 'Se requiere atención prioritaria',
                'accion': causa_raiz.get('pasos_sugeridos', ['Revisar caso con urgencia'])[0] if causa_raiz.get('pasos_sugeridos') else 'Revisar caso con urgencia'
            })
        
        # Recomendaciones según medios probatorios
        medios_info = cumplimiento.get('medios_probatorios', {})
        porcentaje = medios_info.get('porcentaje_completitud', 100)
        if porcentaje < 50:
            recomendaciones.append({
                'tipo': 'atencion',
                'mensaje': f'Solo se cuenta con {porcentaje:.0f}% de medios probatorios requeridos',
                'accion': 'Solicitar medios faltantes antes de continuar'
            })
        
        return recomendaciones
    
    def _generar_observaciones(self, expediente: Dict[str, Any],
                              analisis: Dict[str, Any],
                              cumplimiento: Dict[str, Any]) -> List[str]:
        """Genera observaciones adicionales"""
        observaciones = []
        
        # Observación si es análisis automático
        respuesta_info = cumplimiento.get('respuesta_primera_instancia', {})
        if respuesta_info.get('es_analisis_automatico', False):
            observaciones.append('Este es un análisis automático. No hay respuesta de empresa disponible aún.')
        
        # Observaciones sobre consistencia
        consistencia_info = cumplimiento.get('consistencia_informacion', {})
        if not consistencia_info.get('consistente', True):
            inconsistencias = consistencia_info.get('inconsistencias', [])
            observaciones.append(f'Se detectaron inconsistencias: {", ".join(inconsistencias)}')
        
        # Observaciones sobre clasificación
        clasificacion = expediente.get('clasificacion', {})
        confianza = clasificacion.get('confianza', 1.0)
        if confianza < 0.5:
            observaciones.append(f'La clasificación tiene baja confianza ({confianza*100:.0f}%). Revisar manualmente.')
        
        return observaciones
    
    def formatear_texto(self, instrucciones: Dict[str, Any]) -> str:
        """
        Formatea las instrucciones como texto legible
        
        Args:
            instrucciones: Diccionario con instrucciones
            
        Returns:
            Texto formateado
        """
        texto = []
        texto.append("=" * 80)
        texto.append("INSTRUCCIONES PARA FUNCIONARIO SEC")
        texto.append("=" * 80)
        texto.append(f"\nReclamo: {instrucciones.get('numero_reclamo', 'N/A')}")
        texto.append(f"Tipología: {instrucciones.get('tipologia', 'N/A')}")
        texto.append(f"Fecha: {instrucciones.get('fecha_generacion', 'N/A')}")
        
        # Acciones inmediatas
        texto.append("\n" + "-" * 80)
        texto.append("ACCIONES INMEDIATAS")
        texto.append("-" * 80)
        acciones = instrucciones.get('acciones_inmediatas', [])
        for i, accion in enumerate(acciones, 1):
            texto.append(f"\n{i}. [{accion.get('prioridad', 'normal').upper()}] {accion.get('accion', '')}")
            texto.append(f"   Detalle: {accion.get('detalle', '')}")
            texto.append(f"   Siguiente paso: {accion.get('siguiente_paso', '')}")
        
        # Medios probatorios a solicitar
        medios = instrucciones.get('medios_probatorios_solicitar', [])
        if medios:
            texto.append("\n" + "-" * 80)
            texto.append("MEDIOS PROBATORIOS A SOLICITAR")
            texto.append("-" * 80)
            for i, medio in enumerate(medios, 1):
                texto.append(f"\n{i}. {medio.get('medio', '')}")
                texto.append(f"   Prioridad: {medio.get('prioridad', 'media')}")
                texto.append(f"   Justificación: {medio.get('justificacion', '')}")
                texto.append(f"   Plazo sugerido: {medio.get('plazo_sugerido', '')}")
        
        # Pasos siguientes
        pasos = instrucciones.get('pasos_siguientes', [])
        if pasos:
            texto.append("\n" + "-" * 80)
            texto.append("PASOS SIGUIENTES")
            texto.append("-" * 80)
            for i, paso in enumerate(pasos, 1):
                texto.append(f"{i}. {paso}")
        
        # Recomendaciones
        recomendaciones = instrucciones.get('recomendaciones', [])
        if recomendaciones:
            texto.append("\n" + "-" * 80)
            texto.append("RECOMENDACIONES")
            texto.append("-" * 80)
            for i, rec in enumerate(recomendaciones, 1):
                texto.append(f"\n{i}. [{rec.get('tipo', 'normal').upper()}] {rec.get('mensaje', '')}")
                texto.append(f"   Acción: {rec.get('accion', '')}")
        
        # Observaciones
        observaciones = instrucciones.get('observaciones', [])
        if observaciones:
            texto.append("\n" + "-" * 80)
            texto.append("OBSERVACIONES")
            texto.append("-" * 80)
            for obs in observaciones:
                texto.append(f"- {obs}")
        
        texto.append("\n" + "=" * 80)
        
        return "\n".join(texto)

