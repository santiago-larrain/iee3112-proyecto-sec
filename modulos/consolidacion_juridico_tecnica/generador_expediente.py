"""
Generador de expedientes según formato SEC
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from modulos.utils.logger import Logger
from modulos.utils.config import Config


class GeneradorExpediente:
    """Genera expedientes estructurados según formato SEC"""
    
    def __init__(self, config: Optional[Config] = None, logger: Optional[Logger] = None):
        """
        Inicializa el generador
        
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
    
    def generar(self, reclamo: Dict[str, Any], clasificacion: Dict[str, Any],
               analisis: Dict[str, Any], boletas: List[Dict[str, Any]],
               cumplimiento: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Genera un expediente completo
        
        Args:
            reclamo: Datos del reclamo
            clasificacion: Resultado de clasificación de tipologías
            analisis: Resultado del análisis del reclamo
            boletas: Lista de boletas
            cumplimiento: Resultado de evaluación de cumplimiento (opcional)
            
        Returns:
            Diccionario con expediente estructurado
        """
        # Validar que los parámetros no sean None
        if reclamo is None:
            reclamo = {}
        if clasificacion is None:
            clasificacion = {}
        if analisis is None:
            analisis = {}
        if boletas is None:
            boletas = []
        
        self.logger.info(f"Generando expediente para reclamo: {reclamo.get('numero_reclamo', 'N/A')}")
        
        expediente = {
            'metadata': {
                'numero_expediente': self._generar_numero_expediente(reclamo),
                'fecha_creacion': datetime.now().isoformat(),
                'version': '1.0'
            },
            'reclamo': {
                'numero_reclamo': reclamo.get('numero_reclamo'),
                'numero_cliente': reclamo.get('numero_cliente'),
                'distribuidora': reclamo.get('distribuidora'),
                'fecha_ingreso': reclamo.get('fecha_ingreso'),
                'descripcion': reclamo.get('descripcion'),
                'titulo': reclamo.get('titulo')
            },
            'clasificacion': {
                'tipologia_principal': clasificacion.get('tipologia_principal'),
                'tipologias_secundarias': clasificacion.get('tipologias_secundarias', []),
                'confianza': clasificacion.get('confianza'),
                'razon': clasificacion.get('razon')
            },
            'analisis': analisis,
            'boletas': boletas,
            'medios_probatorios': self._generar_medios_probatorios(analisis, boletas),
            'cumplimiento': cumplimiento or {},
            'resumen': self._generar_resumen(reclamo, clasificacion, analisis)
        }
        
        return expediente
    
    def guardar(self, expediente: Dict[str, Any], formato: str = 'json') -> str:
        """
        Guarda el expediente en archivo
        
        Args:
            expediente: Expediente a guardar
            formato: Formato de salida ('json' o 'txt')
            
        Returns:
            Ruta del archivo guardado
        """
        numero_expediente = expediente['metadata']['numero_expediente']
        fecha_creacion = expediente['metadata']['fecha_creacion'][:10]  # YYYY-MM-DD
        
        # Crear directorio si no existe
        dir_expedientes = Path(self.rutas['expedientes'])
        dir_expedientes.mkdir(parents=True, exist_ok=True)
        
        if formato == 'json':
            nombre_archivo = f"{numero_expediente}_{fecha_creacion}.json"
            ruta_archivo = dir_expedientes / nombre_archivo
            
            with open(ruta_archivo, 'w', encoding='utf-8') as f:
                json.dump(expediente, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Expediente guardado: {ruta_archivo}")
            return str(ruta_archivo)
        
        elif formato == 'txt':
            nombre_archivo = f"{numero_expediente}_{fecha_creacion}.txt"
            ruta_archivo = dir_expedientes / nombre_archivo
            
            with open(ruta_archivo, 'w', encoding='utf-8') as f:
                f.write(self._formatear_texto(expediente))
            
            self.logger.info(f"Expediente guardado: {ruta_archivo}")
            return str(ruta_archivo)
        
        else:
            raise ValueError(f"Formato no soportado: {formato}")
    
    def _generar_numero_expediente(self, reclamo: Dict[str, Any]) -> str:
        """Genera número único de expediente"""
        numero_reclamo = reclamo.get('numero_reclamo', 'SIN_NUMERO')
        fecha = datetime.now().strftime('%Y%m%d')
        return f"EXP-{numero_reclamo}-{fecha}"
    
    def _generar_medios_probatorios(self, analisis: Dict[str, Any],
                                    boletas: List[Dict[str, Any]]) -> List[str]:
        """
        Genera lista de medios probatorios presentes
        
        Args:
            analisis: Resultado del análisis
            boletas: Lista de boletas
            
        Returns:
            Lista de medios probatorios identificados
        """
        medios = []
        
        # Validar que analisis no sea None
        if analisis is None:
            analisis = {}
        if boletas is None:
            boletas = []
        
        # Historial de consumo
        if boletas:
            medios.append(f"Historial de consumo ({len(boletas)} boletas)")
        
        # Cartola de consumo
        if any(b.get('consumo_kwh') for b in boletas):
            medios.append("Cartola de consumo")
        
        # Informe de verificación (si aplica)
        causa_raiz = analisis.get('causa_raiz')
        if causa_raiz and isinstance(causa_raiz, dict) and causa_raiz.get('tipo') == 'problema_medidor':
            medios.append("Informe de verificación de medidor")
        
        # Carta respuesta (siempre presente en expediente generado)
        medios.append("Carta respuesta")
        
        return medios
    
    def _generar_resumen(self, reclamo: Dict[str, Any], clasificacion: Dict[str, Any],
                        analisis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera resumen ejecutivo del expediente
        
        Args:
            reclamo: Datos del reclamo
            clasificacion: Clasificación de tipología
            analisis: Análisis realizado
            
        Returns:
            Diccionario con resumen
        """
        # Asegurar que analisis y clasificacion no sean None
        if analisis is None:
            analisis = {}
        if clasificacion is None:
            clasificacion = {}
        if reclamo is None:
            reclamo = {}
        
        return {
            'numero_reclamo': reclamo.get('numero_reclamo'),
            'cliente': reclamo.get('numero_cliente'),
            'distribuidora': reclamo.get('distribuidora'),
            'tipologia': clasificacion.get('tipologia_principal'),
            'confianza_clasificacion': clasificacion.get('confianza'),
            'conclusion_principal': analisis.get('conclusion', 'En análisis'),
            'recomendaciones': analisis.get('recomendaciones', []),
            'fecha_analisis': datetime.now().isoformat()
        }
    
    def _formatear_texto(self, expediente: Dict[str, Any]) -> str:
        """
        Formatea expediente como texto legible
        
        Args:
            expediente: Expediente a formatear
            
        Returns:
            Texto formateado
        """
        lines = []
        lines.append("=" * 80)
        lines.append("EXPEDIENTE SEC - ANÁLISIS DE RECLAMO")
        lines.append("=" * 80)
        lines.append("")
        
        # Metadata
        lines.append("METADATA")
        lines.append("-" * 80)
        lines.append(f"Número de Expediente: {expediente['metadata']['numero_expediente']}")
        lines.append(f"Fecha de Creación: {expediente['metadata']['fecha_creacion']}")
        lines.append("")
        
        # Reclamo
        lines.append("DATOS DEL RECLAMO")
        lines.append("-" * 80)
        reclamo = expediente['reclamo']
        lines.append(f"Número de Reclamo: {reclamo.get('numero_reclamo', 'N/A')}")
        lines.append(f"Número de Cliente: {reclamo.get('numero_cliente', 'N/A')}")
        lines.append(f"Distribuidora: {reclamo.get('distribuidora', 'N/A')}")
        lines.append(f"Fecha de Ingreso: {reclamo.get('fecha_ingreso', 'N/A')}")
        lines.append(f"Título: {reclamo.get('titulo', 'N/A')}")
        lines.append(f"Descripción: {reclamo.get('descripcion', 'N/A')[:200]}...")
        lines.append("")
        
        # Clasificación
        lines.append("CLASIFICACIÓN")
        lines.append("-" * 80)
        clasificacion = expediente['clasificacion']
        lines.append(f"Tipología Principal: {clasificacion.get('tipologia_principal', 'N/A')}")
        lines.append(f"Confianza: {clasificacion.get('confianza', 0):.2%}")
        lines.append(f"Razón: {clasificacion.get('razon', 'N/A')}")
        lines.append("")
        
        # Análisis
        lines.append("ANÁLISIS")
        lines.append("-" * 80)
        analisis = expediente.get('analisis', {})
        if analisis:
            lines.append(f"Procedimiento Aplicado: {analisis.get('procedimiento_aplicado', 'N/A')}")
            
            if 'analisis_consumo' in analisis and analisis['analisis_consumo']:
                consumo = analisis['analisis_consumo']
                if isinstance(consumo, dict):
                    lines.append(f"Consumo Reclamado: {consumo.get('consumo_reclamado', 'N/A')} kWh")
                    lines.append(f"Consumo Período Espejo: {consumo.get('consumo_espejo', 'N/A')} kWh")
                    lines.append(f"Supera 2x Período Espejo: {consumo.get('supera_2x_periodo_espejo', False)}")
            
            recomendaciones = analisis.get('recomendaciones')
            if recomendaciones:
                lines.append("Recomendaciones:")
                for rec in recomendaciones:
                    lines.append(f"  - {rec}")
        else:
            lines.append("Análisis no disponible")
        lines.append("")
        
        # Medios Probatorios
        lines.append("MEDIOS PROBATORIOS")
        lines.append("-" * 80)
        for medio in expediente.get('medios_probatorios', []):
            lines.append(f"  - {medio}")
        lines.append("")
        
        # Resumen
        lines.append("RESUMEN")
        lines.append("-" * 80)
        resumen = expediente.get('resumen', {})
        lines.append(f"Conclusión: {resumen.get('conclusion_principal', 'N/A')}")
        lines.append("")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)

