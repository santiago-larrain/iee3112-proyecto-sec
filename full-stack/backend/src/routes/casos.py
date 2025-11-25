from fastapi import APIRouter, HTTPException, Request, Body, Response
from fastapi.responses import FileResponse, StreamingResponse
from typing import List, Optional, Dict, Any
import json
import os
from pathlib import Path
import logging

from src.models import (
    ExpedienteDigitalNormalizado,
    CaseSummary,
    CaseStatus,
    DocumentUpdateRequest,
    ChecklistItemUpdateRequest,
    ResolucionRequest,
    ResolucionResponse,
    UnifiedContextUpdateRequest,
    CerrarCasoRequest,
    ChecklistStatus,
    DocumentType
)
from src.database.json_db_manager import JSONDBManager
from src.engine.min.checklist_generator import ChecklistGenerator
from src.engine.omc.document_categorizer import ensure_functional_categories
from src.engine.mgr.resolucion_generator import ResolucionGenerator
from src.utils.helpers import (
    determine_case_status,
    load_mock_cases,
    create_empty_edn
)
# ensure_edn_completeness está definida localmente en este archivo (versión más completa)
from src.config import (
    DATABASE_DIR,
    DATA_DIR,
    EXAMPLE_CASES_DIR,
    FILES_DIR,
    MOCK_CASOS_PATH,
    RESOLUCIONES_DIR
)

router = APIRouter()

# Configuración del logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Inicialización de Singletons ---
db_manager = JSONDBManager(base_path=DATABASE_DIR)
checklist_generator = ChecklistGenerator()
resolucion_generator = ResolucionGenerator()

# --- Cache en memoria para cambios temporales ---
cases_store: Dict[str, Any] = {}

# --- Definición de Rutas ---
# Se utilizan variables del config para las rutas, aunque algunas son para lógica interna
db_path = DATABASE_DIR
json_db_dir = DATABASE_DIR
data_path = DATA_DIR
temp_dir = data_path / "temp_pdfs"
resoluciones_dir = RESOLUCIONES_DIR # Usando la ruta centralizada
documentos_path = db_path / "documentos.json"
personas_path = db_path / "personas.json"
suministros_path = db_path / "suministros.json"
example_cases_dir = EXAMPLE_CASES_DIR  # Ahora apunta directamente a FILES_DIR
files_dir = FILES_DIR
mock_casos_path = MOCK_CASOS_PATH

# --- Funciones Auxiliares ---

def get_mode(request: Request) -> str:
    """Obtiene el modo de la aplicación desde header o query param"""
    x_app_mode = request.headers.get("X-App-Mode")
    mode = request.query_params.get("mode")
    mode_value = (x_app_mode or mode or 'validate').lower()
    return mode_value if mode_value in ['test', 'validate'] else 'validate'

def _sort_summaries(summaries: List[CaseSummary], sort_by: str, reverse: bool = False) -> List[CaseSummary]:
    """Ordena los summaries por la columna especificada"""
    sort_key_map = {
        'case_id': lambda s: s.case_id,
        'client_name': lambda s: s.client_name.lower(),
        'rut_client': lambda s: s.rut_client.lower(),
        'materia': lambda s: s.materia.lower(),
        'monto_disputa': lambda s: s.monto_disputa or 0,
        'empresa': lambda s: s.empresa.lower(),
        'status': lambda s: s.status.value if hasattr(s.status, 'value') else str(s.status),
        'fecha_ingreso': lambda s: s.fecha_ingreso or ''
    }
    
    sort_key = sort_key_map.get(sort_by.lower())
    if sort_key:
        return sorted(summaries, key=sort_key, reverse=reverse)
    return summaries

# Inicializar generador de checklist
checklist_generator = ChecklistGenerator()

def ensure_edn_completeness(edn: dict) -> dict:
    """Asegura que el EDN tenga todos los campos requeridos con valores por defecto"""
    # Asegurar compilation_metadata
    if "compilation_metadata" not in edn:
        edn["compilation_metadata"] = {}
    if "case_id" not in edn["compilation_metadata"]:
        edn["compilation_metadata"]["case_id"] = "UNKNOWN"
    if "processing_timestamp" not in edn["compilation_metadata"]:
        from datetime import datetime, timezone
        edn["compilation_metadata"]["processing_timestamp"] = datetime.now(timezone.utc).isoformat()
    if "status" not in edn["compilation_metadata"]:
        edn["compilation_metadata"]["status"] = "COMPLETED"
    
    # Asegurar unified_context
    if "unified_context" not in edn:
        edn["unified_context"] = {}
    unified_context = edn["unified_context"]
    # Convertir None a strings por defecto
    unified_context["rut_client"] = unified_context.get("rut_client") or "N/A"
    unified_context["client_name"] = unified_context.get("client_name") or "N/A"
    unified_context["service_nis"] = unified_context.get("service_nis") or "N/A"
    unified_context["address_standard"] = unified_context.get("address_standard")  # Puede ser None
    unified_context["commune"] = unified_context.get("commune") or "Desconocida"
    unified_context["email"] = unified_context.get("email")  # Puede ser None
    unified_context["phone"] = unified_context.get("phone")  # Puede ser None
    
    # Asegurar document_inventory
    if "document_inventory" not in edn:
        edn["document_inventory"] = {
            "level_1_critical": [],
            "level_2_supporting": [],
            "level_0_missing": []
        }
    doc_inv = edn["document_inventory"]
    doc_inv.setdefault("level_1_critical", [])
    doc_inv.setdefault("level_2_supporting", [])
    doc_inv.setdefault("level_0_missing", [])
    
    # Asegurar categorías funcionales
    doc_inv = ensure_functional_categories(doc_inv)
    edn["document_inventory"] = doc_inv
    
    # Siempre regenerar checklist usando MIN (para asegurar tipo_caso correcto y estructura nueva)
    try:
        edn["checklist"] = checklist_generator.generate_checklist(edn)
    except Exception as e:
        print(f"Error generando checklist en ensure_edn_completeness: {e}")
        import traceback
        traceback.print_exc()
        # Checklist por defecto vacío
        edn["checklist"] = {
            "group_a_admisibilidad": [],
            "group_b_instruccion": [],
            "group_c_analisis": []
        }
    
    # Campos opcionales adicionales
    edn.setdefault("materia", None)
    edn.setdefault("monto_disputa", None)
    edn.setdefault("empresa", None)
    edn.setdefault("fecha_ingreso", None)
    edn.setdefault("alertas", [])
    
    return edn

def get_cases_data_with_mode(app_mode: str = 'validate'):
    """Obtiene casos según el modo especificado"""
    if app_mode == 'test':
        # Modo test: usar mock
        data = load_mock_cases()
        casos = []
        for caso_data in data["casos"]:
            case_id = caso_data["compilation_metadata"]["case_id"]
            if case_id in cases_store:
                stored = cases_store[case_id]
                if "document_inventory" in stored:
                    caso_data["document_inventory"] = stored["document_inventory"]
                if "checklist" in stored:
                    caso_data["checklist"] = stored["checklist"]
            casos.append(caso_data)
        return casos
    
    # Modo validate: casos reales
    return get_cases_data()

