"""
Extractor de entidades (RUT, NIS, direcciones, montos) con soporte para información de posición
"""

import re
from typing import Dict, List, Optional, Any
from pathlib import Path

class EntityExtractor:
    """Extrae entidades maestras de documentos"""
    
    # Patrón RUT chileno: XX.XXX.XXX-X o X.XXX.XXX-X
    RUT_PATTERN = re.compile(r'\b\d{1,2}\.\d{3}\.\d{3}-[\dkK]\b')
    
    # Patrón para montos en CLP
    MONTO_PATTERN = re.compile(r'\$?\s*(\d{1,3}(?:\.\d{3})*(?:,\d+)?)')
    
    # Patrón para NIS/Número de Cliente
    NIS_PATTERN = re.compile(r'(?:nis|nis|cliente\s*n[°º]|n[°º]\s*cliente|numero\s*cliente)[\s:]*(\d{4,10})', re.IGNORECASE)
    
    # Patrón para direcciones
    DIRECCION_PATTERN = re.compile(r'(?:av\.?|avenida|calle|pasaje|pje\.?|camino)\s+[^,\n]+(?:,\s*[^,\n]+)?', re.IGNORECASE)
    
    # Patrones para comunas comunes
    COMUNA_PATTERN = re.compile(r'\b(?:providencia|las condes|vitacura|ñuñoa|maipú|maipu|santiago|puente alto|la florida|san bernardo)\b', re.IGNORECASE)
    
    def extract_rut(self, text: str) -> Optional[str]:
        """
        Extrae RUT del texto
        
        Args:
            text: Texto a analizar
            
        Returns:
            RUT normalizado o None
        """
        matches = self.RUT_PATTERN.findall(text)
        if matches:
            # Normalizar formato
            rut = matches[0].replace(' ', '')
            return rut
        return None
    
    def extract_nis(self, text: str, file_path: Optional[Path] = None) -> Optional[str]:
        """
        Extrae NIS/Número de Cliente
        
        Args:
            text: Texto a analizar
            file_path: Ruta del archivo (para buscar en nombre)
            
        Returns:
            NIS encontrado o None
        """
        # Buscar en nombre de archivo primero
        if file_path:
            file_name = file_path.name
            # Buscar patrones como "NIS 123456" o "cliente N°123456"
            nis_match = re.search(r'(?:nis|cliente\s*n[°º]?)\s*(\d{4,10})', file_name, re.IGNORECASE)
            if nis_match:
                return nis_match.group(1)
            
            # Buscar números grandes en nombre de archivo
            numbers = re.findall(r'\d{6,10}', file_name)
            if numbers:
                return numbers[0]
        
        # Buscar en contenido
        matches = self.NIS_PATTERN.findall(text)
        if matches:
            return matches[0]
        
        # Buscar números grandes en el texto
        numbers = re.findall(r'\b\d{6,10}\b', text)
        if numbers:
            return numbers[0]
        
        return None
    
    def extract_address(self, text: str) -> Optional[str]:
        """
        Extrae dirección del texto
        
        Args:
            text: Texto a analizar
            
        Returns:
            Dirección encontrada o None
        """
        matches = self.DIRECCION_PATTERN.findall(text)
        if matches:
            # Tomar la primera dirección encontrada
            return matches[0].strip()
        return None
    
    def extract_commune(self, text: str) -> Optional[str]:
        """
        Extrae comuna del texto
        
        Args:
            text: Texto a analizar
            
        Returns:
            Comuna encontrada o None
        """
        matches = self.COMUNA_PATTERN.findall(text)
        if matches:
            # Capitalizar primera letra
            comuna = matches[0].title()
            # Normalizar
            if comuna.lower() == 'maipu':
                comuna = 'Maipú'
            return comuna
        return None
    
    def extract_amounts(self, text: str) -> List[float]:
        """
        Extrae montos del texto
        
        Args:
            text: Texto a analizar
            
        Returns:
            Lista de montos encontrados
        """
        amounts = []
        matches = self.MONTO_PATTERN.findall(text)
        
        for match in matches:
            try:
                # Limpiar formato (remover puntos de miles, convertir coma a punto)
                amount_str = match.replace('.', '').replace(',', '.')
                amount = float(amount_str)
                # Filtrar montos razonables (mayores a 1000 CLP)
                if amount > 1000:
                    amounts.append(amount)
            except ValueError:
                continue
        
        return amounts
    
    def extract_all(self, text: str, file_path: Optional[Path] = None, 
                   positions_data: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Extrae todas las entidades del texto
        
        Args:
            text: Texto a analizar
            file_path: Ruta del archivo
            positions_data: Lista de datos de posición por página (de PDFExtractor)
            
        Returns:
            Diccionario con todas las entidades encontradas, incluyendo source si hay positions_data
        """
        entities = {
            'rut': self.extract_rut(text),
            'nis': self.extract_nis(text, file_path),
            'address': self.extract_address(text),
            'commune': self.extract_commune(text),
            'amounts': self.extract_amounts(text)
        }
        
        # Si hay información de posición, agregar source a las entidades encontradas
        if positions_data and file_path:
            file_id = str(file_path)  # Por ahora, usar path como referencia
            # Buscar posición de RUT si existe
            if entities['rut'] and positions_data:
                rut_source = self._find_entity_position(entities['rut'], positions_data, file_id)
                if rut_source:
                    entities['rut_source'] = rut_source
            
            # Buscar posición de montos si existen
            if entities['amounts'] and positions_data:
                amounts_with_source = []
                for amount in entities['amounts']:
                    amount_str = str(amount)
                    amount_source = self._find_entity_position(amount_str, positions_data, file_id)
                    amounts_with_source.append({
                        'value': amount,
                        'source': amount_source
                    })
                entities['amounts'] = amounts_with_source
        
        return entities
    
    def _find_entity_position(self, entity_value: str, positions_data: List[Dict], 
                              file_ref: str) -> Optional[Dict]:
        """
        Busca la posición (bbox) de una entidad en los datos de posición
        
        Args:
            entity_value: Valor de la entidad a buscar
            positions_data: Datos de posición por página
            file_ref: Referencia al archivo
            
        Returns:
            Diccionario con source reference o None
        """
        if not positions_data:
            return None
        
        entity_str = str(entity_value)
        # Buscar en cada página
        for page_data in positions_data:
            page_index = page_data.get('page_index', 0)
            words = page_data.get('words', [])
            
            # Buscar palabra que contenga el valor
            for word in words:
                word_text = word.get('text', '')
                if entity_str in word_text or word_text in entity_str:
                    bbox = word.get('bbox', [])
                    if bbox and len(bbox) >= 4:
                        return {
                            'file_ref': file_ref,
                            'page_index': page_index,
                            'coordinates': bbox  # [x0, y0, x1, y1]
                        }
        
        return None

