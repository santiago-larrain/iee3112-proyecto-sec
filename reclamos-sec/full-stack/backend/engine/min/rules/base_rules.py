"""
Reglas base de validación compartidas entre diferentes tipos de casos
"""

from typing import Dict, Any, Optional
from datetime import datetime
import sys
from pathlib import Path

# Agregar path para imports
backend_dir = Path(__file__).parent.parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from models import ChecklistStatus, DocumentType


def rule_check_response_deadline(edn: Dict[str, Any]) -> Dict[str, Any]:
    """
    A.1. Validación de Plazo de Respuesta
    Verifica que la respuesta de la empresa esté dentro de los 30 días corridos.
    """
    fecha_ingreso_str = edn.get("fecha_ingreso") or edn.get("compilation_metadata", {}).get("case_id", "")
    response_date_str = None
    
    # Buscar fecha en carta de respuesta
    doc_inventory = edn.get("document_inventory", {})
    for doc in doc_inventory.get("level_1_critical", []):
        if doc.get("type") == DocumentType.CARTA_RESPUESTA.value:
            extracted_data = doc.get("extracted_data", {})
            response_date_str = extracted_data.get("response_date")
            if response_date_str:
                break
    
    status = ChecklistStatus.REVISION_MANUAL.value
    evidence = "Fechas no disponibles para cálculo."
    evidence_data = None
    
    if fecha_ingreso_str and response_date_str:
        try:
            # Intentar parsear fecha de ingreso desde case_id (formato: YYMMDD-XXXXXX)
            if len(fecha_ingreso_str) >= 6 and '-' in fecha_ingreso_str:
                year = '20' + fecha_ingreso_str[:2]
                month = fecha_ingreso_str[2:4]
                day = fecha_ingreso_str[4:6]
                fecha_ingreso = datetime(int(year), int(month), int(day))
            else:
                fecha_ingreso = datetime.fromisoformat(fecha_ingreso_str.replace('Z', '+00:00'))
            
            # Parsear fecha de respuesta
            fecha_respuesta = datetime.fromisoformat(response_date_str.replace('Z', '+00:00'))
            delta = (fecha_respuesta - fecha_ingreso).days
            
            if delta <= 30:
                status = ChecklistStatus.CUMPLE.value
                evidence = f"En Plazo ({delta} días)"
            else:
                status = ChecklistStatus.NO_CUMPLE.value
                evidence = f"Fuera de Plazo ({delta} días) - Causal de Instrucción Inmediata"
            
            # Agregar datos con source si está disponible
            for doc in doc_inventory.get("level_1_critical", []):
                if doc.get("type") == DocumentType.CARTA_RESPUESTA.value:
                    evidence_data = {
                        "file_id": doc.get("file_id"),
                        "page_index": 0,  # Por ahora, asumir primera página
                        "coordinates": None
                    }
                    break
        except (ValueError, TypeError) as e:
            pass  # Mantener como REVISION_MANUAL
    
    return {
        "status": status,
        "evidence": evidence,
        "evidence_data": evidence_data
    }


def rule_check_previous_claim_trace(edn: Dict[str, Any]) -> Dict[str, Any]:
    """
    A.2. Trazabilidad del Reclamo Previo
    Verifica si la Carta de Respuesta cita un ID de reclamo interno.
    """
    doc_inventory = edn.get("document_inventory", {})
    id_reclamo = None
    evidence_data = None
    
    for doc in doc_inventory.get("level_1_critical", []):
        if doc.get("type") == DocumentType.CARTA_RESPUESTA.value:
            extracted_data = doc.get("extracted_data", {})
            id_reclamo = extracted_data.get("cnr_reference") or extracted_data.get("resolution_number")
            if not id_reclamo:
                # Buscar en nombre de archivo
                import re
                original_name = doc.get("original_name", "")
                match = re.search(r'(\d{6,10})', original_name)
                if match:
                    id_reclamo = match.group(1)
            
            if id_reclamo:
                evidence_data = {
                    "file_id": doc.get("file_id"),
                    "page_index": 0,
                    "coordinates": None
                }
                break
    
    if id_reclamo:
        status = ChecklistStatus.CUMPLE.value
        evidence = f"Vinculación Correcta (Ticket #{id_reclamo})"
    else:
        status = ChecklistStatus.REVISION_MANUAL.value
        evidence = "No se detecta referencia a reclamo previo"
    
    return {
        "status": status,
        "evidence": evidence,
        "evidence_data": evidence_data
    }


def rule_check_materia_consistency(edn: Dict[str, Any]) -> Dict[str, Any]:
    """
    A.3. Competencia de la Materia
    Verifica que la materia clasificada coincida con los documentos adjuntos.
    """
    materia = edn.get("materia", "").upper()
    doc_inventory = edn.get("document_inventory", {})
    
    has_ot = any(
        doc.get("type") == DocumentType.ORDEN_TRABAJO.value
        for doc in doc_inventory.get("level_1_critical", [])
    )
    
    status = ChecklistStatus.REVISION_MANUAL.value
    evidence = "No se pudo verificar coherencia documental."
    evidence_data = None
    
    if "CNR" in materia or "RECUPERACION" in materia:
        if has_ot:
            status = ChecklistStatus.CUMPLE.value
            evidence = f"Coherencia Documental (Mat: {materia})"
            # Buscar OT para evidence_data
            for doc in doc_inventory.get("level_1_critical", []):
                if doc.get("type") == DocumentType.ORDEN_TRABAJO.value:
                    evidence_data = {
                        "file_id": doc.get("file_id"),
                        "page_index": 0,
                        "coordinates": None
                    }
                    break
        else:
            status = ChecklistStatus.NO_CUMPLE.value
            evidence = f"Incoherencia: Materia '{materia}' pero falta OT de Irregularidad."
    
    return {
        "status": status,
        "evidence": evidence,
        "evidence_data": evidence_data
    }


