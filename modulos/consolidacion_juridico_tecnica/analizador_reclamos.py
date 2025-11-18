"""
Analizador de reclamos según procedimientos del Manual SEC 2025
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from modulos.utils.logger import Logger
from modulos.utils.config import Config


class AnalizadorReclamos:
    """Analiza reclamos según procedimientos específicos de cada tipología"""
    
    def __init__(self, config: Optional[Config] = None, logger: Optional[Logger] = None):
        """
        Inicializa el analizador
        
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
    
    def analizar(self, reclamo: Dict[str, Any], boletas: List[Dict[str, Any]], 
                tipologia: str) -> Dict[str, Any]:
        """
        Analiza un reclamo según su tipología
        
        Args:
            reclamo: Datos del reclamo
            boletas: Lista de boletas del cliente (últimos 24 meses)
            tipologia: ID de la tipología
            
        Returns:
            Diccionario con resultado del análisis
        """
        self.logger.info(f"Analizando reclamo tipo: {tipologia}")
        
        if tipologia == 'facturacion_excesiva':
            return self._analizar_facturacion_excesiva(reclamo, boletas)
        elif tipologia == 'facturacion_provisoria':
            return self._analizar_facturacion_provisoria(reclamo, boletas)
        elif tipologia == 'error_lectura':
            return self._analizar_error_lectura(reclamo, boletas)
        elif tipologia == 'cnr':
            return self._analizar_cnr(reclamo, boletas)
        elif tipologia == 'cobros_indebidos':
            return self._analizar_cobros_indebidos(reclamo, boletas)
        else:
            return self._analizar_generico(reclamo, boletas, tipologia)
    
    def _analizar_facturacion_excesiva(self, reclamo: Dict[str, Any], 
                                      boletas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analiza reclamo de Facturación Excesiva según Anexo N°1
        
        Procedimiento según manual:
        1. Descartar CNR, Facturación Provisoria, Cobros Indebidos
        2. Comparar consumo con 2x período espejo (año anterior)
        3. Árbol de decisión: causas internas → error lectura → problema medidor
        """
        self.logger.info("Aplicando análisis de Facturación Excesiva")
        
        resultado = {
            'tipologia': 'facturacion_excesiva',
            'procedimiento_aplicado': 'Anexo N°1',
            'pasos_completados': [],
            'descarte_causas_comunes': {},
            'analisis_consumo': {},
            'causa_raiz': None,
            'recomendaciones': []
        }
        
        # Paso 1: Descartar causas comunes
        resultado['pasos_completados'].append('descarte_causas_comunes')
        descarte = self._descartar_causas_comunes(boletas)
        resultado['descarte_causas_comunes'] = descarte
        
        if descarte['tiene_cnr']:
            resultado['recomendaciones'].append(
                "Reclasificar como CNR según Resolución 1952"
            )
            return resultado
        
        if descarte['tiene_facturacion_provisoria']:
            resultado['recomendaciones'].append(
                "Reclasificar como Facturación Provisoria (Anexo N°2)"
            )
            return resultado
        
        if descarte['tiene_cobros_indebidos']:
            resultado['recomendaciones'].append(
                "Reclasificar como Cobros Indebidos (Anexo N°3)"
            )
            return resultado
        
        # Paso 2: Análisis de consumo
        resultado['pasos_completados'].append('analisis_consumo')
        analisis_consumo = self._analizar_consumo_excesivo(boletas)
        resultado['analisis_consumo'] = analisis_consumo
        
        # Paso 3: Árbol de decisión
        if analisis_consumo['supera_2x_periodo_espejo']:
            resultado['pasos_completados'].append('arbol_decision')
            causa_raiz = self._determinar_causa_raiz(analisis_consumo, boletas)
            resultado['causa_raiz'] = causa_raiz
            
            if causa_raiz['tipo'] == 'causas_internas':
                resultado['recomendaciones'].append(
                    "Verificar cambios en hábitos de consumo o fugas en instalación interior"
                )
            elif causa_raiz['tipo'] == 'error_lectura':
                resultado['recomendaciones'].append(
                    "Solicitar lectura al cliente o verificación de lectura (con costo si lectura fue correcta)"
                )
            elif causa_raiz['tipo'] == 'problema_medidor':
                resultado['recomendaciones'].append(
                    "Ofrecer verificación de medidor sin costo"
                )
        else:
            resultado['conclusion'] = 'consumo_dentro_habitual'
            resultado['recomendaciones'].append(
                "El consumo está dentro del comportamiento habitual. "
                "Si el cliente no está de acuerdo, solicitar lectura o verificación con costo."
            )
        
        return resultado
    
    def _descartar_causas_comunes(self, boletas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Descarta causas comunes: CNR, Facturación Provisoria, Cobros Indebidos
        
        Returns:
            Diccionario con resultados del descarte
        """
        descarte = {
            'tiene_cnr': False,
            'tiene_facturacion_provisoria': False,
            'tiene_cobros_indebidos': False,
            'detalles': {}
        }
        
        # Verificar facturación provisoria (promedios)
        for boleta in boletas:
            periodo = boleta.get('periodo_facturacion', '')
            if 'provisori' in periodo.lower() or 'promedio' in periodo.lower():
                descarte['tiene_facturacion_provisoria'] = True
                descarte['detalles']['facturacion_provisoria'] = {
                    'periodo': periodo,
                    'boleta': boleta.get('numero_boleta')
                }
        
        # Verificar lecturas cero o idénticas (indicador de provisoria)
        for i, boleta in enumerate(boletas):
            lectura_actual = boleta.get('lectura_actual')
            lectura_anterior = boleta.get('lectura_anterior')
            
            if lectura_actual == 0 or lectura_actual == lectura_anterior:
                descarte['tiene_facturacion_provisoria'] = True
                descarte['detalles']['lectura_cero_identica'] = {
                    'periodo': boleta.get('periodo_facturacion'),
                    'lectura_actual': lectura_actual,
                    'lectura_anterior': lectura_anterior
                }
        
        return descarte
    
    def _analizar_consumo_excesivo(self, boletas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analiza si el consumo excede 2x el período espejo (año anterior)
        
        Según manual: Si consumo > 2x mismo período año anterior
        """
        if not boletas:
            return {
                'supera_2x_periodo_espejo': False,
                'razon': 'No hay boletas para comparar'
            }
        
        # Ordenar boletas por período (más reciente primero)
        boletas_ordenadas = sorted(
            boletas,
            key=lambda b: self._parsear_periodo(b.get('periodo_facturacion', '')),
            reverse=True
        )
        
        # Obtener períodos reclamados (últimas boletas)
        # Por simplicidad, analizar la boleta más reciente
        boleta_reclamada = boletas_ordenadas[0]
        consumo_reclamado = boleta_reclamada.get('consumo_kwh')
        periodo_reclamado = boleta_reclamada.get('periodo_facturacion')
        
        if not consumo_reclamado:
            return {
                'supera_2x_periodo_espejo': False,
                'razon': 'No se puede determinar consumo reclamado'
            }
        
        # Buscar período espejo (mismo mes del año anterior)
        periodo_espejo = self._obtener_periodo_espejo(periodo_reclamado)
        consumo_espejo = self._obtener_consumo_periodo(boletas_ordenadas, periodo_espejo)
        
        if not consumo_espejo:
            # Si no hay período exacto, usar promedio de meses circundantes
            consumo_espejo = self._obtener_promedio_periodo_espejo(
                boletas_ordenadas, periodo_reclamado
            )
        
        if not consumo_espejo:
            return {
                'supera_2x_periodo_espejo': False,
                'razon': 'No se encontró período espejo para comparar'
            }
        
        # Comparar: consumo > 2x período espejo
        umbral = consumo_espejo * 2
        supera = consumo_reclamado > umbral
        
        return {
            'supera_2x_periodo_espejo': supera,
            'consumo_reclamado': consumo_reclamado,
            'consumo_espejo': consumo_espejo,
            'umbral_2x': umbral,
            'diferencia': consumo_reclamado - consumo_espejo,
            'factor': consumo_reclamado / consumo_espejo if consumo_espejo > 0 else 0,
            'periodo_reclamado': periodo_reclamado,
            'periodo_espejo': periodo_espejo
        }
    
    def _determinar_causa_raiz(self, analisis_consumo: Dict[str, Any],
                               boletas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Determina la causa raíz según árbol de decisión del manual
        
        Árbol:
        1. Causas internas (cambio hábitos, fuga)
        2. Error de lectura
        3. Problema de medidor
        """
        # Por ahora, retornar análisis básico
        # En implementación completa, se harían verificaciones adicionales
        
        return {
            'tipo': 'requiere_verificacion',
            'pasos_sugeridos': [
                'Indagar por cambios en hábitos de consumo',
                'Solicitar lectura al cliente',
                'Ofrecer verificación de medidor sin costo'
            ],
            'prioridad': 'alta'
        }
    
    def _analizar_facturacion_provisoria(self, reclamo: Dict[str, Any],
                                        boletas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza reclamo de Facturación Provisoria según Anexo N°2"""
        resultado = {
            'tipologia': 'facturacion_provisoria',
            'procedimiento_aplicado': 'Anexo N°2',
            'meses_provisorios': 0,
            'requiere_limite_triple': False,
            'medios_probatorios_requeridos': []
        }
        
        # Contar meses provisorios consecutivos
        meses_provisorios = 0
        for boleta in boletas:
            periodo = boleta.get('periodo_facturacion', '').lower()
            lectura_actual = boleta.get('lectura_actual')
            lectura_anterior = boleta.get('lectura_anterior')
            
            if 'provisori' in periodo or lectura_actual == lectura_anterior:
                meses_provisorios += 1
            else:
                break  # Romper si encuentra lectura efectiva
        
        resultado['meses_provisorios'] = meses_provisorios
        
        # Si 3+ meses consecutivos, límite es triple del promedio
        if meses_provisorios >= 3:
            resultado['requiere_limite_triple'] = True
            resultado['medios_probatorios_requeridos'] = [
                'Lecturas contiguas (3 puntos)',
                'Fotografía de inaccesibilidad',
                'Tabla histórica de lecturas'
            ]
        
        return resultado
    
    def _analizar_error_lectura(self, reclamo: Dict[str, Any],
                               boletas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza reclamo de Error de Lectura según Anexo N°1.1"""
        return {
            'tipologia': 'error_lectura',
            'procedimiento_aplicado': 'Anexo N°1.1',
            'requiere_lectura_cliente': True,
            'requiere_verificacion_lectura': False
        }
    
    def _analizar_cnr(self, reclamo: Dict[str, Any],
                     boletas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza reclamo de CNR según Resolución 1952"""
        return {
            'tipologia': 'cnr',
            'procedimiento_aplicado': 'Resolución 1952',
            'requiere_cim': True,
            'periodo_maximo': 12  # meses para conexiones irregulares
        }
    
    def _analizar_cobros_indebidos(self, reclamo: Dict[str, Any],
                                   boletas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza reclamo de Cobros Indebidos según Anexo N°3"""
        return {
            'tipologia': 'cobros_indebidos',
            'procedimiento_aplicado': 'Anexo N°3',
            'categoria': None  # inherente, contable/financiero, servicio asociado
        }
    
    def _analizar_generico(self, reclamo: Dict[str, Any],
                          boletas: List[Dict[str, Any]],
                          tipologia: str) -> Dict[str, Any]:
        """Análisis genérico para tipologías sin procedimiento específico"""
        return {
            'tipologia': tipologia,
            'procedimiento_aplicado': 'Genérico',
            'boletas_analizadas': len(boletas)
        }
    
    def _parsear_periodo(self, periodo: str) -> datetime:
        """Parsea período a datetime para ordenamiento"""
        try:
            # Intentar formato YYYY-MM
            return datetime.strptime(periodo, '%Y-%m')
        except ValueError:
            try:
                # Intentar formato MM/YYYY
                return datetime.strptime(periodo, '%m/%Y')
            except ValueError:
                # Valor por defecto
                return datetime(2000, 1, 1)
    
    def _obtener_periodo_espejo(self, periodo: str) -> str:
        """Obtiene el período espejo (mismo mes, año anterior)"""
        try:
            fecha = self._parsear_periodo(periodo)
            fecha_espejo = fecha - relativedelta(years=1)
            return fecha_espejo.strftime('%Y-%m')
        except:
            return ''
    
    def _obtener_consumo_periodo(self, boletas: List[Dict[str, Any]],
                                 periodo: str) -> Optional[float]:
        """Obtiene el consumo de un período específico"""
        for boleta in boletas:
            if boleta.get('periodo_facturacion') == periodo:
                return boleta.get('consumo_kwh')
        return None
    
    def _obtener_promedio_periodo_espejo(self, boletas: List[Dict[str, Any]],
                                         periodo_reclamado: str) -> Optional[float]:
        """
        Obtiene promedio de consumo del período espejo
        Según manual: si es un mes, comparar con promedio de mes anterior, mismo mes y mes posterior del año anterior
        """
        try:
            fecha = self._parsear_periodo(periodo_reclamado)
            fecha_espejo = fecha - relativedelta(years=1)
            
            # Mes anterior, mismo mes, mes posterior
            periodos = [
                (fecha_espejo - relativedelta(months=1)).strftime('%Y-%m'),
                fecha_espejo.strftime('%Y-%m'),
                (fecha_espejo + relativedelta(months=1)).strftime('%Y-%m')
            ]
            
            consumos = []
            for periodo in periodos:
                consumo = self._obtener_consumo_periodo(boletas, periodo)
                if consumo:
                    consumos.append(consumo)
            
            if consumos:
                return sum(consumos) / len(consumos)
            
            return None
        except:
            return None

