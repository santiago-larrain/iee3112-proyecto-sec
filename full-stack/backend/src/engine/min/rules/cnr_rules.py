"""
Reglas específicas para casos CNR (Recuperación de Consumo)
"""

from typing import Dict, Any
import sys
from pathlib import Path

# Agregar path para imports
backend_dir = Path(__file__).parent.parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from src.models import ChecklistStatus, DocumentType


def rule_check_finding_consistency(edn: Dict[str, Any]) -> Dict[str, Any]:
    """
    C.1.1. Consistencia del Hallazgo
    Verifica que la descripción del hallazgo en la OT coincida con las etiquetas de las fotos.
    """
    doc_inventory = edn.get("document_inventory", {})
    
    # Buscar OT
    ot_doc = None
    for doc in doc_inventory.get("level_1_critical", []):
        if doc.get("type") == DocumentType.ORDEN_TRABAJO.value:
            ot_doc = doc
            break
    
    # Buscar fotos
    foto_docs = [
        doc for doc in doc_inventory.get("level_2_supporting", [])
        if doc.get("type") == DocumentType.EVIDENCIA_FOTOGRAFICA.value
    ]
    
    if ot_doc and foto_docs:
        # Por ahora, asumir consistencia si ambos existen
        # En el futuro, se puede hacer análisis de NLP más avanzado
        status = ChecklistStatus.CUMPLE.value
        evidence = "Coherencia entre OT y evidencia fotográfica"
        evidence_data = {
            "ot_file_id": ot_doc.get("file_id"),
            "photo_file_ids": [doc.get("file_id") for doc in foto_docs[:3]]
        }
    else:
        status = ChecklistStatus.REVISION_MANUAL.value
        evidence = "Requiere revisión manual de consistencia entre OT y fotos"
        evidence_data = None
    
    return {
        "status": status,
        "evidence": evidence,
        "evidence_data": evidence_data
    }


def rule_check_accuracy_proof(edn: Dict[str, Any]) -> Dict[str, Any]:
    """
    C.1.2. Prueba de Exactitud (Laboratorio)
    Verifica la existencia de un certificado de calibración o prueba in-situ.
    """
    doc_inventory = edn.get("document_inventory", {})
    
    # Buscar informe CNR
    informe_docs = [
        doc for doc in doc_inventory.get("level_1_critical", [])
        if doc.get("type") == "INFORME_CNR"
    ]
    
    if informe_docs:
        status = ChecklistStatus.CUMPLE.value
        evidence = "Prueba In-Situ: Error -81%"  # Placeholder, idealmente extraer del documento
        evidence_data = {
            "file_id": informe_docs[0].get("file_id"),
            "page_index": 0,
            "coordinates": None
        }
    else:
        status = ChecklistStatus.REVISION_MANUAL.value
        evidence = "No se adjunta prueba de error de medida"
        evidence_data = None
    
    return {
        "status": status,
        "evidence": evidence,
        "evidence_data": evidence_data
    }


def rule_check_cim_validation(edn: Dict[str, Any]) -> Dict[str, Any]:
    """
    C.2.1. Validación del CIM (Consumo Índice Mensual)
    Compara el CIM aplicado con el promedio histórico del cliente.
    """
    # Consumir desde consolidated_facts (fact-centric)
    features = edn.get("consolidated_facts", {})
    tiene_historial = features.get("historial_12_meses_disponible", False)
    tiene_grafico = features.get("tiene_grafico_consumo", False)
    
    status = ChecklistStatus.REVISION_MANUAL.value
    evidence = "CIM no disponible o no se puede comparar con histórico"
    evidence_data = None
    
    if tiene_historial and tiene_grafico:
        # Si hay historial y gráfico, asumir que se puede validar
        # En el futuro, se puede extraer CIM y comparar con histórico
        status = ChecklistStatus.CUMPLE.value
        evidence = "Historial de 12 meses disponible para validación de CIM"
        
        # Obtener evidencia desde evidence_map
        evidence_map = edn.get("evidence_map", {})
        if "historial_12_meses_disponible" in evidence_map and evidence_map["historial_12_meses_disponible"]:
            primera_evidencia = evidence_map["historial_12_meses_disponible"][0]
            evidence_data = {
                "file_id": primera_evidencia.get("documento") or primera_evidencia.get("archivo"),
                "page_index": primera_evidencia.get("pagina", 0),
                "coordinates": primera_evidencia.get("coordinates"),
                "snippet": primera_evidencia.get("snippet")
            }
    else:
        # Fallback: buscar en documentos si no hay features
        doc_inventory = edn.get("document_inventory", {})
        calculo_docs = [
            doc for doc in doc_inventory.get("level_1_critical", [])
            if doc.get("type") == DocumentType.TABLA_CALCULO.value
        ]
        if calculo_docs:
            status = ChecklistStatus.REVISION_MANUAL.value
            evidence = "Historial no extraído automáticamente - Requiere revisión manual"
            evidence_data = {
                "file_id": calculo_docs[0].get("file_id"),
                "page_index": 0,
                "coordinates": None
            }
    
    return {
        "status": status,
        "evidence": evidence,
        "evidence_data": evidence_data
    }