def rule_check_ot_exists(edn: Dict[str, Any]) -> Dict[str, Any]:
    """
    B.1. Existencia de Orden de Trabajo (OT)
    Verifica la presencia de una Orden de Trabajo en los documentos críticos.
    """
    doc_inventory = edn.get("document_inventory", {})
    ot_docs = [
        doc for doc in doc_inventory.get("level_1_critical", [])
        if doc.get("type") == DocumentType.ORDEN_TRABAJO.value
    ]
    
    if ot_docs:
        # Extraer número de OT si está disponible
        ot_number = None
        for doc in ot_docs:
            extracted_data = doc.get("extracted_data", {})
            ot_number = extracted_data.get("ot_number")
            if ot_number:
                break
        
        evidence = f"OT Adjunta (Folio {ot_number})" if ot_number else "OT Adjunta"
        evidence_data = {
            "file_id": ot_docs[0].get("file_id"),
            "page_index": 0,
            "coordinates": None
        }
        status = ChecklistStatus.CUMPLE.value
    else:
        status = ChecklistStatus.NO_CUMPLE.value
        evidence = "Falta OT - Imposible acreditar hecho"
        evidence_data = None
    
    return {
        "status": status,
        "evidence": evidence,
        "evidence_data": evidence_data
    }


def rule_check_photos_existence(edn: Dict[str, Any]) -> Dict[str, Any]:
    """
    B.2. Existencia de Evidencia Fotográfica
    Verifica la presencia de al menos una imagen como evidencia fotográfica.
    """
    doc_inventory = edn.get("document_inventory", {})
    foto_docs = [
        doc for doc in doc_inventory.get("level_2_supporting", [])
        if doc.get("type") == DocumentType.EVIDENCIA_FOTOGRAFICA.value
    ]
    
    photo_count = len(foto_docs)
    
    if photo_count >= 1:
        # Verificar calidad (si hay metadata de OCR confidence)
        low_quality = False
        for doc in foto_docs:
            metadata = doc.get("metadata", {})
            confidence = metadata.get("extraction_confidence", 1.0)
            if confidence < 0.5:
                low_quality = True
                break
        
        if low_quality:
            status = ChecklistStatus.REVISION_MANUAL.value
            evidence = f"Fotos insuficientes o de baja calidad (OCR confidence < 50%)"
        else:
            status = ChecklistStatus.CUMPLE.value
            evidence = f"Set Fotográfico ({photo_count} imágenes)"
        
        evidence_data = {
            "file_ids": [doc.get("file_id") for doc in foto_docs[:3]],  # Primeras 3
            "count": photo_count
        }
    else:
        status = ChecklistStatus.NO_CUMPLE.value
        evidence = "Sin evidencia visual"
        evidence_data = None
    
    return {
        "status": status,
        "evidence": evidence,
        "evidence_data": evidence_data
    }


def rule_check_calculation_table(edn: Dict[str, Any]) -> Dict[str, Any]:
    """
    B.3. Existencia de Memoria de Cálculo
    Verifica la presencia de una Tabla de Cálculo o documento similar.
    """
    doc_inventory = edn.get("document_inventory", {})
    calculo_docs = [
        doc for doc in doc_inventory.get("level_1_critical", [])
        if doc.get("type") == DocumentType.TABLA_CALCULO.value
    ]
    
    if calculo_docs:
        status = ChecklistStatus.CUMPLE.value
        evidence = "Tabla Detallada Disponible"
        evidence_data = {
            "file_id": calculo_docs[0].get("file_id"),
            "page_index": 0,
            "coordinates": None
        }
    else:
        status = ChecklistStatus.NO_CUMPLE.value
        evidence = "Falta desglose de deuda"
        evidence_data = None
    
    return {
        "status": status,
        "evidence": evidence,
        "evidence_data": evidence_data
    }


def rule_check_notification_proof(edn: Dict[str, Any]) -> Dict[str, Any]:
    """
    B.4. Acreditación de Notificación
    Verifica la acreditación de la notificación de cobro al cliente.
    """
    doc_inventory = edn.get("document_inventory", {})
    keywords = ["carta certificada", "notificación personal", "firma", "notificado"]
    found_keywords = []
    evidence_data = None
    
    for level in ["level_1_critical", "level_2_supporting"]:
        for doc in doc_inventory.get(level, []):
            original_name = doc.get("original_name", "").lower()
            extracted_data = doc.get("extracted_data", {})
            text_content = str(extracted_data).lower()
            
            for keyword in keywords:
                if keyword in original_name or keyword in text_content:
                    if keyword not in found_keywords:
                        found_keywords.append(keyword)
                        if not evidence_data:
                            evidence_data = {
                                "file_id": doc.get("file_id"),
                                "page_index": 0,
                                "coordinates": None
                            }
    
    if found_keywords:
        status = ChecklistStatus.CUMPLE.value
        keyword_display = found_keywords[0].title()
        evidence = f"Cliente Notificado (Ref: {keyword_display})"
    else:
        status = ChecklistStatus.REVISION_MANUAL.value
        evidence = "No se acredita entrega de notificación de cobro"
    
    return {
        "status": status,
        "evidence": evidence,
        "evidence_data": evidence_data
    }