def get_cases_data():
    """Obtiene casos de JSON DB, SQLite BD o fallback a mock"""
    # Prioridad 1: JSON DB (casos reales procesados)
    try:
        casos_json = db_manager.data_store.get("casos", [])
        if casos_json:
            casos = []
            for caso_json in casos_json:
                case_id = caso_json.get('case_id')
                if not case_id:
                    continue
                
                # Obtener EDN desde edn.json (nueva estructura)
                edn = db_manager.get_caso_by_case_id(case_id)
                if not edn:
                    # Si no hay EDN, crear uno básico
                    edn = {
                        "compilation_metadata": {
                            "case_id": case_id,
                            "processing_timestamp": "",
                            "status": "UNKNOWN"
                        },
                        "unified_context": {},
                        "document_inventory": {
                            "level_1_critical": [],
                            "level_2_supporting": [],
                            "level_0_missing": []
                        }
                    }
                
                # Aplicar cambios en memoria si existen
                if case_id in cases_store:
                    stored = cases_store[case_id]
                    if "document_inventory" in stored:
                        edn["document_inventory"] = stored["document_inventory"]
                    if "checklist" in stored:
                        edn["checklist"] = stored["checklist"]
                
                casos.append(edn)
            if casos:
                return casos
    except Exception as e:
        print(f"Error leyendo de JSON DB: {e}")
    
    # Prioridad 2: SQLite BD
    try:
        casos_bd = db_manager.get_all_casos()
        if casos_bd:
            casos = []
            for caso_bd in casos_bd:
                case_id = caso_bd['case_id']
                edn = db_manager.get_caso_by_case_id(case_id)
                if edn:
                    # Aplicar cambios en memoria si existen
                    if case_id in cases_store:
                        stored = cases_store[case_id]
                        if "document_inventory" in stored:
                            edn["document_inventory"] = stored["document_inventory"]
                        if "checklist" in stored:
                            edn["checklist"] = stored["checklist"]
                    casos.append(edn)
            if casos:
                return casos
    except Exception as e:
        print(f"Error leyendo de BD: {e}")
    
    # Fallback a mock
    data = load_mock_cases()
    casos = []
    for caso_data in data["casos"]:
        case_id = caso_data["compilation_metadata"]["case_id"]
        if case_id in cases_store:
            stored = cases_store[case_id]
            if "document_inventory" in stored:
                caso_data["document_inventory"] = stored["document_inventory"]
            if "checklist" in stored:
                caso_data["checklist"] = stored["checklist"]
        casos.append(caso_data)
    return casos

def recalculate_checklist(caso: dict):
    """Recalcula el checklist basado en los documentos disponibles"""
    # Regenerar checklist completo usando el generador
    try:
        return checklist_generator.generate_checklist(caso)
    except Exception as e:
        print(f"Error recalculando checklist: {e}")
        # Retornar checklist existente si hay error
        return caso.get("checklist", {
            "group_a_admisibilidad": [],
            "group_b_instruccion": [],
            "group_c_analisis": {
                "c1_acreditacion_hecho": [],
                "c2_legalidad_cobro": []
            }
        })

