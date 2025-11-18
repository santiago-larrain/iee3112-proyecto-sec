"""
Gestión de configuración del sistema
"""

import os
import yaml
from typing import Any, Dict, Optional
from pathlib import Path


class Config:
    """Gestor de configuración del sistema"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializa el gestor de configuración
        
        Args:
            config_path: Ruta al archivo de configuración. Si es None, busca config.yaml
        """
        if config_path is None:
            # Buscar config.yaml en la raíz del proyecto
            root_dir = Path(__file__).parent.parent.parent
            config_path = root_dir / "config" / "config.yaml"
        
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._cargar_configuracion()
    
    def _cargar_configuracion(self):
        """Carga la configuración desde archivo y variables de entorno"""
        # Cargar desde archivo si existe
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
        else:
            self._config = {}
        
        # Variables de entorno tienen prioridad
        self._cargar_variables_entorno()
    
    def _cargar_variables_entorno(self):
        """Carga configuración desde variables de entorno"""
        # Base de datos
        if os.getenv('DB_HOST'):
            self._config.setdefault('base_datos', {})['host'] = os.getenv('DB_HOST')
        if os.getenv('DB_PORT'):
            self._config.setdefault('base_datos', {})['port'] = int(os.getenv('DB_PORT'))
        if os.getenv('DB_NAME'):
            self._config.setdefault('base_datos', {})['nombre'] = os.getenv('DB_NAME')
        if os.getenv('DB_USER'):
            self._config.setdefault('base_datos', {})['usuario'] = os.getenv('DB_USER')
        if os.getenv('DB_PASSWORD'):
            self._config.setdefault('base_datos', {})['password'] = os.getenv('DB_PASSWORD')
        
        # Logging
        if os.getenv('LOG_LEVEL'):
            self._config.setdefault('logging', {})['nivel'] = os.getenv('LOG_LEVEL')
        if os.getenv('LOG_FILE'):
            self._config.setdefault('logging', {})['archivo'] = os.getenv('LOG_FILE')
        
        # Scraping
        if os.getenv('SCRAPER_TIMEOUT'):
            self._config.setdefault('scraping', {})['timeout'] = int(os.getenv('SCRAPER_TIMEOUT'))
        if os.getenv('SCRAPER_RETRY'):
            self._config.setdefault('scraping', {})['max_reintentos'] = int(os.getenv('SCRAPER_RETRY'))
    
    def get(self, clave: str, valor_default: Any = None) -> Any:
        """
        Obtiene un valor de configuración usando notación de puntos
        
        Args:
            clave: Clave de configuración (ej: 'base_datos.host')
            valor_default: Valor por defecto si no existe
            
        Returns:
            Valor de configuración o valor por defecto
        """
        keys = clave.split('.')
        valor = self._config
        
        for key in keys:
            if isinstance(valor, dict) and key in valor:
                valor = valor[key]
            else:
                return valor_default
        
        return valor
    
    def set(self, clave: str, valor: Any):
        """
        Establece un valor de configuración
        
        Args:
            clave: Clave de configuración (ej: 'base_datos.host')
            valor: Valor a establecer
        """
        keys = clave.split('.')
        config = self._config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = valor
    
    def get_base_datos(self) -> Dict[str, Any]:
        """Obtiene configuración de base de datos"""
        return self.get('base_datos', {
            'tipo': 'sqlite',
            'nombre': 'sec_reclamos.db',
            'host': 'localhost',
            'port': 5432,
            'usuario': '',
            'password': ''
        })
    
    def get_logging(self) -> Dict[str, Any]:
        """Obtiene configuración de logging"""
        return self.get('logging', {
            'nivel': 'INFO',
            'archivo': 'logs/sec_reclamos.log',
            'formato': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        })
    
    def get_scraping(self) -> Dict[str, Any]:
        """Obtiene configuración de scraping"""
        return self.get('scraping', {
            'timeout': 30,
            'max_reintentos': 3,
            'delay_entre_peticiones': 2,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_rutas(self) -> Dict[str, str]:
        """Obtiene rutas de directorios"""
        root_dir = Path(__file__).parent.parent.parent
        return {
            'raiz': str(root_dir),
            'data': str(root_dir / 'data'),
            'boletas': str(root_dir / 'data' / 'boletas'),
            'expedientes': str(root_dir / 'data' / 'expedientes'),
            'cache': str(root_dir / 'data' / 'cache'),
            'logs': str(root_dir / 'logs')
        }

