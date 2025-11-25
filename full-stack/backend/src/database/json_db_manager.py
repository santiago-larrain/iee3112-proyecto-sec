"""
Gestor de base de datos JSON para leer casos desde archivos JSON relacionales
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
from src.config import DATABASE_DIR

# Configuración del logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JSONDBManager:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(JSONDBManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, base_path: Path = DATABASE_DIR):
        if not hasattr(self, 'initialized'):
            self.base_path = base_path
            self.base_path.mkdir(parents=True, exist_ok=True)
            
            self.files = {
                "casos": self.base_path / "casos.json",
                "edn": self.base_path / "edn.json",
                "personas": self.base_path / "personas.json",
                "suministros": self.base_path / "suministros.json",
                "documentos": self.base_path / "documentos.json"
            }
            
            self._ensure_files_exist()
            self.data_store = self._load_data()
            self.cases_store: Dict[str, Any] = {}
            self.initialized = True

    def _ensure_files_exist(self):
        """
        Asegura que todos los archivos JSON necesarios existan.
        Si no, los crea con un formato vacío.
        """
        for file_path in self.files.values():
            if not file_path.exists():
                logger.warning(f"Archivo {file_path} no encontrado. Creando un archivo vacío.")
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump({}, f, indent=2, ensure_ascii=False)

    def _load_data(self) -> Dict[str, Any]:
        """Carga todos los datos de los archivos JSON"""
        data = {}
        for file_name, file_path in self.files.items():
            if file_name == "casos":
                with open(file_path, "r", encoding="utf-8") as f:
                    data["casos"] = json.load(f)
            elif file_name == "edn":
                with open(file_path, "r", encoding="utf-8") as f:
                    data["edns"] = json.load(f)
            elif file_name == "personas":
                with open(file_path, "r", encoding="utf-8") as f:
                    data["personas"] = {p['rut']: p for p in json.load(f)}
            elif file_name == "suministros":
                with open(file_path, "r", encoding="utf-8") as f:
                    data["suministros"] = {f"{s['nis']}-{s['comuna']}": s for s in json.load(f)}
            elif file_name == "documentos":
                with open(file_path, "r", encoding="utf-8") as f:
                    data["documentos"] = json.load(f)
        return data
    
    def get_caso_by_case_id(self, case_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un caso por su case_id, fusionando metadatos del caso con el EDN
        
        Args:
            case_id: ID del caso
            
        Returns:
            Diccionario con el EDN fusionado con metadatos del caso, o None si no existe
        """
        # Buscar caso en casos.json
        caso = None
        for c in self.data_store["casos"]:
            if c.get('case_id') == case_id:
                caso = c
                break
        
        if not caso:
            return None
        
        # Obtener EDN desde edn.json (nueva estructura)
        # Si no existe en edn.json, intentar desde caso.edn (compatibilidad con estructura antigua)
        edn = self.data_store["edns"].get(case_id)
        if not edn:
            # Fallback: estructura antigua con EDN anidado
            edn = caso.get('edn', {})
        
        # Fusionar metadatos del caso con el EDN
        # Estos campos son necesarios para el frontend
        merged = edn.copy()
        merged['materia'] = caso.get('materia')
        merged['monto_disputa'] = caso.get('monto_disputa')
        merged['empresa'] = caso.get('empresa')
        merged['fecha_ingreso'] = caso.get('fecha_ingreso')
        
        return merged
    
    def get_all_casos(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los casos con información resumida
        Usa el EDN como fuente de verdad para unified_context (cliente, RUT, etc.)
        
        Returns:
            Lista de diccionarios con información resumida de casos
        """
        summaries = []
        for caso in self.data_store["casos"]:
            case_id = caso.get('case_id')
            if not case_id:
                continue
            
            # Obtener EDN para usar como fuente de verdad
            edn = self.data_store["edns"].get(case_id)
            if not edn:
                # Si no hay EDN, crear uno básico
                edn = {
                    "unified_context": {},
                    "compilation_metadata": {"case_id": case_id}
                }
            
            unified_context = edn.get('unified_context', {})
            
            # Usar datos del EDN como fuente principal
            # Si no están en el EDN, intentar desde personas.json como fallback
            client_name = unified_context.get('client_name')
            rut_client = unified_context.get('rut_client')
            
            # Fallback a personas.json solo si no hay datos en EDN
            if not client_name or client_name == '—' or client_name == 'N/A':
                persona_id = caso.get('persona_id')
                persona = next((p for p in self.data_store["personas"].values() if p.get('id') == persona_id), None)
                if persona:
                    client_name = persona.get('nombre', 'N/A')
                    if not rut_client or rut_client == '—' or rut_client == 'N/A':
                        rut_client = persona.get('rut', 'N/A')
            
            # Si aún no hay nombre, usar un placeholder
            if not client_name or client_name == '—':
                client_name = f"Cliente {case_id}"
            if not rut_client or rut_client == '—':
                rut_client = f"RUT-{case_id}"
            
            # Usar tipo_caso del EDN como materia si no hay materia específica
            compilation_metadata = edn.get('compilation_metadata', {})
            tipo_caso = compilation_metadata.get('tipo_caso')
            materia = caso.get('materia') or edn.get('materia') or tipo_caso or 'N/A'
            
            summaries.append({
                'case_id': case_id,
                'empresa': caso.get('empresa') or 'N/A',
                'materia': materia,
                'monto_disputa': caso.get('monto_disputa') or edn.get('monto_disputa') or 0,
                'fecha_ingreso': caso.get('fecha_ingreso') or 'N/A',
                'estado': caso.get('estado') or 'PENDIENTE',
                'client_name': client_name,
                'rut_client': rut_client
            })
        
        return summaries
    
    def reload(self):
        """Recarga todos los datos desde los archivos JSON"""
        self.data_store = self._load_data()
    
    def reload_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """
        Recarga un caso específico desde los archivos JSON
        
        Args:
            case_id: ID del caso a recargar
            
        Returns:
            Diccionario con el EDN actualizado o None si no existe
        """
        # Recargar casos
        casos_path = self.files["casos"]
        if casos_path.exists():
            with open(casos_path, "r", encoding="utf-8") as f:
                casos = json.load(f)
                # Actualizar el caso en memoria
                for caso in casos:
                    if caso.get('case_id') == case_id:
                        # Actualizar en la lista de casos
                        for idx, c in enumerate(self.data_store["casos"]):
                            if c.get('case_id') == case_id:
                                self.data_store["casos"][idx] = caso
                                break
                        else:
                            # Si no existe, agregarlo
                            self.data_store["casos"].append(caso)
        
        # Recargar EDN
        edn_path = self.files["edn"]
        if edn_path.exists():
            with open(edn_path, "r", encoding="utf-8") as f:
                edns = json.load(f)
                if case_id in edns:
                    self.data_store["edns"][case_id] = edns[case_id]
                    return edns[case_id]
        
        # Recargar personas y suministros también
        self._load_data()
        return None
    
    def update_edn(self, case_id: str, edn: Dict[str, Any]) -> bool:
        """
        Actualiza un EDN en edn.json y sincroniza con personas.json y suministros.json
        
        Args:
            case_id: ID del caso
            edn: Diccionario con el EDN a guardar
            
        Returns:
            True si se actualizó correctamente, False en caso contrario
        """
        try:
            # Cargar EDNs existentes
            edn_path = self.files["edn"]
            if edn_path.exists():
                with open(edn_path, "r", encoding="utf-8") as f:
                    edns = json.load(f)
            else:
                edns = {}
            
            # Actualizar EDN
            edns[case_id] = edn
            
            # Guardar
            with open(edn_path, "w", encoding="utf-8") as f:
                json.dump(edns, f, indent=2, ensure_ascii=False)
            
            # Actualizar en memoria
            self.data_store["edns"][case_id] = edn
            
            # Sincronizar unified_context con personas.json y suministros.json
            unified_context = edn.get('unified_context', {})
            if unified_context:
                rut = unified_context.get('rut_client')
                client_name = unified_context.get('client_name')
                email = unified_context.get('email')
                phone = unified_context.get('phone')
                
                # Actualizar persona si hay RUT válido
                if rut and rut not in ['—', 'N/A', '']:
                    self._sync_persona(rut, client_name, email, phone)
                
                # Actualizar suministro si hay NIS válido
                nis = unified_context.get('service_nis')
                commune = unified_context.get('commune')
                address = unified_context.get('address_standard')
                
                if nis and nis not in ['—', 'N/A', '']:
                    self._sync_suministro(nis, commune, address)
            
            return True
        except Exception as e:
            print(f"Error actualizando EDN en edn.json: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _sync_persona(self, rut: str, nombre: str = None, email: str = None, telefono: str = None):
        """Sincroniza datos de persona desde EDN a personas.json"""
        personas_path = self.files["personas"]
        if not personas_path.exists():
            return
        
        try:
            with open(personas_path, "r", encoding="utf-8") as f:
                personas = json.load(f)
            
            # Buscar persona por RUT
            persona_encontrada = None
            for idx, persona in enumerate(personas):
                if persona.get("rut") == rut:
                    persona_encontrada = idx
                    break
            
            if persona_encontrada is not None:
                # Actualizar persona existente
                if nombre and nombre not in ['—', 'N/A', '']:
                    personas[persona_encontrada]["nombre"] = nombre
                if email:
                    personas[persona_encontrada]["email"] = email
                if telefono:
                    personas[persona_encontrada]["telefono"] = telefono
            else:
                # Crear nueva persona si no existe
                nueva_persona = {
                    "id": len(personas) + 1,
                    "rut": rut,
                    "nombre": nombre if nombre and nombre not in ['—', 'N/A', ''] else f"Cliente {rut}",
                    "email": email,
                    "telefono": telefono
                }
                personas.append(nueva_persona)
            
            # Guardar
            with open(personas_path, "w", encoding="utf-8") as f:
                json.dump(personas, f, indent=2, ensure_ascii=False)
            
            # Actualizar en memoria (self.personas es un dict indexado por RUT)
            if persona_encontrada is not None:
                self.data_store["personas"][rut] = personas[persona_encontrada]
            else:
                self.data_store["personas"][rut] = nueva_persona
        except Exception as e:
            print(f"Error sincronizando persona: {e}")
    
    def _sync_suministro(self, nis: str, comuna: str = None, direccion: str = None):
        """Sincroniza datos de suministro desde EDN a suministros.json"""
        suministros_path = self.files["suministros"]
        if not suministros_path.exists():
            return
        
        try:
            with open(suministros_path, "r", encoding="utf-8") as f:
                suministros = json.load(f)
            
            # Buscar suministro por NIS
            suministro_encontrado = None
            for idx, suministro in enumerate(suministros):
                if suministro.get("nis") == nis:
                    suministro_encontrado = idx
                    break
            
            if suministro_encontrado is not None:
                # Actualizar suministro existente
                if comuna and comuna not in ['—', 'N/A', '']:
                    suministros[suministro_encontrado]["comuna"] = comuna
                if direccion and direccion not in ['—', 'N/A', '']:
                    suministros[suministro_encontrado]["direccion"] = direccion
            else:
                # Crear nuevo suministro si no existe
                nuevo_suministro = {
                    "id": len(suministros) + 1,
                    "nis": nis,
                    "comuna": comuna if comuna and comuna not in ['—', 'N/A', ''] else "Desconocida",
                    "direccion": direccion,
                    "numero_cliente": None
                }
                suministros.append(nuevo_suministro)
            
            # Guardar
            with open(suministros_path, "w", encoding="utf-8") as f:
                json.dump(suministros, f, indent=2, ensure_ascii=False)
            
            # Actualizar en memoria
            comuna_key = comuna if comuna and comuna not in ['—', 'N/A', ''] else "Desconocida"
            key = f"{nis}-{comuna_key}"
            if suministro_encontrado is not None:
                self.data_store["suministros"][key] = suministros[suministro_encontrado]
            else:
                self.data_store["suministros"][key] = nuevo_suministro
        except Exception as e:
            print(f"Error sincronizando suministro: {e}")
    
    @property
    def casos(self):
        """Propiedad para acceder a casos de manera compatible"""
        return self.data_store.get("casos", [])
    
    @property
    def personas(self):
        """Propiedad para acceder a personas de manera compatible"""
        return self.data_store.get("personas", {})
    
    @property
    def suministros(self):
        """Propiedad para acceder a suministros de manera compatible"""
        return self.data_store.get("suministros", {})

