"""
Orquestador principal para enriquecimiento externo vía scraping
Coordina múltiples scrapers según la empresa detectada
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class PIPManager:
    """
    Manager que coordina la descarga de boletas desde portales PIP
    Selecciona el scraper apropiado según la empresa y maneja errores silenciosamente
    """
    
    def __init__(self):
        """Inicializa el manager con registro de scrapers"""
        self.scrapers: Dict[str, BaseScraper] = {}
        self._register_scrapers()
    
    def _register_scrapers(self):
        """
        Registra los scrapers disponibles
        Por ahora, implementaciones placeholder que deben ser completadas
        """
        # TODO: Implementar scrapers específicos cuando estén disponibles
        # from .pip_enel_scraper import ENELScraper
        # from .pip_cge_scraper import CGEScraper
        # self.scrapers['ENEL'] = ENELScraper()
        # self.scrapers['CGE'] = CGEScraper()
        
        logger.info("Scrapers registrados: Ninguno (implementaciones pendientes)")
    
    def register_scraper(self, company_name: str, scraper: BaseScraper):
        """
        Registra un scraper para una empresa
        
        Args:
            company_name: Nombre de la empresa (ej: "ENEL")
            scraper: Instancia del scraper
        """
        self.scrapers[company_name.upper()] = scraper
        logger.info(f"Scraper registrado para {company_name}")
    
    def enrich_case(
        self, 
        company: str, 
        nis: str, 
        output_dir: Path,
        periods: Optional[List[str]] = None
    ) -> List[Path]:
        """
        Enriquece un caso descargando boletas oficiales desde el portal PIP
        
        Args:
            company: Nombre de la empresa distribuidora
            nis: Número de Identificación del Suministro
            output_dir: Directorio donde guardar los PDFs descargados
            periods: Lista de períodos a descargar (opcional, si None descarga últimos 12 meses)
            
        Returns:
            Lista de paths a los archivos descargados exitosamente
        """
        if not company or not nis:
            logger.warning("Company o NIS no proporcionados, saltando enriquecimiento")
            return []
        
        company_upper = company.upper()
        
        # Buscar scraper para esta empresa
        scraper = self.scrapers.get(company_upper)
        
        if not scraper:
            logger.warning(f"No hay scraper disponible para empresa {company}, saltando enriquecimiento")
            return []
        
        # Validar credenciales
        try:
            if not scraper.validate_credentials():
                logger.warning(f"Credenciales inválidas para scraper de {company}, saltando enriquecimiento")
                return []
        except Exception as e:
            logger.warning(f"Error validando credenciales para {company}: {e}, saltando enriquecimiento")
            return []
        
        # Obtener períodos disponibles si no se especificaron
        if not periods:
            try:
                available_periods = scraper.get_available_periods(nis)
                periods = [p['period'] for p in available_periods if p.get('available', False)]
                # Limitar a últimos 12 meses
                periods = periods[:12]
            except Exception as e:
                logger.warning(f"Error obteniendo períodos disponibles para NIS {nis}: {e}")
                return []
        
        # Descargar boletas
        try:
            downloaded_files = scraper.download_multiple_boletas(nis, periods, output_dir)
            logger.info(f"Descargadas {len(downloaded_files)} boletas para NIS {nis} de {company}")
            return downloaded_files
        except Exception as e:
            logger.warning(f"Error descargando boletas para NIS {nis} de {company}: {e}")
            return []
    
    def has_scraper_for_company(self, company: str) -> bool:
        """
        Verifica si hay un scraper disponible para una empresa
        
        Args:
            company: Nombre de la empresa
            
        Returns:
            True si hay scraper disponible, False en caso contrario
        """
        return company.upper() in self.scrapers

