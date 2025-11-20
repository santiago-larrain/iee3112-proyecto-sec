"""
Gestor de base de datos JSON para leer casos desde archivos JSON relacionales
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List

class JSONDBManager:
    """Gestor que lee datos de archivos JSON relacionales"""
    
    def __init__(self, db_dir: str = "data/DataBase"):
        """
        Inicializa el gestor
        
        Args:
            db_dir: Directorio donde están los archivos JSON
        """
        self.db_dir = Path(db_dir)
        self._load_data()
    
    def _load_data(self):
        """Carga todos los datos de los archivos JSON"""
        # Cargar personas
        personas_path = self.db_dir / "personas.json"
        if personas_path.exists():
            with open(personas_path, "r", encoding="utf-8") as f:
                personas_data = json.load(f)
                self.personas = {p['rut']: p for p in personas_data}
        else:
            self.personas = {}
        
        # Cargar suministros
        suministros_path = self.db_dir / "suministros.json"
        if suministros_path.exists():
            with open(suministros_path, "r", encoding="utf-8") as f:
                suministros_data = json.load(f)
                self.suministros = {f"{s['nis']}-{s['comuna']}": s for s in suministros_data}
        else:
            self.suministros = {}
        
        # Cargar casos
        casos_path = self.db_dir / "casos.json"
        if casos_path.exists():
            with open(casos_path, "r", encoding="utf-8") as f:
                self.casos = json.load(f)
        else:
            self.casos = []
        
        # Cargar documentos
        documentos_path = self.db_dir / "documentos.json"
        if documentos_path.exists():
            with open(documentos_path, "r", encoding="utf-8") as f:
                self.documentos = json.load(f)
        else:
            self.documentos = []
    
    def get_caso_by_case_id(self, case_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un caso por su case_id
        
        Args:
            case_id: ID del caso
            
        Returns:
            Diccionario con el EDN o None si no existe
        """
        for caso in self.casos:
            if caso['case_id'] == case_id:
                return caso['edn']
        return None
    
    def get_all_casos(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los casos con información resumida
        
        Returns:
            Lista de diccionarios con información resumida de casos
        """
        summaries = []
        for caso in self.casos:
            # Buscar persona por persona_id
            persona_id = caso.get('persona_id')
            persona = next((p for p in self.personas.values() if p.get('id') == persona_id), None)
            
            # Si no se encuentra, buscar por RUT del EDN
            if not persona:
                edn = caso.get('edn', {})
                unified_context = edn.get('unified_context', {})
                rut = unified_context.get('rut_client')
                if rut:
                    persona = self.personas.get(rut)
            
            summaries.append({
                'case_id': caso['case_id'],
                'empresa': caso.get('empresa') or 'N/A',
                'materia': caso.get('materia') or 'N/A',
                'monto_disputa': caso.get('monto_disputa') or 0,
                'fecha_ingreso': caso.get('fecha_ingreso') or '',
                'estado': caso.get('estado') or 'PENDIENTE',
                'client_name': persona.get('nombre') if persona else 'N/A',
                'rut_client': persona.get('rut') if persona else 'N/A'
            })
        
        return summaries
    
    def reload(self):
        """Recarga todos los datos desde los archivos JSON"""
        self._load_data()
    
    def reload_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """
        Recarga un caso específico desde el archivo JSON
        
        Args:
            case_id: ID del caso a recargar
            
        Returns:
            Diccionario con el EDN actualizado o None si no existe
        """
        # Recargar casos
        casos_path = self.db_dir / "casos.json"
        if casos_path.exists():
            with open(casos_path, "r", encoding="utf-8") as f:
                casos = json.load(f)
                # Actualizar el caso en memoria
                for caso in casos:
                    if caso.get('case_id') == case_id:
                        # Actualizar en la lista de casos
                        for idx, c in enumerate(self.casos):
                            if c.get('case_id') == case_id:
                                self.casos[idx] = caso
                                return caso.get('edn')
                        # Si no existe, agregarlo
                        self.casos.append(caso)
                        return caso.get('edn')
        
        # Recargar personas y suministros también
        self._load_data()
        return None

