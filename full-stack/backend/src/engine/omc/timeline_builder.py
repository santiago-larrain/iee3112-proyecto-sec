"""
Constructor de Timeline Temporal
Extrae fechas clave del EDN y construye una línea temporal con deltas y warnings
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import re
import logging

logger = logging.getLogger(__name__)


def build_timeline(edn: Dict[str, Any]) -> Dict[str, Any]:
    """
    Construye un análisis temporal del caso extrayendo fechas clave
    
    Args:
        edn: Expediente Digital Normalizado (dict o objeto Pydantic)
        
    Returns:
        Diccionario con estructura:
        {
            "events": [...],
            "critical_deltas": {...},
            "warnings": [...],
            "incomplete": bool
        }
    """
    # Convertir a dict si es necesario
    if hasattr(edn, 'model_dump'):
        edn = edn.model_dump()
    elif hasattr(edn, 'dict'):
        edn = edn.dict()
    
    events = []
    warnings = []
    incomplete = False
    
    # Extraer fechas de unified_context
    unified_context = edn.get("unified_context", {})
    fecha_ingreso = edn.get("fecha_ingreso")
    
    # Extraer fechas de document_inventory
    document_inventory = edn.get("document_inventory", {})
    
    # Buscar fechas en documentos críticos
    for doc in document_inventory.get("level_1_critical", []):
        extracted_data = doc.get("extracted_data", {})
        doc_type = doc.get("type", "")
        file_id = doc.get("file_id", "")
        
        # Fecha de respuesta (CARTA_RESPUESTA)
        if doc_type == "CARTA_RESPUESTA":
            response_date = extracted_data.get("response_date")
            if response_date:
                fecha_parsed = _parse_date(response_date)
                if fecha_parsed:
                    events.append({
                        "date": fecha_parsed.isoformat(),
                        "event": "Respuesta de la Empresa",
                        "source_doc": file_id,
                        "type": "respuesta"
                    })
        
        # Fecha de inspección (ORDEN_TRABAJO)
        if doc_type == "ORDEN_TRABAJO":
            visit_date = extracted_data.get("visit_date") or extracted_data.get("fecha_visita")
            if visit_date:
                fecha_parsed = _parse_date(visit_date)
                if fecha_parsed:
                    events.append({
                        "date": fecha_parsed.isoformat(),
                        "event": "Inspección Técnica",
                        "source_doc": file_id,
                        "type": "inspeccion"
                    })
        
        # Período de cobro (TABLA_CALCULO)
        if doc_type == "TABLA_CALCULO":
            period_start = extracted_data.get("period_start") or extracted_data.get("fecha_inicio")
            period_end = extracted_data.get("period_end") or extracted_data.get("fecha_termino")
            
            if period_start:
                fecha_parsed = _parse_date(period_start)
                if fecha_parsed:
                    events.append({
                        "date": fecha_parsed.isoformat(),
                        "event": "Inicio Período de Cobro",
                        "source_doc": file_id,
                        "type": "periodo_inicio"
                    })
            
            if period_end:
                fecha_parsed = _parse_date(period_end)
                if fecha_parsed:
                    events.append({
                        "date": fecha_parsed.isoformat(),
                        "event": "Fin Período de Cobro",
                        "source_doc": file_id,
                        "type": "periodo_fin"
                    })
    
    # Buscar fechas en consolidated_facts
    consolidated_facts = edn.get("consolidated_facts", {})
    if consolidated_facts:
        fecha_inicio = consolidated_facts.get("fecha_inicio")
        fecha_termino = consolidated_facts.get("fecha_termino")
        
        if fecha_inicio:
            fecha_parsed = _parse_date(fecha_inicio)
            if fecha_parsed:
                events.append({
                    "date": fecha_parsed.isoformat(),
                    "event": "Inicio Período CNR",
                    "source_doc": None,
                    "type": "periodo_inicio"
                })
        
        if fecha_termino:
            fecha_parsed = _parse_date(fecha_termino)
            if fecha_parsed:
                events.append({
                    "date": fecha_parsed.isoformat(),
                    "event": "Fin Período CNR",
                    "source_doc": None,
                    "type": "periodo_fin"
                })
    
    # Agregar fecha de ingreso del reclamo
    if fecha_ingreso:
        fecha_parsed = _parse_date(fecha_ingreso)
        if fecha_parsed:
            events.append({
                "date": fecha_parsed.isoformat(),
                "event": "Ingreso del Reclamo",
                "source_doc": None,
                "type": "reclamo"
            })
    
    # Ordenar eventos por fecha
    events.sort(key=lambda x: x["date"])
    
    # Calcular deltas entre eventos críticos
    critical_deltas = {}
    
    # Buscar eventos clave
    fecha_reclamo = next((e for e in events if e.get("type") == "reclamo"), None)
    fecha_respuesta = next((e for e in events if e.get("type") == "respuesta"), None)
    fecha_inspeccion = next((e for e in events if e.get("type") == "inspeccion"), None)
    fecha_periodo_inicio = next((e for e in events if e.get("type") == "periodo_inicio"), None)
    fecha_periodo_fin = next((e for e in events if e.get("type") == "periodo_fin"), None)
    
    # Delta: Reclamo → Respuesta
    if fecha_reclamo and fecha_respuesta:
        delta = _calculate_delta(fecha_reclamo["date"], fecha_respuesta["date"])
        if delta is not None:
            critical_deltas["reclamo_to_respuesta"] = delta
            events[events.index(fecha_respuesta)]["delta_days"] = delta
            
            # Warning: Silencio administrativo (>30 días)
            if delta > 30:
                warnings.append(f"Silencio administrativo detectado: {delta} días entre reclamo y respuesta (límite: 30 días)")
    
    # Delta: Inspección → Cobro
    if fecha_inspeccion and fecha_periodo_inicio:
        delta = _calculate_delta(fecha_inspeccion["date"], fecha_periodo_inicio["date"])
        if delta is not None:
            critical_deltas["inspeccion_to_cobro"] = delta
    
    # Delta: Período de cobro (duración)
    if fecha_periodo_inicio and fecha_periodo_fin:
        delta = _calculate_delta(fecha_periodo_inicio["date"], fecha_periodo_fin["date"])
        if delta is not None:
            meses = delta / 30.0
            critical_deltas["periodo_cobro_meses"] = meses
            
            # Warning: Período retroactivo ilegal (>12 meses)
            if meses > 12:
                warnings.append(f"Periodo retroactivo excede 12 meses: {meses:.1f} meses")
    
    # Marcar como incompleto si faltan fechas críticas
    if not fecha_reclamo:
        incomplete = True
        warnings.append("Falta fecha de ingreso del reclamo")
    
    if not fecha_respuesta:
        incomplete = True
        warnings.append("Falta fecha de respuesta de la empresa")
    
    return {
        "events": events,
        "critical_deltas": critical_deltas,
        "warnings": warnings,
        "incomplete": incomplete
    }


def _parse_date(date_str: Any) -> Optional[datetime]:
    """
    Parsea una fecha desde string con múltiples formatos
    
    Args:
        date_str: String de fecha en varios formatos
        
    Returns:
        datetime object o None si no se puede parsear
    """
    if not date_str:
        return None
    
    # Convertir a string si es necesario
    if isinstance(date_str, datetime):
        return date_str
    
    date_str = str(date_str).strip()
    
    # Formatos comunes
    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%d-%m-%y",
        "%d/%m/%y",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    # Intentar parsear desde case_id (formato: YYMMDD-XXXXXX)
    if len(date_str) >= 6 and '-' in date_str:
        try:
            year = '20' + date_str[:2]
            month = date_str[2:4]
            day = date_str[4:6]
            return datetime(int(year), int(month), int(day))
        except (ValueError, IndexError):
            pass
    
    logger.warning(f"No se pudo parsear fecha: {date_str}")
    return None


def _calculate_delta(date1_str: str, date2_str: str) -> Optional[int]:
    """
    Calcula la diferencia en días entre dos fechas
    
    Args:
        date1_str: Primera fecha (ISO format)
        date2_str: Segunda fecha (ISO format)
        
    Returns:
        Diferencia en días (positiva si date2 > date1) o None si hay error
    """
    try:
        date1 = datetime.fromisoformat(date1_str.replace('Z', '+00:00'))
        date2 = datetime.fromisoformat(date2_str.replace('Z', '+00:00'))
        
        # Normalizar a UTC si tienen timezone
        if date1.tzinfo:
            date1 = date1.replace(tzinfo=None)
        if date2.tzinfo:
            date2 = date2.replace(tzinfo=None)
        
        delta = date2 - date1
        return delta.days
    except (ValueError, AttributeError) as e:
        logger.warning(f"Error calculando delta entre {date1_str} y {date2_str}: {e}")
        return None

