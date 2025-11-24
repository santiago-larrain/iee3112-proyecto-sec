"""
Categorizador de documentos por función (reclamo/respuesta, informe/evidencias, historial/cálculos, otros)
"""

from typing import Dict, List, Any, Optional

def categorize_document_by_function(doc_type: str) -> str:
    """
    Categoriza un documento por su función en el proceso de reclamo
    
    Args:
        doc_type: Tipo de documento (CARTA_RESPUESTA, TABLA_CALCULO, etc.)
        
    Returns:
        Categoría funcional: 'reclamo_respuesta', 'informe_evidencias', 'historial_calculos', 'otros'
    """
    # Reclamo y Respuesta
    if doc_type == "CARTA_RESPUESTA":
        return "reclamo_respuesta"
    
    # Informe de Laboratorio y Evidencias
    if doc_type in ["INFORME_CNR", "EVIDENCIA_FOTOGRAFICA", "ORDEN_TRABAJO"]:
        return "informe_evidencias"
    
    # Historial de Consumo y Cálculos
    if doc_type in ["TABLA_CALCULO", "GRAFICO_CONSUMO"]:
        return "historial_calculos"
    
    # Otros
    return "otros"


def add_functional_categories(document_inventory: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agrega categorías funcionales al inventario de documentos
    
    Args:
        document_inventory: Inventario de documentos con estructura antigua (level_1, level_2, level_0)
        
    Returns:
        Inventario con categorías funcionales agregadas
    """
    # Inicializar categorías funcionales
    functional_categories = {
        "reclamo_respuesta": [],
        "informe_evidencias": [],
        "historial_calculos": [],
        "otros": []
    }
    
    # Procesar documentos de level_1_critical y level_2_supporting
    for level in ["level_1_critical", "level_2_supporting"]:
        for doc in document_inventory.get(level, []):
            doc_type = doc.get("type", "OTROS")
            category = categorize_document_by_function(doc_type)
            functional_categories[category].append(doc)
    
    # Agregar categorías funcionales al inventario
    document_inventory.update(functional_categories)
    
    return document_inventory


def ensure_functional_categories(document_inventory: Dict[str, Any]) -> Dict[str, Any]:
    """
    Asegura que el inventario tenga categorías funcionales.
    Si no las tiene, las genera desde la estructura antigua.
    
    Args:
        document_inventory: Inventario de documentos
        
    Returns:
        Inventario con categorías funcionales garantizadas
    """
    # Si ya tiene categorías funcionales, verificar que estén completas
    has_functional = any(
        key in document_inventory 
        for key in ["reclamo_respuesta", "informe_evidencias", "historial_calculos", "otros"]
    )
    
    if not has_functional:
        # Generar desde estructura antigua
        return add_functional_categories(document_inventory)
    
    # Si ya tiene, asegurar que todas las categorías existan (pueden estar vacías)
    for category in ["reclamo_respuesta", "informe_evidencias", "historial_calculos", "otros"]:
        if category not in document_inventory:
            document_inventory[category] = []
    
    return document_inventory

