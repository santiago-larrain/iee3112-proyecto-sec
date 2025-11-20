"""
Gestor de base de datos con esquema estrella y lógica de upsert
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DBManager:
    """Gestor de base de datos SQLite con esquema estrella"""
    
    def __init__(self, db_path: str = "data/sec_reclamos.db"):
        """
        Inicializa el gestor de base de datos
        
        Args:
            db_path: Ruta al archivo de base de datos
        """
        self.db_path = db_path
        # Crear directorio si no existe
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._create_schema()
    
    def _get_connection(self):
        """Obtiene una conexión a la base de datos"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _create_schema(self):
        """Crea el esquema de base de datos si no existe"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Tabla PERSONAS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS personas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rut TEXT UNIQUE NOT NULL,
                nombre TEXT,
                email TEXT,
                telefono TEXT,
                fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
                fecha_actualizacion TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla SUMINISTROS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS suministros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nis TEXT NOT NULL,
                comuna TEXT NOT NULL,
                direccion TEXT,
                numero_cliente TEXT,
                fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(nis, comuna)
            )
        ''')
        
        # Tabla CASOS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS casos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT UNIQUE NOT NULL,
                persona_id INTEGER NOT NULL,
                suministro_id INTEGER NOT NULL,
                empresa TEXT,
                materia TEXT,
                monto_disputa REAL,
                fecha_ingreso TEXT,
                estado TEXT DEFAULT 'PENDIENTE',
                edn_json TEXT,
                fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
                fecha_actualizacion TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (persona_id) REFERENCES personas(id),
                FOREIGN KEY (suministro_id) REFERENCES suministros(id)
            )
        ''')
        
        # Tabla DOCUMENTOS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                caso_id INTEGER NOT NULL,
                file_id TEXT NOT NULL,
                original_name TEXT NOT NULL,
                standardized_name TEXT,
                type TEXT NOT NULL,
                level TEXT,
                file_path TEXT,
                extracted_data TEXT,
                metadata TEXT,
                fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (caso_id) REFERENCES casos(id),
                UNIQUE(caso_id, file_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Esquema de base de datos inicializado")
    
    def upsert_persona(self, rut: str, nombre: Optional[str] = None, 
                      email: Optional[str] = None, telefono: Optional[str] = None) -> int:
        """
        Inserta o actualiza una persona
        
        Args:
            rut: RUT de la persona
            nombre: Nombre (opcional)
            email: Email (opcional)
            telefono: Teléfono (opcional)
            
        Returns:
            ID de la persona
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Buscar si existe
        cursor.execute("SELECT id FROM personas WHERE rut = ?", (rut,))
        row = cursor.fetchone()
        
        if row:
            # Actualizar
            persona_id = row['id']
            updates = []
            params = []
            
            if nombre:
                updates.append("nombre = ?")
                params.append(nombre)
            if email:
                updates.append("email = ?")
                params.append(email)
            if telefono:
                updates.append("telefono = ?")
                params.append(telefono)
            
            if updates:
                updates.append("fecha_actualizacion = ?")
                params.append(datetime.utcnow().isoformat())
                params.append(persona_id)
                
                cursor.execute(
                    f"UPDATE personas SET {', '.join(updates)} WHERE id = ?",
                    params
                )
        else:
            # Insertar
            cursor.execute('''
                INSERT INTO personas (rut, nombre, email, telefono, fecha_creacion, fecha_actualizacion)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (rut, nombre, email, telefono, 
                  datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))
            persona_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return persona_id
    
    def upsert_suministro(self, nis: str, comuna: str, 
                         direccion: Optional[str] = None,
                         numero_cliente: Optional[str] = None) -> int:
        """
        Inserta o actualiza un suministro
        
        Args:
            nis: NIS del suministro
            comuna: Comuna
            direccion: Dirección (opcional)
            numero_cliente: Número de cliente (opcional)
            
        Returns:
            ID del suministro
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Buscar si existe
        cursor.execute("SELECT id FROM suministros WHERE nis = ? AND comuna = ?", (nis, comuna))
        row = cursor.fetchone()
        
        if row:
            suministro_id = row['id']
            # Actualizar si hay nuevos datos
            if direccion or numero_cliente:
                updates = []
                params = []
                if direccion:
                    updates.append("direccion = ?")
                    params.append(direccion)
                if numero_cliente:
                    updates.append("numero_cliente = ?")
                    params.append(numero_cliente)
                if updates:
                    params.append(suministro_id)
                    cursor.execute(
                        f"UPDATE suministros SET {', '.join(updates)} WHERE id = ?",
                        params
                    )
        else:
            # Insertar
            cursor.execute('''
                INSERT INTO suministros (nis, comuna, direccion, numero_cliente, fecha_creacion)
                VALUES (?, ?, ?, ?, ?)
            ''', (nis, comuna, direccion, numero_cliente, datetime.utcnow().isoformat()))
            suministro_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return suministro_id
    
    def upsert_caso(self, case_id: str, persona_id: int, suministro_id: int,
                   edn: Dict[str, Any], empresa: Optional[str] = None,
                   materia: Optional[str] = None, monto_disputa: Optional[float] = None,
                   fecha_ingreso: Optional[str] = None) -> int:
        """
        Inserta o actualiza un caso
        
        Args:
            case_id: ID del caso
            persona_id: ID de la persona
            suministro_id: ID del suministro
            edn: Expediente Digital Normalizado completo
            empresa: Empresa (opcional)
            materia: Materia (opcional)
            monto_disputa: Monto en disputa (opcional)
            fecha_ingreso: Fecha de ingreso (opcional)
            
        Returns:
            ID del caso
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Buscar si existe
        cursor.execute("SELECT id FROM casos WHERE case_id = ?", (case_id,))
        row = cursor.fetchone()
        
        edn_json = json.dumps(edn, ensure_ascii=False)
        
        if row:
            # Actualizar
            caso_id_db = row['id']
            cursor.execute('''
                UPDATE casos 
                SET persona_id = ?, suministro_id = ?, empresa = ?, materia = ?,
                    monto_disputa = ?, fecha_ingreso = ?, edn_json = ?,
                    fecha_actualizacion = ?
                WHERE id = ?
            ''', (persona_id, suministro_id, empresa, materia, monto_disputa,
                  fecha_ingreso, edn_json, datetime.utcnow().isoformat(), caso_id_db))
        else:
            # Insertar
            cursor.execute('''
                INSERT INTO casos (case_id, persona_id, suministro_id, empresa, materia,
                                 monto_disputa, fecha_ingreso, estado, edn_json,
                                 fecha_creacion, fecha_actualizacion)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (case_id, persona_id, suministro_id, empresa, materia,
                  monto_disputa, fecha_ingreso, 'PENDIENTE', edn_json,
                  datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))
            caso_id_db = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return caso_id_db
    
    def upsert_documento(self, caso_id: int, file_id: str, original_name: str,
                        doc_type: str, level: str, file_path: Optional[str] = None,
                        standardized_name: Optional[str] = None,
                        extracted_data: Optional[Dict] = None,
                        metadata: Optional[Dict] = None):
        """
        Inserta o actualiza un documento
        
        Args:
            caso_id: ID del caso
            file_id: ID único del archivo
            original_name: Nombre original del archivo
            doc_type: Tipo de documento
            level: Nivel (level_1_critical, level_2_supporting)
            file_path: Ruta del archivo (opcional)
            standardized_name: Nombre estandarizado (opcional)
            extracted_data: Datos extraídos (opcional)
            metadata: Metadatos (opcional)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        extracted_data_json = json.dumps(extracted_data, ensure_ascii=False) if extracted_data else None
        metadata_json = json.dumps(metadata, ensure_ascii=False) if metadata else None
        
        # Buscar si existe
        cursor.execute("SELECT id FROM documentos WHERE caso_id = ? AND file_id = ?", 
                      (caso_id, file_id))
        row = cursor.fetchone()
        
        if row:
            # Actualizar
            cursor.execute('''
                UPDATE documentos 
                SET original_name = ?, standardized_name = ?, type = ?, level = ?,
                    file_path = ?, extracted_data = ?, metadata = ?
                WHERE id = ?
            ''', (original_name, standardized_name, doc_type, level, file_path,
                  extracted_data_json, metadata_json, row['id']))
        else:
            # Insertar
            cursor.execute('''
                INSERT INTO documentos (caso_id, file_id, original_name, standardized_name,
                                      type, level, file_path, extracted_data, metadata,
                                      fecha_creacion)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (caso_id, file_id, original_name, standardized_name, doc_type, level,
                  file_path, extracted_data_json, metadata_json, datetime.utcnow().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_caso_by_case_id(self, case_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un caso por su case_id
        
        Args:
            case_id: ID del caso
            
        Returns:
            Diccionario con el EDN o None si no existe
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT edn_json FROM casos WHERE case_id = ?", (case_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return json.loads(row['edn_json'])
        return None
    
    def get_all_casos(self) -> list:
        """
        Obtiene todos los casos
        
        Returns:
            Lista de diccionarios con información resumida de casos
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.case_id, 
                   COALESCE(c.empresa, 'N/A') as empresa, 
                   COALESCE(c.materia, 'N/A') as materia, 
                   COALESCE(c.monto_disputa, 0) as monto_disputa, 
                   COALESCE(c.fecha_ingreso, '') as fecha_ingreso, 
                   COALESCE(c.estado, 'PENDIENTE') as estado,
                   COALESCE(p.nombre, 'N/A') as client_name, 
                   COALESCE(p.rut, 'N/A') as rut_client
            FROM casos c
            JOIN personas p ON c.persona_id = p.id
            ORDER BY c.fecha_creacion DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

