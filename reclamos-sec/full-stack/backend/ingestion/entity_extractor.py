"""
Extractor de entidades (RUT, NIS, direcciones, montos)
"""

import re
from typing import Dict, List, Optional
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
    
    def extract_all(self, text: str, file_path: Optional[Path] = None) -> Dict[str, any]:
        """
        Extrae todas las entidades del texto
        
        Args:
            text: Texto a analizar
            file_path: Ruta del archivo
            
        Returns:
            Diccionario con todas las entidades encontradas
        """
        return {
            'rut': self.extract_rut(text),
            'nis': self.extract_nis(text, file_path),
            'address': self.extract_address(text),
            'commune': self.extract_commune(text),
            'amounts': self.extract_amounts(text)
        }

