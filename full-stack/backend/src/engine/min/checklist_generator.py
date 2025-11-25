"""
Generador de Checklist usando el Motor de Inferencia Normativa (MIN)
Wrapper que delega la generación al RuleEngine
"""

from typing import Dict, Any
from src.models import Checklist
from .rule_engine import RuleEngine


class ChecklistGenerator:
    """Genera checklist estructurado usando el MIN y JSONs configurables"""
    
    def __init__(self):
        """Inicializa el generador con el RuleEngine"""
        self.rule_engine = RuleEngine()
    
    def generate_checklist(self, edn: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera checklist completo basado en el EDN usando el MIN
        
        Args:
            edn: Expediente Digital Normalizado (dict o objeto Pydantic)
            
        Returns:
            Checklist estructurado con grupos A, B, C (como diccionario para compatibilidad)
        """
        # Convertir objeto Pydantic a diccionario si es necesario
        if isinstance(edn, dict):
            edn_dict = edn
        elif hasattr(edn, 'model_dump'):
            edn_dict = edn.model_dump()
        elif hasattr(edn, 'dict'):
            edn_dict = edn.dict()
        else:
            edn_dict = edn
        
        # Usar RuleEngine para generar el checklist
        checklist = self.rule_engine.generate_checklist(edn_dict)
        
        # Convertir Checklist (Pydantic) a diccionario para compatibilidad
        def item_to_dict(item):
            """Convierte un ChecklistItem a diccionario"""
            if hasattr(item, 'model_dump'):
                return item.model_dump()
            elif hasattr(item, 'dict'):
                return item.dict()
            elif isinstance(item, dict):
                return item
            return item
        
        return {
            "group_a_admisibilidad": [
                item_to_dict(item) for item in (checklist.group_a_admisibilidad or [])
            ],
            "group_b_instruccion": [
                item_to_dict(item) for item in (checklist.group_b_instruccion or [])
            ],
            "group_c_analisis": [
                item_to_dict(item) for item in (checklist.group_c_analisis or [])
            ],
            "metadata": {
                "generated_at": checklist.metadata.get("generated_at") if checklist.metadata else None,
                "case_id": edn_dict.get("compilation_metadata", {}).get("case_id", "UNKNOWN")
            }
        }

