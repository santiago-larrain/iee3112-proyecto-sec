"""
Factory para crear scrapers según la distribuidora
"""

from typing import Optional
from modulos.utils.config import Config
from modulos.utils.logger import Logger

from .enel_scraper import EnelScraper


class ScraperFactory:
    """Factory para crear instancias de scrapers"""
    
    _scrapers_disponibles = {
        'enel': EnelScraper,
        # Agregar más scrapers aquí cuando se implementen
        # 'cge': CGEScraper,
        # 'saesa': SaesaScraper,
    }
    
    def __init__(self, config: Optional[Config] = None, logger: Optional[Logger] = None):
        """
        Inicializa el factory
        
        Args:
            config: Instancia de Config
            logger: Instancia de Logger
        """
        if config is None:
            config = Config()
        if logger is None:
            logger = Logger(config)
        
        self.config = config
        self.logger = logger
    
    def crear_scraper(self, distribuidora: str):
        """
        Crea un scraper para la distribuidora especificada
        
        Args:
            distribuidora: Nombre de la distribuidora (en minúsculas)
            
        Returns:
            Instancia del scraper correspondiente
            
        Raises:
            ValueError: Si la distribuidora no está soportada
        """
        distribuidora_lower = distribuidora.lower()
        
        if distribuidora_lower not in self._scrapers_disponibles:
            distribuidoras = ', '.join(self._scrapers_disponibles.keys())
            raise ValueError(
                f"Distribuidora '{distribuidora}' no soportada. "
                f"Distribuidoras disponibles: {distribuidoras}"
            )
        
        scraper_class = self._scrapers_disponibles[distribuidora_lower]
        return scraper_class(config=self.config, logger=self.logger)
    
    def listar_distribuidoras(self) -> list:
        """
        Lista las distribuidoras soportadas
        
        Returns:
            Lista de nombres de distribuidoras
        """
        return list(self._scrapers_disponibles.keys())
    
    def registrar_scraper(self, nombre: str, scraper_class):
        """
        Registra un nuevo scraper
        
        Args:
            nombre: Nombre de la distribuidora (en minúsculas)
            scraper_class: Clase del scraper (debe heredar de ScraperBase)
        """
        self._scrapers_disponibles[nombre.lower()] = scraper_class
        self.logger.info(f"Scraper '{nombre}' registrado exitosamente")

