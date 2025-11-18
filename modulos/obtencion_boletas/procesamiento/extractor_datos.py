"""
Extractor de datos de boletas desde PDFs y HTML
"""

import re
from typing import Dict, Any, Optional, List
from pathlib import Path
import pdfplumber
from bs4 import BeautifulSoup

from modulos.utils.logger import Logger
from modulos.utils.config import Config


class ExtractorDatos:
    """Extractor de datos estructurados desde PDFs y HTML"""
    
    def __init__(self, config: Optional[Config] = None, logger: Optional[Logger] = None):
        """
        Inicializa el extractor
        
        Args:
            config: Instancia de Config
            logger: Instancia de Logger
        """
        if config is None:
            from modulos.utils.config import Config
            config = Config()
        if logger is None:
            from modulos.utils.logger import Logger
            logger = Logger(config)
        
        self.config = config
        self.logger = logger
    
    def extraer_desde_pdf(self, ruta_pdf: str) -> Dict[str, Any]:
        """
        Extrae datos de una boleta desde un archivo PDF
        
        Args:
            ruta_pdf: Ruta al archivo PDF
            
        Returns:
            Diccionario con datos extraídos
        """
        datos = {}
        
        try:
            self.logger.info(f"Extrayendo datos desde PDF: {ruta_pdf}")
            
            with pdfplumber.open(ruta_pdf) as pdf:
                texto_completo = ""
                
                # Extraer texto de todas las páginas
                for pagina in pdf.pages:
                    texto_pagina = pagina.extract_text()
                    if texto_pagina:
                        texto_completo += texto_pagina + "\n"
                
                # Extraer datos usando expresiones regulares
                datos = self._parsear_texto_boleta(texto_completo)
                
                # Intentar extraer tablas
                for pagina in pdf.pages:
                    tablas = pagina.extract_tables()
                    if tablas:
                        datos_tablas = self._parsear_tablas(tablas)
                        datos.update(datos_tablas)
            
            self.logger.info("Extracción desde PDF completada")
            return datos
            
        except Exception as e:
            self.logger.error(f"Error al extraer datos desde PDF: {str(e)}")
            return datos
    
    def extraer_desde_html(self, html: str) -> Dict[str, Any]:
        """
        Extrae datos de una boleta desde HTML
        
        Args:
            html: Contenido HTML
            
        Returns:
            Diccionario con datos extraídos
        """
        datos = {}
        
        try:
            self.logger.info("Extrayendo datos desde HTML")
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Buscar elementos comunes en boletas
            datos['numero_boleta'] = self._buscar_texto(soup, 
                ['numero-boleta', 'boleta-numero', 'factura-numero'])
            datos['numero_cliente'] = self._buscar_texto(soup,
                ['numero-cliente', 'cliente-numero', 'rut-cliente'])
            datos['periodo_facturacion'] = self._buscar_texto(soup,
                ['periodo', 'fecha-facturacion', 'mes-facturacion'])
            datos['direccion'] = self._buscar_texto(soup,
                ['direccion', 'domicilio', 'direccion-suministro'])
            
            # Buscar montos
            datos['monto_total'] = self._buscar_monto(soup,
                ['monto-total', 'total', 'total-pagar'])
            
            # Buscar lecturas
            datos['lectura_actual'] = self._buscar_lectura(soup,
                ['lectura-actual', 'lectura', 'medicion-actual'])
            datos['lectura_anterior'] = self._buscar_lectura(soup,
                ['lectura-anterior', 'lectura-prev', 'medicion-anterior'])
            
            # Calcular consumo si hay lecturas
            if datos.get('lectura_actual') and datos.get('lectura_anterior'):
                consumo = datos['lectura_actual'] - datos['lectura_anterior']
                datos['consumo_kwh'] = max(0, consumo)  # No permitir negativos
            
            # Buscar fecha de vencimiento
            datos['fecha_vencimiento'] = self._buscar_fecha(soup,
                ['vencimiento', 'fecha-vencimiento', 'vencimiento-pago'])
            
            self.logger.info("Extracción desde HTML completada")
            return datos
            
        except Exception as e:
            self.logger.error(f"Error al extraer datos desde HTML: {str(e)}")
            return datos
    
    def _parsear_texto_boleta(self, texto: str) -> Dict[str, Any]:
        """
        Parsea texto de boleta usando expresiones regulares
        
        Args:
            texto: Texto completo de la boleta
            
        Returns:
            Diccionario con datos extraídos
        """
        datos = {}
        
        # Patrones comunes en boletas chilenas
        patrones = {
            'numero_boleta': [
                r'[Nn]úmero\s+[Dd]e\s+[Bb]oleta[:\s]+(\d+)',
                r'[Bb]oleta\s+[Nn]°[:\s]+(\d+)',
                r'[Ff]actura\s+[Nn]°[:\s]+(\d+)',
            ],
            'numero_cliente': [
                r'[Nn]úmero\s+[Dd]e\s+[Cc]liente[:\s]+(\d+)',
                r'[Cc]liente[:\s]+(\d+)',
                r'[Rr]UT[:\s]+([\d\.\-]+)',
            ],
            'periodo_facturacion': [
                r'[Pp]eríodo[:\s]+([A-Za-z]+\s+\d{4})',
                r'[Mm]es[:\s]+([A-Za-z]+\s+\d{4})',
                r'(\d{2}/\d{4})',  # MM/YYYY
            ],
            'lectura_actual': [
                r'[Ll]ectura\s+[Aa]ctual[:\s]+([\d\.,]+)',
                r'[Ll]ectura[:\s]+([\d\.,]+)',
            ],
            'lectura_anterior': [
                r'[Ll]ectura\s+[Aa]nterior[:\s]+([\d\.,]+)',
                r'[Ll]ectura\s+[Pp]rev[:\s]+([\d\.,]+)',
            ],
            'consumo_kwh': [
                r'[Cc]onsumo[:\s]+([\d\.,]+)\s*k?wh',
                r'([\d\.,]+)\s*k?wh',
            ],
            'monto_total': [
                r'[Tt]otal\s+[Aa]\s+[Pp]agar[:\s]+\$?\s*([\d\.]+)',
                r'[Tt]otal[:\s]+\$?\s*([\d\.]+)',
                r'\$\s*([\d\.]+)\s*[Tt]otal',
            ],
            'fecha_vencimiento': [
                r'[Vv]encimiento[:\s]+(\d{2}/\d{2}/\d{4})',
                r'[Ff]echa\s+[Vv]encimiento[:\s]+(\d{2}/\d{2}/\d{4})',
            ],
        }
        
        for campo, lista_patrones in patrones.items():
            for patron in lista_patrones:
                match = re.search(patron, texto, re.IGNORECASE)
                if match:
                    valor = match.group(1).strip()
                    datos[campo] = self._normalizar_valor(campo, valor)
                    break
        
        return datos
    
    def _parsear_tablas(self, tablas: List[List]) -> Dict[str, Any]:
        """
        Parsea tablas extraídas del PDF
        
        Args:
            tablas: Lista de tablas (cada tabla es lista de filas)
            
        Returns:
            Diccionario con datos extraídos de tablas
        """
        datos = {}
        
        for tabla in tablas:
            for fila in tabla:
                if not fila or len(fila) < 2:
                    continue
                
                # Buscar patrones en las filas
                texto_fila = ' '.join([str(celda) for celda in fila if celda])
                
                # Detectar consumo
                if 'consumo' in texto_fila.lower() and 'kwh' in texto_fila.lower():
                    consumo = re.search(r'([\d\.,]+)', texto_fila)
                    if consumo:
                        datos['consumo_kwh'] = self._normalizar_valor('consumo_kwh', consumo.group(1))
                
                # Detectar montos
                if '$' in texto_fila or 'total' in texto_fila.lower():
                    monto = re.search(r'\$?\s*([\d\.]+)', texto_fila)
                    if monto:
                        datos['monto_total'] = self._normalizar_valor('monto_total', monto.group(1))
        
        return datos
    
    def _buscar_texto(self, soup: BeautifulSoup, clases: List[str]) -> Optional[str]:
        """Busca texto en elementos HTML por clase"""
        for clase in clases:
            elemento = soup.find(class_=clase)
            if elemento:
                return elemento.get_text(strip=True)
        return None
    
    def _buscar_monto(self, soup: BeautifulSoup, clases: List[str]) -> Optional[float]:
        """Busca monto en elementos HTML"""
        for clase in clases:
            elemento = soup.find(class_=clase)
            if elemento:
                texto = elemento.get_text(strip=True)
                monto = re.search(r'\$?\s*([\d\.]+)', texto.replace('.', '').replace(',', '.'))
                if monto:
                    return float(monto.group(1))
        return None
    
    def _buscar_lectura(self, soup: BeautifulSoup, clases: List[str]) -> Optional[float]:
        """Busca lectura en elementos HTML"""
        for clase in clases:
            elemento = soup.find(class_=clase)
            if elemento:
                texto = elemento.get_text(strip=True)
                lectura = re.search(r'([\d\.,]+)', texto)
                if lectura:
                    return float(lectura.group(1).replace(',', '.'))
        return None
    
    def _buscar_fecha(self, soup: BeautifulSoup, clases: List[str]) -> Optional[str]:
        """Busca fecha en elementos HTML"""
        for clase in clases:
            elemento = soup.find(class_=clase)
            if elemento:
                texto = elemento.get_text(strip=True)
                fecha = re.search(r'(\d{2}/\d{2}/\d{4})', texto)
                if fecha:
                    return fecha.group(1)
        return None
    
    def _normalizar_valor(self, campo: str, valor: str) -> Any:
        """
        Normaliza un valor según su tipo
        
        Args:
            campo: Nombre del campo
            valor: Valor a normalizar
            
        Returns:
            Valor normalizado
        """
        if campo in ['lectura_actual', 'lectura_anterior', 'consumo_kwh']:
            # Convertir a float
            valor = valor.replace(',', '.').replace(' ', '')
            try:
                return float(valor)
            except ValueError:
                return None
        
        elif campo == 'monto_total':
            # Remover símbolos y convertir a float
            valor = valor.replace('$', '').replace('.', '').replace(',', '.').replace(' ', '')
            try:
                return float(valor)
            except ValueError:
                return None
        
        elif campo == 'numero_boleta' or campo == 'numero_cliente':
            # Mantener como string
            return valor.strip()
        
        else:
            # Mantener como string
            return valor.strip()

