"""
Extractor de texto de archivos PDF con soporte para información de posición
"""

import pdfplumber
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
import logging

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extrae texto de archivos PDF usando pdfplumber"""
    
    def extract_text(self, file_path: Path, include_positions: bool = False) -> Union[Optional[str], Optional[List[Dict]]]:
        """
        Extrae texto de un archivo PDF
        
        Args:
            file_path: Ruta al archivo PDF
            include_positions: Si True, retorna texto con información de posición (bbox)
            
        Returns:
            Si include_positions=False: Texto extraído o None
            Si include_positions=True: Lista de dicts con texto y bbox por página
        """
        try:
            if not include_positions:
                # Modo simple: solo texto
                text_parts = []
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                
                return "\n\n".join(text_parts) if text_parts else None
            else:
                # Modo avanzado: texto con posiciones
                pages_data = []
                with pdfplumber.open(file_path) as pdf:
                    for page_num, page in enumerate(pdf.pages):
                        # Extraer texto con palabras y sus posiciones
                        words = page.extract_words()
                        chars = page.chars
                        
                        # Construir texto completo
                        page_text = page.extract_text() or ""
                        
                        # Extraer bounding boxes de palabras clave
                        word_bboxes = []
                        for word in words:
                            word_bboxes.append({
                                'text': word.get('text', ''),
                                'bbox': [word.get('x0', 0), word.get('top', 0), 
                                        word.get('x1', 0), word.get('bottom', 0)]
                            })
                        
                        pages_data.append({
                            'page_index': page_num,
                            'text': page_text,
                            'words': word_bboxes,
                            'chars': chars  # Para bbox más precisos si se necesita
                        })
                
                return pages_data if pages_data else None
            
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

