"""
Generador de Checklist usando el Motor de Inferencia Normativa (MIN)
Wrapper que delega la generación al RuleEngine
"""

from typing import Dict, Any
from models import Checklist
from engine.min import RuleEngine


class ChecklistGenerator:
    """Genera checklist estructurado usando el MIN y JSONs configurables"""
    
    def __init__(self):
        """Inicializa el generador con el RuleEngine"""
        self.rule_engine = RuleEngine()
    
    def generate_checklist(self, edn: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera checklist completo basado en el EDN usando el MIN
        
        Args:
            edn: Expediente Digital Normalizado
            
        Returns:
            Checklist estructurado con grupos A, B, C (como diccionario para compatibilidad)
        """
        # Usar RuleEngine para generar el checklist
        checklist = self.rule_engine.generate_checklist(edn)
        
        # Convertir Checklist (Pydantic) a diccionario para compatibilidad
        return {
            "group_a_admisibilidad": [
                item.dict() for item in (checklist.group_a_admisibilidad or [])
            ],
            "group_b_instruccion": [
                item.dict() for item in (checklist.group_b_instruccion or [])
            ],
            "group_c_analisis": [
                item.dict() for item in (checklist.group_c_analisis or [])
            ],
            "metadata": {
                "generated_at": checklist.metadata.get("generated_at") if checklist.metadata else None,
                "case_id": edn.get("compilation_metadata", {}).get("case_id", "UNKNOWN")
            }
        }
