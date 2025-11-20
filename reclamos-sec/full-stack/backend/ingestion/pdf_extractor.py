"""
Extractor de texto de archivos PDF
"""

import pdfplumber
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extrae texto de archivos PDF usando pdfplumber"""
    
    def extract_text(self, file_path: Path) -> Optional[str]:
        """
        Extrae texto de un archivo PDF
        
        Args:
            file_path: Ruta al archivo PDF
            
        Returns:
            Texto extraído o None si hay error
        """
        try:
            text_parts = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            
            return "\n\n".join(text_parts) if text_parts else None
            
        except Exception as e:
            logger.error(f"Error extrayendo texto de PDF {file_path}: {e}")
            return None
    
    def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extrae metadatos básicos del PDF
        
        Args:
            file_path: Ruta al archivo PDF
            
        Returns:
            Diccionario con metadatos
        """
        metadata = {
            "file_name": file_path.name,
            "file_size": file_path.stat().st_size,
            "num_pages": 0
        }
        
        try:
            with pdfplumber.open(file_path) as pdf:
                metadata["num_pages"] = len(pdf.pages)
        except Exception as e:
            logger.warning(f"Error obteniendo metadatos de PDF {file_path}: {e}")
        
        return metadata

