"""
Clase base abstracta para scrapers de distribuidoras
"""

import time
import requests
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from modulos.utils.config import Config
from modulos.utils.logger import Logger


class ScraperBase(ABC):
    """Clase base abstracta para scrapers de distribuidoras"""
    
    def __init__(self, distribuidora: str, config: Optional[Config] = None, 
                 logger: Optional[Logger] = None):
        """
        Inicializa el scraper base
        
        Args:
            distribuidora: Nombre de la distribuidora
            config: Instancia de Config
            logger: Instancia de Logger
        """
        if config is None:
            config = Config()
        if logger is None:
            logger = Logger(config)
        
        self.distribuidora = distribuidora
        self.config = config
        self.logger = logger
        self.scraping_config = config.get_scraping()
        
        self.timeout = self.scraping_config.get('timeout', 30)
        self.max_reintentos = self.scraping_config.get('max_reintentos', 3)
        self.delay_entre_peticiones = self.scraping_config.get('delay_entre_peticiones', 2)
        self.user_agent = self.scraping_config.get('user_agent', 
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver: Optional[webdriver.Chrome] = None
        self.session: Optional[requests.Session] = None
    
    def _crear_sesion(self) -> requests.Session:
        """Crea una sesión HTTP con configuración estándar"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        return session
    
    def _crear_driver(self, headless: bool = True) -> webdriver.Chrome:
        """
        Crea un driver de Selenium
        
        Args:
            headless: Si es True, ejecuta el navegador en modo headless
            
        Returns:
            Instancia de webdriver.Chrome
        """
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f'--user-agent={self.user_agent}')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def _retry(self, funcion, *args, **kwargs):
        """
        Ejecuta una función con lógica de reintentos
        
        Args:
            funcion: Función a ejecutar
            *args: Argumentos posicionales
            **kwargs: Argumentos nombrados
            
        Returns:
            Resultado de la función
            
        Raises:
            Exception: Si falla después de todos los reintentos
        """
        ultimo_error = None
        
        for intento in range(1, self.max_reintentos + 1):
            try:
                self.logger.debug(f"Intento {intento}/{self.max_reintentos} para {funcion.__name__}")
                return funcion(*args, **kwargs)
            except Exception as e:
                ultimo_error = e
                self.logger.warning(f"Intento {intento} falló: {str(e)}")
                
                if intento < self.max_reintentos:
                    tiempo_espera = self.delay_entre_peticiones * intento
                    self.logger.info(f"Esperando {tiempo_espera} segundos antes de reintentar...")
                    time.sleep(tiempo_espera)
        
        self.logger.error(f"Fallo después de {self.max_reintentos} intentos")
        raise ultimo_error
    
    def _esperar_elemento(self, driver: webdriver.Chrome, by: By, valor: str, 
                         timeout: Optional[int] = None):
        """
        Espera a que un elemento esté presente en la página
        
        Args:
            driver: Instancia del driver
            by: Método de búsqueda (By.ID, By.CLASS_NAME, etc.)
            valor: Valor a buscar
            timeout: Tiempo máximo de espera
            
        Returns:
            Elemento encontrado
        """
        if timeout is None:
            timeout = self.timeout
        
        wait = WebDriverWait(driver, timeout)
        return wait.until(EC.presence_of_element_located((by, valor)))
    
    def _esperar_carga_pagina(self, driver: webdriver.Chrome, timeout: Optional[int] = None):
        """
        Espera a que la página cargue completamente
        
        Args:
            driver: Instancia del driver
            timeout: Tiempo máximo de espera
        """
        if timeout is None:
            timeout = self.timeout
        
        try:
            WebDriverWait(driver, timeout).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
        except TimeoutException:
            self.logger.warning("Timeout esperando carga de página")
    
    @abstractmethod
    def obtener_url_login(self) -> str:
        """
        Retorna la URL de login de la distribuidora
        
        Returns:
            URL de login
        """
        pass
    
    @abstractmethod
    def login(self, usuario: str, password: str) -> bool:
        """
        Realiza login en el portal de la distribuidora
        
        Args:
            usuario: Usuario o número de cliente
            password: Contraseña
            
        Returns:
            True si el login fue exitoso
        """
        pass
    
    @abstractmethod
    def obtener_boletas(self, numero_cliente: str, periodo_inicio: Optional[str] = None,
                        periodo_fin: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtiene las boletas de un cliente
        
        Args:
            numero_cliente: Número de cliente
            periodo_inicio: Fecha de inicio del período (formato YYYY-MM)
            periodo_fin: Fecha de fin del período (formato YYYY-MM)
            
        Returns:
            Lista de diccionarios con datos de las boletas
        """
        pass
    
    def _normalizar_datos_boleta(self, datos_brutos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza los datos de una boleta a formato estándar
        
        Args:
            datos_brutos: Datos extraídos en formato específico de la distribuidora
            
        Returns:
            Datos normalizados
        """
        return {
            'distribuidora': self.distribuidora,
            'numero_cliente': datos_brutos.get('numero_cliente', ''),
            'numero_boleta': datos_brutos.get('numero_boleta', ''),
            'periodo_facturacion': datos_brutos.get('periodo_facturacion', ''),
            'lectura_actual': self._normalizar_lectura(datos_brutos.get('lectura_actual')),
            'lectura_anterior': self._normalizar_lectura(datos_brutos.get('lectura_anterior')),
            'consumo_kwh': self._normalizar_consumo(datos_brutos.get('consumo_kwh')),
            'monto_total': self._normalizar_monto(datos_brutos.get('monto_total')),
            'fecha_vencimiento': datos_brutos.get('fecha_vencimiento', ''),
            'estado_pago': datos_brutos.get('estado_pago', 'pendiente'),
            'direccion': datos_brutos.get('direccion', ''),
            'datos_boleta': datos_brutos  # Mantener datos originales
        }
    
    def _normalizar_lectura(self, lectura: Any) -> Optional[float]:
        """Normaliza una lectura a float"""
        if lectura is None:
            return None
        try:
            if isinstance(lectura, str):
                # Remover caracteres no numéricos excepto punto y coma
                lectura = lectura.replace(',', '.').replace(' ', '')
                return float(lectura)
            return float(lectura)
        except (ValueError, TypeError):
            return None
    
    def _normalizar_consumo(self, consumo: Any) -> Optional[float]:
        """Normaliza un consumo a float (kWh)"""
        return self._normalizar_lectura(consumo)
    
    def _normalizar_monto(self, monto: Any) -> Optional[float]:
        """Normaliza un monto a float (pesos chilenos)"""
        if monto is None:
            return None
        try:
            if isinstance(monto, str):
                # Remover símbolos de moneda y espacios
                monto = monto.replace('$', '').replace('.', '').replace(',', '.').replace(' ', '')
                return float(monto)
            return float(monto)
        except (ValueError, TypeError):
            return None
    
    def cerrar(self):
        """Cierra las conexiones y libera recursos"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
        
        if self.session:
            self.session.close()
            self.session = None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cerrar()

