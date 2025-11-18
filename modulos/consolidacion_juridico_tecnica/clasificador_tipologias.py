"""
Clasificador de tipologías de reclamos según Manual SEC 2025
"""

import re
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from modulos.utils.logger import Logger
from modulos.utils.config import Config


class ClasificadorTipologias:
    """Clasifica reclamos según las tipologías del Manual SEC 2025"""
    
    # Tipologías según Manual
    TIPOLOGIAS = {
        'facturacion_excesiva': {
            'codigo': 'Anexo N°1',
            'nombre': 'Facturación Excesiva',
            'keywords': ['facturación excesiva', 'cobro excesivo', 'consumo excesivo',
                        'aumento consumo', 'factura alta', 'cobro alto', 'demasiado consumo']
        },
        'error_lectura': {
            'codigo': 'Anexo N°1.1',
            'nombre': 'Error de Lectura',
            'keywords': ['error lectura', 'lectura incorrecta', 'medición incorrecta',
                        'lectura errónea', 'medidor mal leído']
        },
        'facturacion_provisoria': {
            'codigo': 'Anexo N°2',
            'nombre': 'Facturación Provisoria',
            'keywords': ['facturación provisoria', 'factura provisoria', 'consumo provisorio',
                        'lectura provisoria', 'promedio', 'estimado']
        },
        'cobros_indebidos': {
            'codigo': 'Anexo N°3',
            'nombre': 'Cobros Indebidos',
            'keywords': ['cobro indebido', 'cargo indebido', 'cobro no corresponde',
                        'cargo incorrecto', 'cobro sin justificación']
        },
        'atencion_comercial': {
            'codigo': 'Anexo N°4',
            'nombre': 'Atención Comercial',
            'keywords': ['mala atención', 'atención deficiente', 'trato inadecuado',
                        'demora atención', 'problema atención', 'servicio cliente']
        },
        'calidad_suministro': {
            'codigo': 'Anexo N°5',
            'nombre': 'Calidad de Suministro',
            'keywords': ['corte luz', 'interrupción', 'cortes reiterados', 'variación voltaje',
                        'daño artefacto', 'calidad servicio', 'suministro deficiente']
        },
        'no_cumplimiento_instruccion': {
            'codigo': 'Anexo N°6',
            'nombre': 'No Cumplimiento de Instrucción',
            'keywords': ['no cumplió', 'incumplimiento', 'no siguió instrucción',
                        'no ejecutó', 'no realizó']
        },
        'cnr': {
            'codigo': 'Resolución 1952',
            'nombre': 'Consumos No Registrados',
            'keywords': ['consumo no registrado', 'cnr', 'consumo erróneo',
                        'medición no registrada', 'consumo sin medir']
        }
    }
    
    def __init__(self, config: Optional[Config] = None, logger: Optional[Logger] = None):
        """
        Inicializa el clasificador
        
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
        self._cargar_manual()
    
    def _cargar_manual(self):
        """Carga el manual de reclamos desde JSON"""
        try:
            root_dir = Path(__file__).parent.parent.parent
            manual_path = root_dir / 'docs' / 'manual_reclamos_2025.json'
            
            if manual_path.exists():
                with open(manual_path, 'r', encoding='utf-8') as f:
                    self.manual = json.load(f)
            else:
                self.manual = {}
                self.logger.warning("Manual de reclamos no encontrado, usando clasificación por keywords")
        except Exception as e:
            self.logger.error(f"Error al cargar manual: {str(e)}")
            self.manual = {}
    
    def clasificar(self, reclamo: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clasifica un reclamo según su contenido
        
        Args:
            reclamo: Diccionario con datos del reclamo
                - 'descripcion': Texto del reclamo
                - 'numero_cliente': Número de cliente
                - 'distribuidora': Nombre de la distribuidora
                - 'fecha_ingreso': Fecha de ingreso
                
        Returns:
            Diccionario con clasificación:
            {
                'tipologia_principal': str,
                'tipologias_secundarias': List[str],
                'confianza': float,
                'razon': str
            }
        """
        descripcion = reclamo.get('descripcion', '').lower()
        titulo = reclamo.get('titulo', '').lower()
        texto_completo = f"{titulo} {descripcion}"
        
        self.logger.info(f"Clasificando reclamo: {reclamo.get('numero_reclamo', 'N/A')}")
        
        # Calcular puntuación para cada tipología
        puntuaciones = {}
        
        for tipologia_id, info in self.TIPOLOGIAS.items():
            puntuacion = self._calcular_puntuacion(texto_completo, info['keywords'])
            if puntuacion > 0:
                puntuaciones[tipologia_id] = puntuacion
        
        # Ordenar por puntuación
        tipologias_ordenadas = sorted(
            puntuaciones.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        if not tipologias_ordenadas:
            # Si no hay coincidencias, usar reglas adicionales
            tipologia_principal = self._clasificar_por_reglas(reclamo)
            return {
                'tipologia_principal': tipologia_principal,
                'tipologias_secundarias': [],
                'confianza': 0.3,
                'razon': 'Clasificación por reglas heurísticas (baja confianza)'
            }
        
        # Tipología principal (mayor puntuación)
        tipologia_principal_id = tipologias_ordenadas[0][0]
        confianza_principal = tipologias_ordenadas[0][1]
        
        # Tipologías secundarias (puntuación > 0.3)
        tipologias_secundarias = [
            tip_id for tip_id, punt in tipologias_ordenadas[1:]
            if punt > 0.3
        ]
        
        # Normalizar confianza (0-1)
        confianza = min(1.0, confianza_principal / 10.0)
        
        razon = f"Coincidencias encontradas con keywords de '{self.TIPOLOGIAS[tipologia_principal_id]['nombre']}'"
        
        return {
            'tipologia_principal': tipologia_principal_id,
            'tipologias_secundarias': tipologias_secundarias,
            'confianza': confianza,
            'razon': razon
        }
    
    def _calcular_puntuacion(self, texto: str, keywords: List[str]) -> float:
        """
        Calcula puntuación de coincidencia con keywords
        
        Args:
            texto: Texto a analizar
            keywords: Lista de palabras clave
            
        Returns:
            Puntuación (0-10)
        """
        puntuacion = 0.0
        
        for keyword in keywords:
            # Buscar coincidencias exactas
            coincidencias = len(re.findall(r'\b' + re.escape(keyword) + r'\b', texto, re.IGNORECASE))
            if coincidencias > 0:
                puntuacion += coincidencias * 2.0
            
            # Buscar coincidencias parciales
            if keyword in texto:
                puntuacion += 1.0
        
        return min(10.0, puntuacion)
    
    def _clasificar_por_reglas(self, reclamo: Dict[str, Any]) -> str:
        """
        Clasifica usando reglas heurísticas cuando no hay keywords
        
        Args:
            reclamo: Datos del reclamo
            
        Returns:
            ID de tipología más probable
        """
        descripcion = reclamo.get('descripcion', '').lower()
        
        # Reglas específicas
        if 'factura' in descripcion and ('alto' in descripcion or 'mucho' in descripcion):
            return 'facturacion_excesiva'
        
        if 'lectura' in descripcion and ('mal' in descripcion or 'incorrect' in descripcion):
            return 'error_lectura'
        
        if 'promedio' in descripcion or 'estimado' in descripcion:
            return 'facturacion_provisoria'
        
        if 'cobro' in descripcion and ('no corresponde' in descripcion or 'indebido' in descripcion):
            return 'cobros_indebidos'
        
        if 'atención' in descripcion or 'trato' in descripcion:
            return 'atencion_comercial'
        
        if 'corte' in descripcion or 'luz' in descripcion or 'suministro' in descripcion:
            return 'calidad_suministro'
        
        # Por defecto: atención comercial (más genérica)
        return 'atencion_comercial'
    
    def obtener_info_tipologia(self, tipologia_id: str) -> Dict[str, Any]:
        """
        Obtiene información de una tipología
        
        Args:
            tipologia_id: ID de la tipología
            
        Returns:
            Diccionario con información de la tipología
        """
        return self.TIPOLOGIAS.get(tipologia_id, {})
    
    def listar_tipologias(self) -> List[Dict[str, Any]]:
        """
        Lista todas las tipologías disponibles
        
        Returns:
            Lista de diccionarios con información de tipologías
        """
        return [
            {'id': tip_id, **info}
            for tip_id, info in self.TIPOLOGIAS.items()
        ]