def get_failed_checklist_items(checklist: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extrae los items del checklist que están en estado NO_CUMPLE.
    Retorna una lista de items fallidos con su información para el generador de resoluciones.
    """
    failures = []
    
    if not checklist:
        return failures
    
    # Buscar en todos los grupos
    for group_key in ["group_a_admisibilidad", "group_b_instruccion", "group_c_analisis"]:
        group = checklist.get(group_key, [])
        if isinstance(group, list):
            for item in group:
                if isinstance(item, dict) and item.get("status") == ChecklistStatus.NO_CUMPLE.value:
                    failures.append({
                        "id": item.get("id", ""),
                        "title": item.get("title", ""),
                        "description": item.get("description", ""),
                        "snippet_ref": item.get("snippet_ref"),  # Referencia al snippet de argumento legal
                        "evidence": item.get("evidence", "")
                    })
    
    return failures

@router.get("/casos", response_model=List[CaseSummary])
def get_casos(request: Request,
              q: Optional[str] = None,
              tipo_caso: Optional[str] = None,
              estado: Optional[str] = None,
              sort_by: Optional[str] = None,
              sort_order: Optional[str] = None,
              page: Optional[int] = None,
              page_size: Optional[int] = None):
    """Lista todos los casos con búsqueda, filtrado, ordenamiento y paginación"""
    app_mode = get_mode(request)
    
    # Valores por defecto
    sort_order = sort_order or 'asc'
    page = page or 1
    page_size = page_size or 100
    
    # Normalizar sort_order
    if sort_order.lower() not in ['asc', 'desc']:
        sort_order = 'asc'
    
    # Si está en modo test, usar mock
    if app_mode == 'test':
        data = load_mock_cases()
        summaries = []
        for caso_data in data["casos"]:
            case_id = caso_data["compilation_metadata"]["case_id"]
            if case_id in cases_store:
                stored = cases_store[case_id]
                if "document_inventory" in stored:
                    caso_data["document_inventory"] = stored["document_inventory"]
                if "checklist" in stored:
                    caso_data["checklist"] = stored["checklist"]
            
            # Aplicar búsqueda si se especifica
            if q:
                query_lower = q.lower()
                unified_context = caso_data.get("unified_context", {})
                searchable_fields = [
                    case_id,
                    unified_context.get("client_name", ''),
                    unified_context.get("rut_client", ''),
                    caso_data.get("materia", ''),
                    caso_data.get("empresa", ''),
                    str(caso_data.get("monto_disputa", 0))
                ]
                if not any(query_lower in str(field).lower() for field in searchable_fields if field):
                    continue
            
            checklist = caso_data.get("checklist")
            status = CaseStatus.PENDIENTE
            if checklist:
                all_validated = True
                has_failures = False
                for category in ["group_a_admisibilidad", "group_b_instruccion", "group_c_analisis"]:
                    items = checklist.get(category, [])
                    if not isinstance(items, list):
                        continue
                    for item in items:
                        if isinstance(item, dict):
                            if item.get("status") == ChecklistStatus.NO_CUMPLE.value:
                                has_failures = True
                            if not item.get("validated", False):
                                all_validated = False
                
                if all_validated and not has_failures:
                    status = CaseStatus.RESUELTO
                elif has_failures:
                    status = CaseStatus.EN_REVISION
            
            # Filtrar por estado si se especifica
            if estado and status.value != estado:
                continue
            
            unified_context = caso_data.get("unified_context", {})
            client_name = unified_context.get("client_name") or "N/A"
            rut_client = unified_context.get("rut_client") or "N/A"
            
            # Usar tipo_caso del EDN si materia no está disponible o es el valor por defecto
            materia = caso_data.get("materia") or "N/A"
            if materia == "N/A" or materia == "Reclamo SEC":
                tipo_caso = caso_data.get("compilation_metadata", {}).get("tipo_caso")
                if tipo_caso:
                    materia = tipo_caso
            
            summary = CaseSummary(
                case_id=caso_data["compilation_metadata"]["case_id"],
                client_name=client_name,
                rut_client=rut_client,
                materia=materia,
                monto_disputa=caso_data.get("monto_disputa") or 0,
                status=status,
                fecha_ingreso=caso_data.get("fecha_ingreso") or "",
                empresa=caso_data.get("empresa") or "N/A"
            )
            summaries.append(summary)
        
        # Aplicar ordenamiento
        if sort_by:
            reverse_order = sort_order.lower() == 'desc'
            summaries = _sort_summaries(summaries, sort_by, reverse_order)
        
        # Aplicar paginación
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        summaries = summaries[start_idx:end_idx]
        
        return summaries
    
    # Modo validate: usar casos reales
    # Intentar obtener de JSON DB primero
    try:
        casos_bd = db_manager.get_all_casos()
        if casos_bd:
            summaries = []
            for caso_bd in casos_bd:
                # Filtrar por tipo_caso si se especifica
                if tipo_caso:
                    # Obtener EDN para verificar tipo_caso
                    edn = db_manager.get_caso_by_case_id(caso_bd['case_id'])
                    if edn:
                        edn_tipo_caso = edn.get("compilation_metadata", {}).get("tipo_caso")
                        if edn_tipo_caso != tipo_caso:
                            continue
                
                # Determinar status desde la BD
                estado_bd = caso_bd.get('estado', 'PENDIENTE')
                if estado_bd == CaseStatus.CERRADO.value:
                    status = CaseStatus.CERRADO
                elif estado_bd == 'RESUELTO':
                    status = CaseStatus.RESUELTO
                elif estado_bd == 'EN_REVISION':
                    status = CaseStatus.EN_REVISION
                else:
                    status = CaseStatus.PENDIENTE
                
                # Filtrar por estado si se especifica
                if estado and status.value != estado:
                    continue
                
                # Aplicar búsqueda si se especifica
                if q:
                    query_lower = q.lower()
                    # Buscar en campos visibles en el dashboard
                    searchable_fields = [
                        caso_bd.get('case_id', ''),
                        caso_bd.get('client_name', ''),
                        caso_bd.get('rut_client', ''),
                        caso_bd.get('materia', ''),
                        caso_bd.get('empresa', ''),
                        str(caso_bd.get('monto_disputa', 0))
                    ]
                    if not any(query_lower in str(field).lower() for field in searchable_fields if field):
                        continue
                
                # Obtener tipo_caso del EDN si materia no está disponible o es el valor por defecto
                materia = caso_bd.get('materia') or 'N/A'
                if materia == 'N/A' or materia == 'Reclamo SEC':
                    # Intentar obtener tipo_caso del EDN
                    edn = db_manager.get_caso_by_case_id(caso_bd['case_id'])
                    if edn:
                        tipo_caso = edn.get('compilation_metadata', {}).get('tipo_caso')
                        if tipo_caso:
                            materia = tipo_caso
                
                summary = CaseSummary(
                    case_id=caso_bd['case_id'],
                    client_name=caso_bd.get('client_name') or 'N/A',
                    rut_client=caso_bd.get('rut_client') or 'N/A',
                    materia=materia,
                    monto_disputa=caso_bd.get('monto_disputa') or 0,
                    status=status,
                    fecha_ingreso=caso_bd.get('fecha_ingreso') or '',
                    empresa=caso_bd.get('empresa') or 'N/A'
                )
                summaries.append(summary)
            
            # Aplicar ordenamiento
            if sort_by:
                reverse_order = sort_order.lower() == 'desc'
                summaries = _sort_summaries(summaries, sort_by, reverse_order)
            
            # Aplicar paginación
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            summaries = summaries[start_idx:end_idx]
            
            if summaries:
                return summaries
    except Exception as e:
        print(f"Error leyendo de JSON DB: {e}")
    
    # Fallback a casos procesados
    casos_data = get_cases_data()
    summaries = []
    
    # Cargar estados guardados desde casos.json
    estados_guardados = {}
    try:
        casos_path = db_path / "casos.json"
        if casos_path.exists():
            with open(casos_path, "r", encoding="utf-8") as f:
                casos_json = json.load(f)
                for caso_json in casos_json:
                    case_id = caso_json.get("case_id")
                    if case_id:
                        estados_guardados[case_id] = caso_json.get("estado")
    except Exception as e:
        print(f"Error leyendo estados de casos: {e}")
    
    for caso in casos_data:
        case_id = caso.get("compilation_metadata", {}).get("case_id") if isinstance(caso.get("compilation_metadata"), dict) else None
        if not case_id:
            case_id = caso.get("case_id")
        
        # Si el caso está cerrado en la BD, usar ese estado directamente
        estado_guardado = estados_guardados.get(case_id)
        if estado_guardado == CaseStatus.CERRADO.value:
            status = CaseStatus.CERRADO
        else:
            # Determinar status basado en checklist
            checklist = caso.get("checklist")
            status = CaseStatus.PENDIENTE
            if checklist:
                all_validated = True
                has_failures = False
                for category in ["group_a_admisibilidad", "group_b_instruccion", "group_c_analisis"]:
                    items = checklist.get(category, [])
                    if not isinstance(items, list):
                        continue
                    for item in items:
                        if isinstance(item, dict):
                            if item.get("status") == ChecklistStatus.NO_CUMPLE.value:
                                has_failures = True
                            if not item.get("validated", False):
                                all_validated = False
                
                if all_validated and not has_failures:
                    status = CaseStatus.RESUELTO
                elif has_failures:
                    status = CaseStatus.EN_REVISION
        
        # Filtrar por estado si se especifica
        if estado and status.value != estado:
            continue
        
        # Aplicar búsqueda si se especifica
        if q:
            query_lower = q.lower()
            unified_context = caso.get("unified_context", {})
            searchable_fields = [
                case_id or '',
                unified_context.get("client_name", ''),
                unified_context.get("rut_client", ''),
                caso.get("materia", ''),
                caso.get("empresa", ''),
                str(caso.get("monto_disputa", 0))
            ]
            if not any(query_lower in str(field).lower() for field in searchable_fields if field):
                continue
        
        unified_context = caso.get("unified_context", {})
        # Asegurar que los valores nunca sean None
        client_name = unified_context.get("client_name") or "N/A"
        rut_client = unified_context.get("rut_client") or "N/A"
        
        case_id_summary = caso.get("compilation_metadata", {}).get("case_id") if isinstance(caso.get("compilation_metadata"), dict) else None
        if not case_id_summary:
            case_id_summary = caso.get("case_id", "UNKNOWN")
        
        # Usar tipo_caso del EDN si materia no está disponible o es el valor por defecto
        materia = caso.get("materia") or "N/A"
        if materia == "N/A" or materia == "Reclamo SEC":
            tipo_caso = caso.get("compilation_metadata", {}).get("tipo_caso") if isinstance(caso.get("compilation_metadata"), dict) else None
            if tipo_caso:
                materia = tipo_caso
        
        summary = CaseSummary(
            case_id=case_id_summary,
            client_name=client_name,
            rut_client=rut_client,
            materia=materia,
            monto_disputa=caso.get("monto_disputa") or 0,
            status=status,
            fecha_ingreso=caso.get("fecha_ingreso") or "",
            empresa=caso.get("empresa") or "N/A"
        )
        summaries.append(summary)
    
    # Aplicar ordenamiento
    if sort_by:
        reverse_order = sort_order.lower() == 'desc'
        summaries = _sort_summaries(summaries, sort_by, reverse_order)
    
    # Aplicar paginación
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    summaries = summaries[start_idx:end_idx]
    
    return summaries

@router.get("/casos/{case_id}", response_model=ExpedienteDigitalNormalizado)
def get_caso(case_id: str, request: Request, mode: Optional[str] = None):
    """Obtiene el EDN completo de un caso"""
    app_mode = get_mode(request)
    
    # Si está en modo test, usar mock
    if app_mode == 'test':
        data = load_mock_cases()
        for caso_data in data["casos"]:
            if caso_data["compilation_metadata"]["case_id"] == case_id:
                # Aplicar cambios en memoria si existen
                if case_id in cases_store:
                    stored = cases_store[case_id]
                    if "document_inventory" in stored:
                        caso_data["document_inventory"] = stored["document_inventory"]
                    if "checklist" in stored:
                        caso_data["checklist"] = stored["checklist"]
                return ExpedienteDigitalNormalizado(**caso_data)
        raise HTTPException(status_code=404, detail=f"Caso {case_id} no encontrado")
    
    # Modo validate: usar casos reales
    # Prioridad 1: JSON DB
    try:
        edn = db_manager.get_caso_by_case_id(case_id)
        if edn:
            # Asegurar que todos los campos requeridos existan
            # Nota: get_caso_by_case_id ya fusiona metadatos del caso con el EDN
            edn = ensure_edn_completeness(edn)
            
            # Aplicar cambios en memoria si existen
            if case_id in cases_store:
                stored = cases_store[case_id]
                if "document_inventory" in stored:
                    edn["document_inventory"] = stored["document_inventory"]
                if "checklist" in stored:
                    edn["checklist"] = stored["checklist"]
            
            # Siempre regenerar checklist usando MIN (para asegurar tipo_caso correcto)
            try:
                edn["checklist"] = checklist_generator.generate_checklist(edn)
            except Exception as e:
                print(f"Error generando checklist en get_caso: {e}")
                import traceback
                traceback.print_exc()
            
            return ExpedienteDigitalNormalizado(**edn)
    except Exception as e:
        print(f"Error obteniendo caso de JSON DB: {e}")
        import traceback
        traceback.print_exc()
    
    # Prioridad 2: SQLite BD
    try:
        edn = db_manager.get_caso_by_case_id(case_id)
        if edn:
            # Aplicar cambios en memoria si existen
            if case_id in cases_store:
                stored = cases_store[case_id]
                if "document_inventory" in stored:
                    edn["document_inventory"] = stored["document_inventory"]
                if "checklist" in stored:
                    edn["checklist"] = stored["checklist"]
            return ExpedienteDigitalNormalizado(**edn)
    except Exception:
        pass
    
    # Fallback a mock
    casos_data = get_cases_data()
    for caso in casos_data:
        case_id_caso = caso.get("compilation_metadata", {}).get("case_id") if isinstance(caso.get("compilation_metadata"), dict) else None
        if not case_id_caso:
            # Intentar obtener desde el caso directamente si no tiene compilation_metadata
            case_id_caso = caso.get("case_id")
        if case_id_caso == case_id:
            return ExpedienteDigitalNormalizado(**caso)
    
    raise HTTPException(status_code=404, detail=f"Caso {case_id} no encontrado")

@router.get("/casos/search", response_model=List[CaseSummary])
def search_casos(request: Request,
                 q: str = None,
                 mode: Optional[str] = None):
    """Busca casos por texto en los campos del EDN"""
    app_mode = get_mode(request)
    
    if app_mode == 'test':
        # En modo test, buscar en mock data
        data = load_mock_cases()
        casos_data = data["casos"]
    else:
        # En modo validate, buscar en JSON DB
        casos_bd = db_manager.get_all_casos()
        casos_data = []
        for caso_bd in casos_bd:
            case_id = caso_bd['case_id']
            edn = db_manager.get_caso_by_case_id(case_id)
            if edn:
                casos_data.append(edn)
    
    # Buscar en campos del EDN
    query_lower = q.lower()
    matching_cases = []
    
    for caso in casos_data:
        case_id = caso.get("compilation_metadata", {}).get("case_id", "")
        
        # Buscar en unified_context
        unified_context = caso.get("unified_context", {})
        if any(query_lower in str(v).lower() for v in unified_context.values() if v):
            matching_cases.append(caso)
            continue
        
        # Buscar en document_inventory
        doc_inventory = caso.get("document_inventory", {})
        for level in ["level_1_critical", "level_2_supporting"]:
            for doc in doc_inventory.get(level, []):
                if query_lower in doc.get("original_name", "").lower() or \
                   query_lower in doc.get("standardized_name", "").lower():
                    matching_cases.append(caso)
                    break
            if caso in matching_cases:
                break
        
        # Buscar en compilation_metadata
        compilation_metadata = caso.get("compilation_metadata", {})
        if query_lower in case_id.lower() or \
           query_lower in str(compilation_metadata.get("tipo_caso", "")).lower():
            matching_cases.append(caso)
            continue
    
    # Convertir a CaseSummary
    summaries = []
    for caso in matching_cases:
        case_id = caso.get("compilation_metadata", {}).get("case_id", "")
        unified_context = caso.get("unified_context", {})
        
        # Usar EDN como fuente principal (unified_context)
        client_name = unified_context.get('client_name')
        rut_client = unified_context.get('rut_client')
        
        # Fallback a personas.json solo si no hay datos en EDN
        if not client_name or client_name in ['—', 'N/A', '']:
            rut = rut_client
            persona = db_manager.data_store.get("personas", {}).get(rut) if rut else None
            if persona:
                client_name = persona.get('nombre', 'N/A')
                if not rut_client or rut_client in ['—', 'N/A', '']:
                    rut_client = persona.get('rut', 'N/A')
        
        # Si aún no hay nombre, usar placeholder
        if not client_name or client_name in ['—', 'N/A', '']:
            client_name = f"Cliente {case_id}"
        if not rut_client or rut_client in ['—', 'N/A', '']:
            rut_client = f"RUT-{case_id}"
        
        # Determinar estado (simplificado)
        status = CaseStatus.PENDIENTE
        # Buscar en casos.json para obtener estado real
        for c in db_manager.data_store.get("casos", []):
            if c.get('case_id') == case_id:
                estado_bd = c.get('estado', 'PENDIENTE')
                if estado_bd == CaseStatus.CERRADO.value:
                    status = CaseStatus.CERRADO
                elif estado_bd == 'RESUELTO':
                    status = CaseStatus.RESUELTO
                break
        
        # Usar tipo_caso del EDN si materia no está disponible o es el valor por defecto
        materia = caso.get('materia') or 'N/A'
        if materia == 'N/A' or materia == 'Reclamo SEC':
            tipo_caso = caso.get('compilation_metadata', {}).get('tipo_caso')
            if tipo_caso:
                materia = tipo_caso
        
        summary = CaseSummary(
            case_id=case_id,
            client_name=client_name,
            rut_client=rut_client,
            materia=materia,
            monto_disputa=caso.get('monto_disputa') or 0,
            status=status,
            fecha_ingreso=caso.get('fecha_ingreso') or '',
            empresa=caso.get('empresa') or 'N/A'
        )
        summaries.append(summary)
    
    return summaries

@router.put("/casos/{case_id}/documentos/{file_id}")
def update_documento(case_id: str, file_id: str, update: DocumentUpdateRequest,
                     request: Request,
                     mode: Optional[str] = None):
    """Actualiza el tipo de un documento (re-clasificación) y guarda en DataBase"""
    app_mode = get_mode(request)
    casos_data = get_cases_data_with_mode(app_mode)
    
    caso_encontrado = None
    for caso in casos_data:
        case_id_caso = caso.get("compilation_metadata", {}).get("case_id") if isinstance(caso.get("compilation_metadata"), dict) else None
        if not case_id_caso:
            # Intentar obtener desde el caso directamente si no tiene compilation_metadata
            case_id_caso = caso.get("case_id")
        if case_id_caso == case_id:
            caso_encontrado = caso
            break
    
    if not caso_encontrado:
        raise HTTPException(status_code=404, detail=f"Caso {case_id} no encontrado")
    
    # Buscar y actualizar el documento
    doc_inventory = caso_encontrado["document_inventory"]
    documento_encontrado = None
    doc_level = None
    
    for doc in doc_inventory["level_1_critical"]:
        if doc["file_id"] == file_id:
            documento_encontrado = doc
            doc_level = "level_1_critical"
            break
    
    if not documento_encontrado:
        for doc in doc_inventory["level_2_supporting"]:
            if doc["file_id"] == file_id:
                documento_encontrado = doc
                doc_level = "level_2_supporting"
                break
    
    if not documento_encontrado:
        raise HTTPException(status_code=404, detail=f"Documento {file_id} no encontrado")
    
    # Actualizar tipo y nombre personalizado
    documento_encontrado["type"] = update.type.value
    
    # Si hay nombre personalizado, actualizarlo
    if update.custom_name:
        documento_encontrado["standardized_name"] = update.custom_name
    else:
        # Generar nombre estandarizado automático
        documento_encontrado["standardized_name"] = f"{update.type.value} - {documento_encontrado['original_name']}"
    
    # Recalcular categorías funcionales después de cambiar el tipo
    doc_inventory = caso_encontrado["document_inventory"]
    doc_inventory = ensure_functional_categories(doc_inventory)
    caso_encontrado["document_inventory"] = doc_inventory
    
    # Recalcular checklist
    caso_encontrado["checklist"] = recalculate_checklist(caso_encontrado)
    
    # Guardar en DataBase (JSON)
    try:
        _save_document_to_database(case_id, documento_encontrado, doc_level)
        
        # Actualizar EDN en edn.json
        if app_mode == 'validate':
            # Obtener EDN actualizado
            edn_actualizado = db_manager.get_caso_by_case_id(case_id)
            if edn_actualizado:
                # Actualizar el documento en el EDN
                # Buscar y actualizar el documento en level_1_critical y level_2_supporting
                doc_inventory_edn = edn_actualizado.get('document_inventory', {})
                for level_key in ['level_1_critical', 'level_2_supporting']:
                    for doc in doc_inventory_edn.get(level_key, []):
                        if doc.get('file_id') == file_id:
                            doc['type'] = documento_encontrado['type']
                            doc['standardized_name'] = documento_encontrado['standardized_name']
                            break
                
                # Recalcular categorías funcionales en el EDN completamente
                # Esto asegura que el documento esté en la categoría correcta según su nuevo tipo
                # y que se elimine de la categoría anterior si cambió de tipo
                from src.engine.omc.document_categorizer import add_functional_categories
                doc_inventory_edn = add_functional_categories(doc_inventory_edn)
                edn_actualizado['document_inventory'] = doc_inventory_edn
                
                # Remover campos de caso que no pertenecen al EDN
                edn_limpio = {k: v for k, v in edn_actualizado.items() 
                             if k not in ['materia', 'monto_disputa', 'empresa', 'fecha_ingreso']}
                db_manager.update_edn(case_id, edn_limpio)
                db_manager.reload_case(case_id)
    except Exception as e:
        print(f"Error guardando documento en DataBase: {e}")
        import traceback
        traceback.print_exc()
        # Continuar aunque falle la persistencia
    
    # Limpiar cache en memoria para forzar recarga desde disco
    # Esto asegura que los cambios se reflejen inmediatamente
    if case_id in cases_store:
        # Mantener solo el checklist temporalmente si existe
        checklist_temp = cases_store[case_id].get("checklist")
        del cases_store[case_id]
        # Restaurar checklist si existe para mantener consistencia
        if checklist_temp:
            cases_store[case_id] = {"checklist": checklist_temp}
    
    return {
        "message": "Documento actualizado correctamente",
        "checklist_updated": True,
        "checklist": caso_encontrado["checklist"],
        "document": documento_encontrado,  # Incluir el documento actualizado en la respuesta
        "document_inventory": caso_encontrado["document_inventory"]  # Incluir el inventario completo actualizado
    }

@router.put("/casos/{case_id}/checklist/{item_id}")
def update_checklist_item(case_id: str, item_id: str, update: ChecklistItemUpdateRequest,
                          request: Request,
                          mode: Optional[str] = None):
    """Actualiza el estado de validación de un item del checklist"""
    app_mode = get_mode(request)
    casos_data = get_cases_data_with_mode(app_mode)
    
    caso_encontrado = None
    for caso in casos_data:
        case_id_caso = caso.get("compilation_metadata", {}).get("case_id") if isinstance(caso.get("compilation_metadata"), dict) else None
        if not case_id_caso:
            # Intentar obtener desde el caso directamente si no tiene compilation_metadata
            case_id_caso = caso.get("case_id")
        if case_id_caso == case_id:
            caso_encontrado = caso
            break
    
    if not caso_encontrado:
        raise HTTPException(status_code=404, detail=f"Caso {case_id} no encontrado")
    
    checklist = caso_encontrado.get("checklist", {})
    item_encontrado = None
    
    # Buscar en los grupos correctos (group_a_admisibilidad, group_b_instruccion, group_c_analisis)
    for category in ["group_a_admisibilidad", "group_b_instruccion", "group_c_analisis"]:
        items = checklist.get(category, [])
        if not isinstance(items, list):
            continue
        for idx, item in enumerate(items):
            if isinstance(item, dict) and item.get("id") == item_id:
                items[idx]["validated"] = update.validated
                item_encontrado = items[idx]
                break
        if item_encontrado:
            break
    
    if item_encontrado is None:
        raise HTTPException(status_code=404, detail=f"Item {item_id} no encontrado en el checklist")
    
    # Guardar cambios en EDN
    if app_mode == 'validate':
        # Obtener EDN actualizado
        edn_actualizado = db_manager.get_caso_by_case_id(case_id)
        if edn_actualizado:
            # Actualizar checklist en EDN
            edn_actualizado["checklist"] = checklist
            # Remover campos de caso que no pertenecen al EDN
            edn_limpio = {k: v for k, v in edn_actualizado.items() 
                         if k not in ['materia', 'monto_disputa', 'empresa', 'fecha_ingreso']}
            db_manager.update_edn(case_id, edn_limpio)
            db_manager.reload_case(case_id)
    
    # Guardar cambios en memoria también
    if case_id not in cases_store:
        cases_store[case_id] = {}
    cases_store[case_id]["checklist"] = checklist
    
    return {"message": "Item del checklist actualizado", "item": item}

@router.post("/casos/{case_id}/resolucion", response_model=ResolucionResponse)
def generar_resolucion(case_id: str,
                       resolucion_req: ResolucionRequest,
                       request: Request,
                       mode: Optional[str] = None):
    """Genera un borrador de resolución basado en el estado del checklist"""
    app_mode = get_mode(request)
    casos_data = get_cases_data_with_mode(app_mode)
    
    caso_encontrado = None
    for caso in casos_data:
        case_id_caso = caso.get("compilation_metadata", {}).get("case_id") if isinstance(caso.get("compilation_metadata"), dict) else None
        if not case_id_caso:
            case_id_caso = caso.get("case_id")
        if case_id_caso == case_id:
            caso_encontrado = caso
            break
    
    if not caso_encontrado:
        raise HTTPException(status_code=404, detail=f"Caso {case_id} no encontrado")

    # Asegurarse de que el caso tenga un checklist
    if "checklist" not in caso_encontrado or not caso_encontrado["checklist"]:
        logger.info(f"Checklist no encontrado para {case_id}, generando uno nuevo.")
        # Pasar el diccionario directamente, no convertir a Pydantic primero
        checklist_obj = checklist_generator.generate_checklist(caso_encontrado)
        caso_encontrado["checklist"] = checklist_obj

    # Preparar datos para el generador
    case_id_val = caso_encontrado.get('compilation_metadata', {}).get('case_id', case_id)
    client_name_val = caso_encontrado.get('unified_context', {}).get('client_name', 'N/A')
    rut_client_val = caso_encontrado.get('unified_context', {}).get('rut_client', 'N/A')
    empresa_val = caso_encontrado.get('empresa', 'N/A')
    materia_val = caso_encontrado.get('materia', 'N/A')
    checklist_val = caso_encontrado.get("checklist", {})

    try:
        content = resolucion_generator.generate_resolucion(
            case_id=case_id_val,
            client_name=client_name_val,
            rut_client=rut_client_val,
            empresa=empresa_val,
            materia=materia_val,
            checklist=checklist_val,
            template_type=resolucion_req.template_type,
            contenido_personalizado=resolucion_req.content  # Usar 'content' del request
        )
        # Devolver según el modelo ResolucionResponse
        return {
            "borrador": content,
            "template_type": resolucion_req.template_type
        }
    except FileNotFoundError as e:
        logger.error(f"Error de template en generar_resolucion: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except ValueError as e:
        logger.error(f"Error de valor en generar_resolucion: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error inesperado al generar resolución para {case_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno al generar la resolución")

def cleanup_temp_previews(case_id: str = None, max_age_hours: int = 1):
    """
    Limpia archivos temporales de preview.
    
    Args:
        case_id: Si se proporciona, solo limpia previews de este caso. Si es None, limpia todos los previews antiguos.
        max_age_hours: Edad máxima en horas para considerar un archivo como antiguo (default: 1 hora)
    """
    import time
    from datetime import datetime, timedelta
    
    if not temp_dir.exists():
        return
    
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    deleted_count = 0
    
    for file_path in temp_dir.glob("resolucion_preview_*.pdf"):
        try:
            # Si se especifica un case_id, solo eliminar si el nombre contiene ese case_id
            if case_id and case_id not in file_path.name:
                continue
            
            # Verificar edad del archivo
            file_age = current_time - file_path.stat().st_mtime
            
            # Eliminar si es específico del caso o si es antiguo
            if case_id or file_age > max_age_seconds:
                file_path.unlink()
                deleted_count += 1
        except Exception as e:
            logger.warning(f"Error al eliminar archivo temporal {file_path}: {e}")
    
    if deleted_count > 0:
        logger.info(f"Limpieza de previews temporales: {deleted_count} archivo(s) eliminado(s)")

@router.post("/casos/{case_id}/resolucion/pdf-preview")
def preview_resolucion_pdf(case_id: str,
                           resolucion_req: ResolucionRequest,
                           request: Request,
                           mode: Optional[str] = None):
    """Genera y devuelve un PDF de previsualización de la resolución"""
    app_mode = get_mode(request)
    casos_data = get_cases_data_with_mode(app_mode)
    
    caso_encontrado = None
    for caso in casos_data:
        case_id_caso = caso.get("compilation_metadata", {}).get("case_id") if isinstance(caso.get("compilation_metadata"), dict) else None
        if not case_id_caso:
            case_id_caso = caso.get("case_id")
        if case_id_caso == case_id:
            caso_encontrado = caso
            break
    
    if not caso_encontrado:
        raise HTTPException(status_code=404, detail=f"Caso {case_id} no encontrado")
    
    unified_context = caso_encontrado.get('unified_context', {})
    client_name = unified_context.get('client_name', 'N/A')
    rut_client = unified_context.get('rut_client', 'N/A')
    empresa = caso_encontrado.get('empresa', 'N/A')
    materia = caso_encontrado.get('materia', 'N/A')
    
    # Limpiar previews antiguos antes de generar uno nuevo
    cleanup_temp_previews(max_age_hours=1)
    
    # Crear directorio temporal para PDFs
    temp_dir.mkdir(exist_ok=True)
    
    # Generar PDF
    import uuid
    pdf_filename = f"resolucion_preview_{case_id}_{uuid.uuid4().hex[:8]}.pdf"
    pdf_path = temp_dir / pdf_filename
    
    resolucion_content = resolucion_req.content or ""
    
    from src.utils.resolucion_pdf import generate_resolucion_pdf
    success = generate_resolucion_pdf(
        resolucion_content=resolucion_content,
        case_id=case_id,
        output_path=pdf_path,
        client_name=client_name,
        rut_client=rut_client,
        empresa=empresa,
        materia=materia
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Error al generar PDF de resolución")
    
    return FileResponse(
        str(pdf_path),
        media_type='application/pdf',
        filename=f"Resolucion_{case_id}_preview.pdf",
        headers={"Content-Disposition": f'inline; filename="Resolucion_{case_id}_preview.pdf"'}
    )

@router.delete("/casos/{case_id}/resolucion/preview-cleanup")
def cleanup_preview(case_id: str, request: Request):
    """Limpia los archivos temporales de preview para un caso específico"""
    cleanup_temp_previews(case_id=case_id)
    return {"message": f"Previews temporales del caso {case_id} eliminados"}

@router.post("/casos/{case_id}/cerrar")
def cerrar_caso(case_id: str,
                cerrar_req: CerrarCasoRequest,
                request: Request,
                mode: Optional[str] = None):
    """Cierra un caso, actualizando su estado a CERRADO y guardando la resolución"""
    app_mode = get_mode(request)
    
    # Solo permitir en modo validate (casos reales)
    if app_mode == 'test':
        raise HTTPException(status_code=400, detail="No se puede cerrar caso en modo test")
    
    # Buscar caso en JSON DB
    casos_path = db_path / "casos.json"
    if not casos_path.exists():
        raise HTTPException(status_code=404, detail="Base de datos no encontrada")
    
    try:
        with open(casos_path, "r", encoding="utf-8") as f:
            casos = json.load(f)
        
        caso_encontrado = None
        caso_index = None
        for idx, caso in enumerate(casos):
            if caso.get("case_id") == case_id:
                caso_encontrado = caso
                caso_index = idx
                break
        
        if not caso_encontrado:
            raise HTTPException(status_code=404, detail=f"Caso {case_id} no encontrado")
        
        # Verificar que el caso no esté ya cerrado
        if caso_encontrado.get("estado") == CaseStatus.CERRADO.value:
            raise HTTPException(status_code=400, detail="El caso ya está cerrado")
        
        # Actualizar estado a CERRADO
        caso_encontrado["estado"] = CaseStatus.CERRADO.value
        
        # Guardar fecha de cierre
        from datetime import datetime
        fecha_cierre = cerrar_req.fecha_cierre or datetime.now().isoformat()
        caso_encontrado["fecha_cierre"] = fecha_cierre
        
        # Guardar cambios en casos.json (solo metadatos del caso)
        casos[caso_index] = caso_encontrado
        with open(casos_path, "w", encoding="utf-8") as f:
            json.dump(casos, f, indent=2, ensure_ascii=False)
        
        # Limpiar previews temporales de este caso al cerrarlo
        cleanup_temp_previews(case_id=case_id)
        
        # Generar PDF de resolución si hay contenido
        resolucion_file_id = None
        if cerrar_req.resolucion_content:
            from src.utils.resolucion_pdf import generate_resolucion_pdf
            import uuid
            
            # Crear directorio para resoluciones finales (en carpeta del caso)
            case_files_dir = files_dir / case_id
            case_resoluciones_dir = case_files_dir / "resoluciones"
            case_resoluciones_dir.mkdir(parents=True, exist_ok=True)
            
            # Obtener datos del caso para el PDF
            edn = db_manager.get_caso_by_case_id(case_id)
            unified_context = edn.get('unified_context', {}) if edn else {}
            client_name = unified_context.get('client_name', 'N/A')
            rut_client = unified_context.get('rut_client', 'N/A')
            empresa = caso_encontrado.get('empresa', 'N/A')
            materia = caso_encontrado.get('materia', 'N/A')
            
            # Generar PDF
            pdf_filename = f"Resolucion_{case_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_path = case_resoluciones_dir / pdf_filename
            
            success = generate_resolucion_pdf(
                resolucion_content=cerrar_req.resolucion_content,
                case_id=case_id,
                output_path=pdf_path,
                client_name=client_name,
                rut_client=rut_client,
                empresa=empresa,
                materia=materia
            )
            
            if success:
                # Guardar documento en documentos.json
                resolucion_file_id = str(uuid.uuid4())
                documentos_path = db_path / "documentos.json"
                
                # Calcular ruta relativa desde FILES_DIR
                relative_resolucion_path = pdf_path.relative_to(FILES_DIR)
                
                documento_resolucion = {
                    "file_id": resolucion_file_id,
                    "case_id": case_id,
                    "original_name": pdf_filename,
                    "standardized_name": f"Resolución Final - {case_id}",
                    "type": "RESOLUCION_FINAL",
                    "relative_path": str(relative_resolucion_path),
                    "file_path": f"resoluciones/{pdf_filename}",  # Relativo desde la carpeta del caso
                    "metadata": {
                        "fecha_generacion": fecha_cierre,
                        "tipo": "RESOLUCION_FINAL"
                    }
                }
                
                if documentos_path.exists():
                    with open(documentos_path, "r", encoding="utf-8") as f:
                        documentos = json.load(f)
                else:
                    documentos = []
                
                documentos.append(documento_resolucion)
                
                with open(documentos_path, "w", encoding="utf-8") as f:
                    json.dump(documentos, f, indent=2, ensure_ascii=False)
                
                # Agregar resolución al document_inventory del EDN
                if edn:
                    if "document_inventory" not in edn:
                        edn["document_inventory"] = {}
                    if "otros" not in edn["document_inventory"]:
                        edn["document_inventory"]["otros"] = []
                    
                    # Verificar que no exista ya
                    existe = any(doc.get("file_id") == resolucion_file_id 
                                for doc in edn["document_inventory"]["otros"])
                    if not existe:
                        edn["document_inventory"]["otros"].append({
                            "file_id": resolucion_file_id,
                            "original_name": pdf_filename,
                            "standardized_name": f"Resolución Final - {case_id}",
                            "type": "RESOLUCION_FINAL"
                        })
        
        # Guardar resolución en EDN
        if cerrar_req.resolucion_content:
            edn = db_manager.get_caso_by_case_id(case_id)
            if edn:
                if "resolucion" not in edn:
                    edn["resolucion"] = {}
                edn["resolucion"]["content"] = cerrar_req.resolucion_content
                edn["resolucion"]["fecha_firma"] = fecha_cierre
                if resolucion_file_id:
                    edn["resolucion"]["pdf_file_id"] = resolucion_file_id
                # Remover campos de caso que no pertenecen al EDN
                edn_limpio = {k: v for k, v in edn.items() 
                             if k not in ['materia', 'monto_disputa', 'empresa', 'fecha_ingreso']}
                db_manager.update_edn(case_id, edn_limpio)
        
        # Recargar el caso desde la base de datos
        db_manager.reload_case(case_id)
        
        # Limpiar cache en memoria
        if case_id in cases_store:
            del cases_store[case_id]
        
        return {
            "message": "Caso cerrado exitosamente",
            "case_id": case_id,
            "estado": CaseStatus.CERRADO.value,
            "fecha_cierre": fecha_cierre,
            "resolucion_file_id": resolucion_file_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error cerrando caso: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al cerrar caso: {str(e)}")

@router.put("/casos/{case_id}/contexto")
def update_unified_context(case_id: str, update: UnifiedContextUpdateRequest,
                           request: Request,
                           mode: Optional[str] = None):
    """Actualiza el contexto unificado y campos del caso, guardando en DataBase"""
    app_mode = get_mode(request)
    
    # Solo permitir en modo validate (casos reales)
    if app_mode == 'test':
        raise HTTPException(status_code=400, detail="No se puede editar en modo test")
    
    # Buscar caso en JSON DB
    casos_path = db_path / "casos.json"
    if not casos_path.exists():
        raise HTTPException(status_code=404, detail="Base de datos no encontrada")
    
    try:
        with open(casos_path, "r", encoding="utf-8") as f:
            casos = json.load(f)
        
        caso_encontrado = None
        caso_index = None
        for idx, caso in enumerate(casos):
            if caso.get("case_id") == case_id:
                caso_encontrado = caso
                caso_index = idx
                break
        
        if not caso_encontrado:
            raise HTTPException(status_code=404, detail=f"Caso {case_id} no encontrado")
        
        # Obtener EDN actual
        edn = db_manager.get_caso_by_case_id(case_id)
        if not edn:
            raise HTTPException(status_code=404, detail=f"EDN para caso {case_id} no encontrado")
        
        # Actualizar unified_context en EDN
        if update.unified_context:
            if "unified_context" not in edn:
                edn["unified_context"] = {}
            
            for key, value in update.unified_context.items():
                edn["unified_context"][key] = value if value else None
        
        # Actualizar otros campos del caso (en casos.json)
        if update.materia is not None:
            caso_encontrado["materia"] = update.materia
        
        if update.monto_disputa is not None:
            caso_encontrado["monto_disputa"] = update.monto_disputa
        
        if update.empresa is not None:
            caso_encontrado["empresa"] = update.empresa
        
        if update.fecha_ingreso is not None:
            caso_encontrado["fecha_ingreso"] = update.fecha_ingreso
        
        # Actualizar personas y suministros si cambió RUT o NIS
        if update.unified_context:
            unified_context = edn["unified_context"]
            
            # Actualizar persona si cambió RUT o datos
            if unified_context.get("rut_client"):
                _update_persona_in_database(
                    unified_context.get("rut_client"),
                    unified_context.get("client_name"),
                    unified_context.get("email"),
                    unified_context.get("phone")
                )
            
            # Actualizar suministro si cambió NIS
            if unified_context.get("service_nis"):
                _update_suministro_in_database(
                    unified_context.get("service_nis"),
                    unified_context.get("commune"),
                    unified_context.get("address_standard")
                )
        
        # Guardar cambios en casos.json (solo metadatos)
        casos[caso_index] = caso_encontrado
        with open(casos_path, "w", encoding="utf-8") as f:
            json.dump(casos, f, indent=2, ensure_ascii=False)
        
        # Guardar cambios en EDN (remover campos de caso que no pertenecen al EDN)
        edn_limpio = {k: v for k, v in edn.items() 
                     if k not in ['materia', 'monto_disputa', 'empresa', 'fecha_ingreso']}
        db_manager.update_edn(case_id, edn_limpio)
        
        # Recargar el caso desde la base de datos para reflejar cambios
        db_manager.reload_case(case_id)
        
        # Limpiar cache en memoria para forzar recarga desde disco
        if case_id in cases_store:
            del cases_store[case_id]
        
        return {
            "message": "Contexto actualizado correctamente en la base de datos",
            "case_id": case_id
        }
        
    except Exception as e:
        print(f"Error actualizando contexto: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al actualizar: {str(e)}")

def _save_document_to_database(case_id: str, documento: Dict[str, Any], level: str):
    """Guarda actualización de documento en documentos.json"""
    documentos_path = DATABASE_DIR / "documentos.json"
    if not documentos_path.exists():
        return
    
    try:
        with open(documentos_path, "r", encoding="utf-8") as f:
            documentos = json.load(f)
        
        # Buscar y actualizar documento
        for idx, doc in enumerate(documentos):
            if doc.get("file_id") == documento["file_id"] and doc.get("case_id") == case_id:
                documentos[idx]["type"] = documento["type"]
                documentos[idx]["standardized_name"] = documento.get("standardized_name")
                documentos[idx]["level"] = level
                break
        
        # Guardar
        with open(documentos_path, "w", encoding="utf-8") as f:
            json.dump(documentos, f, indent=2, ensure_ascii=False)
        
        # Recargar documentos en JSONDBManager
        db_manager.reload()
    except Exception as e:
        print(f"Error guardando documento en DataBase: {e}")

def _update_persona_in_database(rut: str, nombre: str = None, email: str = None, telefono: str = None):
    """Actualiza persona en personas.json"""
    personas_path = db_path / "personas.json"
    if not personas_path.exists():
        return
    
    try:
        with open(personas_path, "r", encoding="utf-8") as f:
            personas = json.load(f)
        
        # Buscar y actualizar
        for idx, persona in enumerate(personas):
            if persona.get("rut") == rut:
                if nombre:
                    personas[idx]["nombre"] = nombre
                if email:
                    personas[idx]["email"] = email
                if telefono:
                    personas[idx]["telefono"] = telefono
                break
        
        # Guardar
        with open(personas_path, "w", encoding="utf-8") as f:
            json.dump(personas, f, indent=2, ensure_ascii=False)
        
        # Recargar personas en JSONDBManager
        db_manager.reload()
    except Exception as e:
        print(f"Error actualizando persona: {e}")

def _update_suministro_in_database(nis: str, comuna: str = None, direccion: str = None):
    """Actualiza suministro en suministros.json"""
    suministros_path = db_path / "suministros.json"
    if not suministros_path.exists():
        return
    
    try:
        with open(suministros_path, "r", encoding="utf-8") as f:
            suministros = json.load(f)
        
        # Buscar y actualizar
        for idx, suministro in enumerate(suministros):
            if suministro.get("nis") == nis:
                if comuna:
                    suministros[idx]["comuna"] = comuna
                if direccion:
                    suministros[idx]["direccion"] = direccion
                break
        
        # Guardar
        with open(suministros_path, "w", encoding="utf-8") as f:
            json.dump(suministros, f, indent=2, ensure_ascii=False)
        
        # Recargar suministros en JSONDBManager
        db_manager.reload()
    except Exception as e:
        print(f"Error actualizando suministro: {e}")

@router.get("/casos/{case_id}/documentos/{file_id}/preview")
def preview_documento(case_id: str, file_id: str,
                     request: Request,
                     mode: Optional[str] = None,
                     format: Optional[str] = None):
    """Sirve el archivo del documento para vista previa. Para DOCX, convierte a PDF automáticamente."""
    # Buscar documento en documentos.json primero (más confiable)
    documento_encontrado = None
    documentos_path = db_path / "documentos.json"
    
    if documentos_path.exists():
        try:
            with open(documentos_path, "r", encoding="utf-8") as f:
                documentos = json.load(f)
                for doc in documentos:
                    if doc.get("file_id") == file_id and doc.get("case_id") == case_id:
                        documento_encontrado = doc
                        break
        except Exception as e:
            print(f"Error leyendo documentos.json: {e}")
    
    # Si no se encuentra en documentos.json, buscar en EDN
    if not documento_encontrado:
        app_mode = get_mode(request)
        casos_data = get_cases_data_with_mode(app_mode)
        
        for caso in casos_data:
            case_id_caso = caso.get("compilation_metadata", {}).get("case_id") if isinstance(caso.get("compilation_metadata"), dict) else None
            if not case_id_caso:
                case_id_caso = caso.get("case_id")
            if case_id_caso == case_id:
                doc_inventory = caso.get("document_inventory", {})
                # Buscar en todas las categorías funcionales también
                for category in ["reclamo_respuesta", "informe_evidencias", "historial_calculos", "otros", "level_1_critical", "level_2_supporting"]:
                    for doc in doc_inventory.get(category, []):
                        if doc.get("file_id") == file_id:
                            documento_encontrado = doc
                            break
                    if documento_encontrado:
                        break
                if documento_encontrado:
                    break
    
    if not documento_encontrado:
        raise HTTPException(status_code=404, detail=f"Documento {file_id} no encontrado")
    
    # Determinar ruta del archivo usando rutas relativas
    file_path = None
    
    # Prioridad 1: relative_path (ruta relativa desde FILES_DIR)
    if documento_encontrado.get("relative_path"):
        file_path = files_dir / documento_encontrado["relative_path"]
        if file_path.exists():
            # Si es DOCX, convertir a PDF automáticamente
            if file_path.suffix.lower() == '.docx':
                from src.utils.docx_to_pdf import docx_to_pdf
                pdf_path = docx_to_pdf(file_path)
                if pdf_path and pdf_path.exists():
                    return _serve_file(pdf_path, documento_encontrado.get("original_name", "documento.docx").replace('.docx', '.pdf'))
                else:
                    # Si falla la conversión, intentar HTML como fallback
                    from src.utils.docx_to_html import docx_to_html
                    html_content = docx_to_html(file_path)
                    if html_content:
                        from fastapi.responses import HTMLResponse
                        return HTMLResponse(content=html_content)
                    raise HTTPException(status_code=500, detail="No se pudo convertir DOCX a PDF ni HTML")
            return _serve_file(file_path, documento_encontrado.get("original_name", "documento.pdf"))
    
    # Prioridad 2: file_path relativo desde la carpeta del caso (compatibilidad con datos antiguos)
    if documento_encontrado.get("file_path"):
        case_dir = example_cases_dir / case_id
        file_path = case_dir / documento_encontrado["file_path"]
        
        if file_path.exists():
            # Si es DOCX, convertir a PDF automáticamente
            if file_path.suffix.lower() == '.docx':
                from src.utils.docx_to_pdf import docx_to_pdf
                pdf_path = docx_to_pdf(file_path)
                if pdf_path and pdf_path.exists():
                    return _serve_file(pdf_path, documento_encontrado.get("original_name", "documento.docx").replace('.docx', '.pdf'))
                else:
                    # Si falla la conversión, intentar HTML como fallback
                    from src.utils.docx_to_html import docx_to_html
                    html_content = docx_to_html(file_path)
                    if html_content:
                        from fastapi.responses import HTMLResponse
                        return HTMLResponse(content=html_content)
                    raise HTTPException(status_code=500, detail="No se pudo convertir DOCX a PDF ni HTML")
            return _serve_file(file_path, documento_encontrado.get("original_name", "documento.pdf"))
    
    raise HTTPException(status_code=404, detail=f"Archivo físico no encontrado para documento {file_id}")

def _serve_file(file_path: Path, filename: str) -> FileResponse:
    """Helper para servir archivos con el MIME type correcto"""
    suffix = file_path.suffix.lower()
    
    # Determinar MIME type
    mime_types = {
        '.pdf': 'application/pdf',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.doc': 'application/msword',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.xls': 'application/vnd.ms-excel'
    }
    
    media_type = mime_types.get(suffix, 'application/octet-stream')
    
    return FileResponse(
        str(file_path),
        media_type=media_type,
        filename=filename,
        headers={
            "Content-Disposition": f'inline; filename="{filename}"'
        }
    )

