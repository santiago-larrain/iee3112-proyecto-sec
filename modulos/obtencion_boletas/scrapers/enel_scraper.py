"""
Scraper para Enel Distribución
"""

import time
from typing import Dict, List, Optional, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException

from ..scraper_base import ScraperBase


class EnelScraper(ScraperBase):
    """Scraper específico para Enel Distribución"""
    
    def __init__(self, config=None, logger=None):
        super().__init__("Enel", config, logger)
        self.url_base = "https://www.enel.cl"
        self.url_login = f"{self.url_base}/es/clientes/ingresa-tu-cuenta.html"
    
    def obtener_url_login(self) -> str:
        """Retorna la URL de login de Enel"""
        return self.url_login
    
    def login(self, usuario: str, password: str) -> bool:
        """
        Realiza login en el portal de Enel
        
        Args:
            usuario: Número de cliente o RUT
            password: Contraseña
            
        Returns:
            True si el login fue exitoso
        """
        try:
            if not self.driver:
                self.driver = self._crear_driver(headless=True)
            
            self.logger.info(f"Iniciando login en Enel para usuario: {usuario}")
            self.driver.get(self.url_login)
            self._esperar_carga_pagina(self.driver)
            
            # Buscar campos de login (estructura puede variar)
            # Nota: Estos selectores son ejemplos y deben ajustarse según la estructura real
            try:
                campo_usuario = self._esperar_elemento(self.driver, By.ID, "usuario")
                campo_password = self.driver.find_element(By.ID, "password")
                boton_login = self.driver.find_element(By.ID, "btn-login")
                
                campo_usuario.clear()
                campo_usuario.send_keys(usuario)
                campo_password.clear()
                campo_password.send_keys(password)
                
                boton_login.click()
                time.sleep(3)  # Esperar redirección
                
                # Verificar si el login fue exitoso
                # (verificar URL o elemento que indique sesión activa)
                if "cuenta" in self.driver.current_url.lower() or "dashboard" in self.driver.current_url.lower():
                    self.logger.info("Login exitoso en Enel")
                    return True
                else:
                    self.logger.warning("Login posiblemente fallido - verificar credenciales")
                    return False
                    
            except NoSuchElementException as e:
                self.logger.error(f"Error al encontrar elementos de login: {str(e)}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error durante login en Enel: {str(e)}")
            return False
    
    def obtener_boletas(self, numero_cliente: str, periodo_inicio: Optional[str] = None,
                       periodo_fin: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtiene las boletas de un cliente de Enel
        
        Args:
            numero_cliente: Número de cliente
            periodo_inicio: Fecha de inicio (YYYY-MM)
            periodo_fin: Fecha de fin (YYYY-MM)
            
        Returns:
            Lista de boletas
        """
        boletas = []
        
        try:
            if not self.driver:
                raise Exception("Driver no inicializado. Debe hacer login primero.")
            
            self.logger.info(f"Obteniendo boletas para cliente {numero_cliente}")
            
            # Navegar a sección de boletas
            # Nota: URLs y selectores deben ajustarse según estructura real
            url_boletas = f"{self.url_base}/es/clientes/mis-boletas.html"
            self.driver.get(url_boletas)
            self._esperar_carga_pagina(self.driver)
            time.sleep(2)
            
            # Buscar lista de boletas
            # Ejemplo de estructura (ajustar según realidad):
            try:
                # Intentar encontrar tabla o lista de boletas
                elementos_boletas = self.driver.find_elements(By.CLASS_NAME, "boleta-item")
                
                if not elementos_boletas:
                    # Intentar otro selector común
                    elementos_boletas = self.driver.find_elements(By.CSS_SELECTOR, 
                        "[data-boleta]")
                
                self.logger.info(f"Encontradas {len(elementos_boletas)} boletas")
                
                for elemento in elementos_boletas:
                    try:
                        boleta = self._extraer_datos_boleta(elemento)
                        if boleta:
                            boleta['numero_cliente'] = numero_cliente
                            boletas.append(self._normalizar_datos_boleta(boleta))
                    except Exception as e:
                        self.logger.warning(f"Error al extraer datos de boleta: {str(e)}")
                        continue
                
            except NoSuchElementException:
                self.logger.warning("No se encontraron boletas o estructura diferente")
            
            # Si hay filtros de período, aplicarlos
            if periodo_inicio or periodo_fin:
                boletas = self._filtrar_por_periodo(boletas, periodo_inicio, periodo_fin)
            
            self.logger.info(f"Se obtuvieron {len(boletas)} boletas válidas")
            return boletas
            
        except Exception as e:
            self.logger.error(f"Error al obtener boletas de Enel: {str(e)}")
            return boletas
    
    def _extraer_datos_boleta(self, elemento) -> Optional[Dict[str, Any]]:
        """
        Extrae los datos de una boleta desde un elemento HTML
        
        Args:
            elemento: Elemento Selenium con datos de la boleta
            
        Returns:
            Diccionario con datos de la boleta
        """
        try:
            # Ejemplo de extracción (ajustar según estructura real)
            datos = {}
            
            # Intentar extraer número de boleta
            try:
                datos['numero_boleta'] = elemento.find_element(
                    By.CLASS_NAME, "numero-boleta").text.strip()
            except:
                datos['numero_boleta'] = ""
            
            # Intentar extraer período
            try:
                datos['periodo_facturacion'] = elemento.find_element(
                    By.CLASS_NAME, "periodo").text.strip()
            except:
                datos['periodo_facturacion'] = ""
            
            # Intentar extraer monto
            try:
                datos['monto_total'] = elemento.find_element(
                    By.CLASS_NAME, "monto").text.strip()
            except:
                datos['monto_total'] = ""
            
            # Intentar extraer fecha de vencimiento
            try:
                datos['fecha_vencimiento'] = elemento.find_element(
                    By.CLASS_NAME, "vencimiento").text.strip()
            except:
                datos['fecha_vencimiento'] = ""
            
            # Intentar obtener link a PDF para extraer más datos
            try:
                link_pdf = elemento.find_element(By.CSS_SELECTOR, "a[href*='.pdf']")
                url_pdf = link_pdf.get_attribute('href')
                datos['url_pdf'] = url_pdf
            except:
                datos['url_pdf'] = None
            
            return datos if datos.get('numero_boleta') else None
            
        except Exception as e:
            self.logger.warning(f"Error al extraer datos de boleta: {str(e)}")
            return None
    
    def _filtrar_por_periodo(self, boletas: List[Dict[str, Any]], 
                            periodo_inicio: Optional[str],
                            periodo_fin: Optional[str]) -> List[Dict[str, Any]]:
        """
        Filtra boletas por período
        
        Args:
            boletas: Lista de boletas
            periodo_inicio: Fecha inicio (YYYY-MM)
            periodo_fin: Fecha fin (YYYY-MM)
            
        Returns:
            Lista filtrada
        """
        from datetime import datetime
        
        boletas_filtradas = []
        
        for boleta in boletas:
            periodo = boleta.get('periodo_facturacion', '')
            if not periodo:
                continue
            
            try:
                # Intentar parsear período (formato puede variar)
                fecha_boleta = datetime.strptime(periodo, '%Y-%m')
                
                if periodo_inicio:
                    fecha_inicio = datetime.strptime(periodo_inicio, '%Y-%m')
                    if fecha_boleta < fecha_inicio:
                        continue
                
                if periodo_fin:
                    fecha_fin = datetime.strptime(periodo_fin, '%Y-%m')
                    if fecha_boleta > fecha_fin:
                        continue
                
                boletas_filtradas.append(boleta)
                
            except ValueError:
                # Si no se puede parsear, incluir por defecto
                boletas_filtradas.append(boleta)
        
        return boletas_filtradas

