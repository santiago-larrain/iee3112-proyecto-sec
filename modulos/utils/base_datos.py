"""
Gestión de base de datos
"""

import sqlite3
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
from contextlib import contextmanager
from .config import Config
from .logger import Logger


class BaseDatos:
    """Gestor de base de datos"""
    
    def __init__(self, config: Optional[Config] = None, logger: Optional[Logger] = None):
        """
        Inicializa el gestor de base de datos
        
        Args:
            config: Instancia de Config. Si es None, crea una nueva
            logger: Instancia de Logger. Si es None, crea una nueva
        """
        if config is None:
            config = Config()
        if logger is None:
            logger = Logger(config)
        
        self.config = config
        self.logger = logger
        self.db_config = config.get_base_datos()
        self.tipo_db = self.db_config.get('tipo', 'sqlite')
        self._conexion: Optional[sqlite3.Connection] = None
        self._inicializar_base_datos()
    
    def _inicializar_base_datos(self):
        """Inicializa la base de datos y crea tablas si no existen"""
        if self.tipo_db == 'sqlite':
            self._inicializar_sqlite()
        else:
            raise NotImplementedError(f"Tipo de base de datos {self.tipo_db} no implementado")
    
    def _inicializar_sqlite(self):
        """Inicializa base de datos SQLite"""
        nombre_db = self.db_config.get('nombre', 'sec_reclamos.db')
        rutas = self.config.get_rutas()
        ruta_db = Path(rutas['data']) / nombre_db
        
        # Crear directorio si no existe
        ruta_db.parent.mkdir(parents=True, exist_ok=True)
        
        self.ruta_db = str(ruta_db)
        self._crear_tablas()
    
    def _crear_tablas(self):
        """Crea las tablas necesarias si no existen"""
        with self._obtener_conexion() as conn:
            cursor = conn.cursor()
            
            # Tabla de reclamos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reclamos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_reclamo TEXT UNIQUE,
                    numero_cliente TEXT,
                    distribuidora TEXT,
                    tipologia TEXT,
                    fecha_ingreso TEXT,
                    estado TEXT,
                    datos_reclamo TEXT,
                    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
                    fecha_actualizacion TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de boletas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS boletas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_cliente TEXT,
                    distribuidora TEXT,
                    periodo_facturacion TEXT,
                    numero_boleta TEXT,
                    lectura_actual REAL,
                    lectura_anterior REAL,
                    consumo_kwh REAL,
                    monto_total REAL,
                    fecha_vencimiento TEXT,
                    estado_pago TEXT,
                    datos_boleta TEXT,
                    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(numero_cliente, periodo_facturacion)
                )
            ''')
            
            # Tabla de expedientes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS expedientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_reclamo INTEGER,
                    tipologia TEXT,
                    analisis TEXT,
                    medios_probatorios TEXT,
                    cumplimiento TEXT,
                    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (id_reclamo) REFERENCES reclamos(id)
                )
            ''')
            
            conn.commit()
            self.logger.info("Tablas de base de datos inicializadas correctamente")
    
    @contextmanager
    def _obtener_conexion(self):
        """Context manager para obtener conexión a la base de datos"""
        if self.tipo_db == 'sqlite':
            conn = sqlite3.connect(self.ruta_db)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            finally:
                conn.close()
        else:
            raise NotImplementedError(f"Tipo de base de datos {self.tipo_db} no implementado")
    
    def guardar_reclamo(self, datos: Dict[str, Any]) -> int:
        """
        Guarda un reclamo en la base de datos
        
        Args:
            datos: Diccionario con datos del reclamo
            
        Returns:
            ID del reclamo guardado
        """
        import json
        
        with self._obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO reclamos 
                (numero_reclamo, numero_cliente, distribuidora, tipologia, 
                 fecha_ingreso, estado, datos_reclamo, fecha_actualizacion)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                datos.get('numero_reclamo'),
                datos.get('numero_cliente'),
                datos.get('distribuidora'),
                datos.get('tipologia'),
                datos.get('fecha_ingreso'),
                datos.get('estado', 'pendiente'),
                json.dumps(datos.get('datos_reclamo', {}))
            ))
            conn.commit()
            return cursor.lastrowid
    
    def obtener_reclamo(self, numero_reclamo: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un reclamo por su número
        
        Args:
            numero_reclamo: Número del reclamo
            
        Returns:
            Diccionario con datos del reclamo o None si no existe
        """
        import json
        
        with self._obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM reclamos WHERE numero_reclamo = ?', (numero_reclamo,))
            row = cursor.fetchone()
            
            if row:
                datos = dict(row)
                if datos.get('datos_reclamo'):
                    datos['datos_reclamo'] = json.loads(datos['datos_reclamo'])
                return datos
            return None
    
    def guardar_boleta(self, datos: Dict[str, Any]) -> int:
        """
        Guarda una boleta en la base de datos
        
        Args:
            datos: Diccionario con datos de la boleta
            
        Returns:
            ID de la boleta guardada
        """
        import json
        
        with self._obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO boletas 
                (numero_cliente, distribuidora, periodo_facturacion, numero_boleta,
                 lectura_actual, lectura_anterior, consumo_kwh, monto_total,
                 fecha_vencimiento, estado_pago, datos_boleta)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datos.get('numero_cliente'),
                datos.get('distribuidora'),
                datos.get('periodo_facturacion'),
                datos.get('numero_boleta'),
                datos.get('lectura_actual'),
                datos.get('lectura_anterior'),
                datos.get('consumo_kwh'),
                datos.get('monto_total'),
                datos.get('fecha_vencimiento'),
                datos.get('estado_pago', 'pendiente'),
                json.dumps(datos.get('datos_boleta', {}))
            ))
            conn.commit()
            return cursor.lastrowid
    
    def obtener_boletas_cliente(self, numero_cliente: str, limite: int = 24) -> List[Dict[str, Any]]:
        """
        Obtiene las boletas de un cliente (últimas N según manual: 24 meses)
        
        Args:
            numero_cliente: Número de cliente
            limite: Número máximo de boletas a obtener
            
        Returns:
            Lista de boletas ordenadas por período
        """
        import json
        
        with self._obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM boletas 
                WHERE numero_cliente = ?
                ORDER BY periodo_facturacion DESC
                LIMIT ?
            ''', (numero_cliente, limite))
            
            boletas = []
            for row in cursor.fetchall():
                datos = dict(row)
                if datos.get('datos_boleta'):
                    datos['datos_boleta'] = json.loads(datos['datos_boleta'])
                boletas.append(datos)
            
            return boletas
    
    def guardar_expediente(self, id_reclamo: int, datos: Dict[str, Any]) -> int:
        """
        Guarda un expediente en la base de datos
        
        Args:
            id_reclamo: ID del reclamo asociado
            datos: Diccionario con datos del expediente
            
        Returns:
            ID del expediente guardado
        """
        import json
        
        with self._obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO expedientes 
                (id_reclamo, tipologia, analisis, medios_probatorios, cumplimiento)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                id_reclamo,
                datos.get('tipologia'),
                json.dumps(datos.get('analisis', {})),
                json.dumps(datos.get('medios_probatorios', [])),
                json.dumps(datos.get('cumplimiento', {}))
            ))
            conn.commit()
            return cursor.lastrowid

