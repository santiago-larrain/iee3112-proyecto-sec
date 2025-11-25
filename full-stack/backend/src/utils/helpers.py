import json
from pathlib import Path
from typing import Dict, Any
from src.config import MOCK_CASOS_PATH
from src.models import ExpedienteDigitalNormalizado, CaseStatus

def load_mock_cases() -> Dict[str, Any]:
    """Carga los casos de prueba desde el archivo mock."""
    try:
        with open(MOCK_CASOS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"casos": []}
    except json.JSONDecodeError:
        return {"casos": []}

def determine_case_status(caso: Dict[str, Any]) -> CaseStatus:
    """Determina el estado de un caso basado en su checklist."""
    # Lógica de ejemplo, puedes adaptarla
    checklist = caso.get("checklist")
    if not checklist:
        return CaseStatus.PENDIENTE

    all_validated = True
    has_failures = False
    for group_key in ["group_a_admisibilidad", "group_b_instruccion", "group_c_analisis"]:
        group = checklist.get(group_key, [])
        for item in group:
            if item.get("status") == "NO_CUMPLE":
                has_failures = True
            if not item.get("validated", False):
                all_validated = False
    
    if all_validated and not has_failures:
        return CaseStatus.RESUELTO
    elif has_failures or not all_validated:
        return CaseStatus.EN_REVISION
    
    return CaseStatus.PENDIENTE

def create_empty_edn(case_id: str) -> Dict[str, Any]:
    """Crea un EDN vacío para un caso no encontrado."""
    return {
        "compilation_metadata": {
            "case_id": case_id,
            "status": "NOT_FOUND"
        },
        "unified_context": {},
        "document_inventory": {
            "level_1_critical": [],
            "level_2_supporting": [],
            "level_0_missing": []
        },
        "checklist": None
    }

def ensure_edn_completeness(edn: dict) -> dict:
    """Asegura que el EDN tenga todos los campos requeridos con valores por defecto."""
    edn.setdefault("compilation_metadata", {})
    edn.setdefault("unified_context", {})
    edn.setdefault("document_inventory", {
        "level_1_critical": [],
        "level_2_supporting": [],
        "level_0_missing": []
    })
    edn.setdefault("checklist", None)
    return edn