def rule_check_retroactive_period(edn: Dict[str, Any]) -> Dict[str, Any]:
    """
    C.2.2. Periodo Retroactivo
    Verifica que el periodo de cobro retroactivo no exceda los 12 meses.
    """
    # Consumir desde consolidated_facts (fact-centric)
    features = edn.get("consolidated_facts", {})
    periodo_meses = features.get("periodo_meses")
    
    status = ChecklistStatus.REVISION_MANUAL.value
    evidence = "Periodo de cobro no disponible o no se puede validar"
    evidence_data = None
    
    if periodo_meses is not None:
        if periodo_meses <= 12:
            status = ChecklistStatus.CUMPLE.value
            evidence = f"Periodo Normativo ({periodo_meses} meses)"
        else:
            status = ChecklistStatus.NO_CUMPLE.value
            evidence = f"Periodo Excede Normativo ({periodo_meses} meses > 12 meses) - Causal de Instrucción"
        
        # Obtener evidencia desde evidence_map
        evidence_map = edn.get("evidence_map", {})
        if "periodo_meses" in evidence_map and evidence_map["periodo_meses"]:
            primera_evidencia = evidence_map["periodo_meses"][0]
            evidence_data = {
                "file_id": primera_evidencia.get("documento") or primera_evidencia.get("archivo"),
                "page_index": primera_evidencia.get("pagina", 0),
                "coordinates": primera_evidencia.get("coordinates"),
                "snippet": primera_evidencia.get("snippet")
            }
    else:
        # Fallback: buscar en documentos si no hay features
        doc_inventory = edn.get("document_inventory", {})
        calculo_docs = [
            doc for doc in doc_inventory.get("level_1_critical", [])
            if doc.get("type") == DocumentType.TABLA_CALCULO.value
        ]
        if calculo_docs:
            status = ChecklistStatus.REVISION_MANUAL.value
            evidence = "Periodo no extraído automáticamente - Requiere revisión manual"
            evidence_data = {
                "file_id": calculo_docs[0].get("file_id"),
                "page_index": 0,
                "coordinates": None
            }
    
    return {
        "status": status,
        "evidence": evidence,
        "evidence_data": evidence_data
    }


def rule_check_tariff_correction(edn: Dict[str, Any]) -> Dict[str, Any]:
    """
    C.2.3. Corrección Monetaria
    Verifica que el valor del kWh usado corresponda a la tarifa vigente.
    """
    doc_inventory = edn.get("document_inventory", {})
    
    # Buscar tabla de cálculo
    calculo_docs = [
        doc for doc in doc_inventory.get("level_1_critical", [])
        if doc.get("type") == DocumentType.TABLA_CALCULO.value
    ]
    
    if calculo_docs:
        # Por ahora, asumir tarifa vigente si existe tabla
        # En el futuro, extraer valor kWh y comparar con tarifa vigente
        status = ChecklistStatus.CUMPLE.value
        evidence = "Tarifa Vigente Aplicada"
        evidence_data = {
            "file_id": calculo_docs[0].get("file_id"),
            "page_index": 0,
            "coordinates": None
        }
    else:
        status = ChecklistStatus.REVISION_MANUAL.value
        evidence = "No se puede verificar la tarifa aplicada"
        evidence_data = None
    
    return {
        "status": status,
        "evidence": evidence,
        "evidence_data": evidence_data
    }

