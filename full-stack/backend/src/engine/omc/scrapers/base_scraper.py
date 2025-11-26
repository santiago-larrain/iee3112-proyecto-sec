"""
Interfaz abstracta para scrapers de portales PIP
Patrón Strategy: Cada empresa implementa su propio scraper
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """
    Interfaz base para scrapers de portales PIP (Plataforma de Información Pública)
    Cada empresa distribuidora debe implementar su propio scraper
    """
    
    def __init__(self, company_name: str):
        """
        Inicializa el scraper
        
        Args:
            company_name: Nombre de la empresa (ej: "ENEL", "CGE")
        """
        self.company_name = company_name
        self.credentials_valid = False
    
    @abstractmethod
    def validate_credentials(self) -> bool:
        """
        Valida las credenciales necesarias para acceder al portal
        
        Returns:
            True si las credenciales son válidas, False en caso contrario
        """
        pass
    
    @abstractmethod
    def get_available_periods(self, nis: str) -> List[Dict[str, Any]]:
        """
        Obtiene los períodos disponibles para un NIS dado
        
        Args:
            nis: Número de Identificación del Suministro
            
        Returns:
            Lista de períodos disponibles con formato:
            [{"period": "2023-05", "available": True}, ...]
        """
        pass
    
    @abstractmethod
    def download_boleta(self, nis: str, period: str, output_path: Path) -> Optional[Path]:
        """
        Descarga una boleta específica para un NIS y período
        
        Args:
            nis: Número de Identificación del Suministro
            period: Período en formato "YYYY-MM"
            output_path: Ruta donde guardar el PDF descargado
            
        Returns:
            Path al archivo descargado si tiene éxito, None en caso contrario
        """
        pass
    
    def download_multiple_boletas(
        self, 
        nis: str, 
        periods: List[str], 
        output_dir: Path
    ) -> List[Path]:
        """
        Descarga múltiples boletas para un NIS
        
        Args:
            nis: Número de Identificación del Suministro
            periods: Lista de períodos a descargar
            output_dir: Directorio donde guardar los PDFs
            
        Returns:
            Lista de paths a los archivos descargados exitosamente
        """
        downloaded_files = []
        
        for period in periods:
            try:
                output_path = output_dir / f"boleta_{nis}_{period}.pdf"
                downloaded = self.download_boleta(nis, period, output_path)
                if downloaded:
                    downloaded_files.append(downloaded)
            except Exception as e:
                logger.warning(f"Error descargando boleta {period} para NIS {nis}: {e}")
                continue
        
        return downloaded_files

