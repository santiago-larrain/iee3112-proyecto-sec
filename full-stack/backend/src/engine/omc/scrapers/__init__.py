"""
Módulo de Scrapers para Enriquecimiento Externo
Implementa patrón Strategy para descargar boletas desde portales PIP
"""

from .base_scraper import BaseScraper
from .pip_manager import PIPManager

__all__ = [
    'BaseScraper',
    'PIPManager'
]

