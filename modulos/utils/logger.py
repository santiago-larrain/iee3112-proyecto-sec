"""
Sistema de logging estructurado
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from .config import Config


class Logger:
    """Gestor de logging del sistema"""
    
    def __init__(self, config: Optional[Config] = None, nombre: str = 'SEC_Reclamos'):
        """
        Inicializa el logger
        
        Args:
            config: Instancia de Config. Si es None, crea una nueva
            nombre: Nombre del logger
        """
        if config is None:
            config = Config()
        
        self.config = config
        self.nombre = nombre
        self.logger = logging.getLogger(nombre)
        self._configurar_logger()
    
    def _configurar_logger(self):
        """Configura el logger según la configuración"""
        log_config = self.config.get_logging()
        nivel = getattr(logging, log_config.get('nivel', 'INFO').upper())
        
        self.logger.setLevel(nivel)
        
        # Evitar duplicación de handlers
        if self.logger.handlers:
            return
        
        # Formato
        formato = logging.Formatter(log_config.get('formato', 
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        
        # Handler para consola
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(nivel)
        console_handler.setFormatter(formato)
        self.logger.addHandler(console_handler)
        
        # Handler para archivo
        archivo_log = log_config.get('archivo')
        if archivo_log:
            # Crear directorio de logs si no existe
            log_path = Path(archivo_log)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(archivo_log, encoding='utf-8')
            file_handler.setLevel(nivel)
            file_handler.setFormatter(formato)
            self.logger.addHandler(file_handler)
    
    def debug(self, mensaje: str, **kwargs):
        """Registra mensaje de debug"""
        self.logger.debug(mensaje, **kwargs)
    
    def info(self, mensaje: str, **kwargs):
        """Registra mensaje informativo"""
        self.logger.info(mensaje, **kwargs)
    
    def warning(self, mensaje: str, **kwargs):
        """Registra advertencia"""
        self.logger.warning(mensaje, **kwargs)
    
    def error(self, mensaje: str, **kwargs):
        """Registra error"""
        self.logger.error(mensaje, **kwargs)
    
    def critical(self, mensaje: str, **kwargs):
        """Registra error crítico"""
        self.logger.critical(mensaje, **kwargs)
    
    def get_logger(self) -> logging.Logger:
        """Obtiene el logger de Python estándar"""
        return self.logger

