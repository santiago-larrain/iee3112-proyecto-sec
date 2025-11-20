from fastapi import APIRouter, HTTPException, Header, Query
from fastapi.responses import FileResponse, StreamingResponse
from typing import List, Optional, Dict, Any
import json
import os
from pathlib import Path
from models import (
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
from database import DBManager
from database.json_db_manager import JSONDBManager
from checklist_generator import ChecklistGenerator

router = APIRouter()

# Inicializar DB Managers
current_dir = Path(__file__).parent
db_path = current_dir.parent / "data" / "sec_reclamos.db"
db_manager = DBManager(str(db_path))

# Inicializar JSON DB Manager (prioritario)
json_db_dir = current_dir.parent / "data" / "DataBase"
json_db_manager = JSONDBManager(str(json_db_dir))

# Inicializar generador de checklist
try:
    checklist_generator = ChecklistGenerator()
except Exception as e:
    print(f"Warning: No se pudo inicializar ChecklistGenerator: {e}")
    # Crear generador dummy
    class DummyChecklistGenerator:
        def generate_checklist(self, edn):
            return {
                "group_a_admisibilidad": [],
                "group_b_instruccion": [],
                "group_c_analisis": {
                    "c1_acreditacion_hecho": [],
                    "c2_legalidad_cobro": []
                }
            }
    checklist_generator = DummyChecklistGenerator()

# Almacenamiento en memoria para cambios
cases_store = {}

# Cargar datos mock (fallback)
def load_mock_data():
    data_path = current_dir.parent / "data" / "mock_casos.json"
    if data_path.exists():
        with open(data_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"casos": []}

def get_app_mode(x_app_mode: Optional[str] = Header(None, alias='X-App-Mode'), mode: Optional[str] = Query(None)) -> str:
    """Obtiene el modo de la aplicación desde header o query param"""
    mode_value = (x_app_mode or mode or 'validate').lower()
    return mode_value if mode_value in ['test', 'validate'] else 'validate'

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
    
    # Generar checklist si no existe o está vacío
    if "checklist" not in edn or not edn.get("checklist"):
        try:
            edn["checklist"] = checklist_generator.generate_checklist(edn)
        except Exception as e:
            print(f"Error generando checklist: {e}")
            # Checklist por defecto vacío
            edn["checklist"] = {
                "group_a_admisibilidad": [],
                "group_b_instruccion": [],
                "group_c_analisis": {
                    "c1_acreditacion_hecho": [],
                    "c2_legalidad_cobro": []
                }
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
        data = load_mock_data()
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
        casos_json = json_db_manager.casos
        if casos_json:
            casos = []
            for caso_json in casos_json:
                edn = caso_json.get('edn', {})
                case_id = caso_json.get('case_id') or edn.get('compilation_metadata', {}).get('case_id')
                
                # Aplicar cambios en memoria si existen
                if case_id and case_id in cases_store:
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
    data = load_mock_data()
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

@router.get("/casos", response_model=List[CaseSummary])
def get_casos(x_app_mode: Optional[str] = Header(None), mode: Optional[str] = Query(None)):
    """Lista todos los casos"""
    app_mode = get_app_mode(x_app_mode, mode)
    
    # Si está en modo test, usar mock
    if app_mode == 'test':
        data = load_mock_data()
        summaries = []
        for caso_data in data["casos"]:
            case_id = caso_data["compilation_metadata"]["case_id"]
            if case_id in cases_store:
                stored = cases_store[case_id]
                if "document_inventory" in stored:
                    caso_data["document_inventory"] = stored["document_inventory"]
                if "checklist" in stored:
                    caso_data["checklist"] = stored["checklist"]
            
            checklist = caso_data.get("checklist")
            status = CaseStatus.PENDIENTE
            if checklist:
                all_validated = True
                has_failures = False
                for category in ["client_information", "evidence_review", "legal_compliance"]:
                    for item in checklist.get(category, []):
                        if item["status"] == ChecklistStatus.NO_CUMPLE.value:
                            has_failures = True
                        if not item.get("validated", False):
                            all_validated = False
                
                if all_validated and not has_failures:
                    status = CaseStatus.RESUELTO
                elif has_failures:
                    status = CaseStatus.EN_REVISION
            
            unified_context = caso_data.get("unified_context", {})
            client_name = unified_context.get("client_name") or "N/A"
            rut_client = unified_context.get("rut_client") or "N/A"
            
            summary = CaseSummary(
                case_id=caso_data["compilation_metadata"]["case_id"],
                client_name=client_name,
                rut_client=rut_client,
                materia=caso_data.get("materia") or "N/A",
                monto_disputa=caso_data.get("monto_disputa") or 0,
                status=status,
                fecha_ingreso=caso_data.get("fecha_ingreso") or "",
                empresa=caso_data.get("empresa") or "N/A"
            )
            summaries.append(summary)
        return summaries
    
    # Modo validate: usar casos reales
    # Intentar obtener de JSON DB primero
    try:
        casos_bd = json_db_manager.get_all_casos()
        if casos_bd:
            summaries = []
            for caso_bd in casos_bd:
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
                
                summary = CaseSummary(
                    case_id=caso_bd['case_id'],
                    client_name=caso_bd.get('client_name') or 'N/A',
                    rut_client=caso_bd.get('rut_client') or 'N/A',
                    materia=caso_bd.get('materia') or 'N/A',
                    monto_disputa=caso_bd.get('monto_disputa') or 0,
                    status=status,
                    fecha_ingreso=caso_bd.get('fecha_ingreso') or '',
                    empresa=caso_bd.get('empresa') or 'N/A'
                )
                summaries.append(summary)
            
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
        casos_path = current_dir.parent / "data" / "DataBase" / "casos.json"
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
        case_id = caso["compilation_metadata"]["case_id"]
        
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
                    for item in checklist.get(category, []):
                        if item["status"] == ChecklistStatus.NO_CUMPLE.value:
                            has_failures = True
                        if not item.get("validated", False):
                            all_validated = False
                
                if all_validated and not has_failures:
                    status = CaseStatus.RESUELTO
                elif has_failures:
                    status = CaseStatus.EN_REVISION
        
        unified_context = caso.get("unified_context", {})
        # Asegurar que los valores nunca sean None
        client_name = unified_context.get("client_name") or "N/A"
        rut_client = unified_context.get("rut_client") or "N/A"
        
        summary = CaseSummary(
            case_id=caso["compilation_metadata"]["case_id"],
            client_name=client_name,
            rut_client=rut_client,
            materia=caso.get("materia") or "N/A",
            monto_disputa=caso.get("monto_disputa") or 0,
            status=status,
            fecha_ingreso=caso.get("fecha_ingreso") or "",
            empresa=caso.get("empresa") or "N/A"
        )
        summaries.append(summary)
    
    return summaries

@router.get("/casos/{case_id}", response_model=ExpedienteDigitalNormalizado)
def get_caso(case_id: str, x_app_mode: Optional[str] = Header(None), mode: Optional[str] = Query(None)):
    """Obtiene el EDN completo de un caso"""
    app_mode = get_app_mode(x_app_mode, mode)
    
    # Si está en modo test, usar mock
    if app_mode == 'test':
        data = load_mock_data()
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
        edn = json_db_manager.get_caso_by_case_id(case_id)
        if edn:
            # Asegurar que todos los campos requeridos existan
            edn = ensure_edn_completeness(edn)
            
            # Aplicar cambios en memoria si existen
            if case_id in cases_store:
                stored = cases_store[case_id]
                if "document_inventory" in stored:
                    edn["document_inventory"] = stored["document_inventory"]
                if "checklist" in stored:
                    edn["checklist"] = stored["checklist"]
            
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
        if caso["compilation_metadata"]["case_id"] == case_id:
            return ExpedienteDigitalNormalizado(**caso)
    
    raise HTTPException(status_code=404, detail=f"Caso {case_id} no encontrado")

@router.put("/casos/{case_id}/documentos/{file_id}")
def update_documento(case_id: str, file_id: str, update: DocumentUpdateRequest,
                    x_app_mode: Optional[str] = Header(None, alias='X-App-Mode'),
                    mode: Optional[str] = Query(None)):
    """Actualiza el tipo de un documento (re-clasificación) y guarda en DataBase"""
    app_mode = get_app_mode(x_app_mode, mode)
    casos_data = get_cases_data_with_mode(app_mode)
    
    caso_encontrado = None
    for caso in casos_data:
        if caso["compilation_metadata"]["case_id"] == case_id:
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
    
    # Recalcular checklist
    caso_encontrado["checklist"] = recalculate_checklist(caso_encontrado)
    
    # Guardar en DataBase (JSON)
    try:
        _save_document_to_database(case_id, documento_encontrado, doc_level)
        # Recargar el caso desde la base de datos para reflejar cambios
        if app_mode == 'validate':
            json_db_manager.reload_case(case_id)
    except Exception as e:
        print(f"Error guardando documento en DataBase: {e}")
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
        "checklist": caso_encontrado["checklist"]
    }

@router.put("/casos/{case_id}/checklist/{item_id}")
def update_checklist_item(case_id: str, item_id: str, update: ChecklistItemUpdateRequest,
                         x_app_mode: Optional[str] = Header(None, alias='X-App-Mode'),
                         mode: Optional[str] = Query(None)):
    """Actualiza el estado de validación de un item del checklist"""
    app_mode = get_app_mode(x_app_mode, mode)
    casos_data = get_cases_data_with_mode(app_mode)
    
    caso_encontrado = None
    for caso in casos_data:
        if caso["compilation_metadata"]["case_id"] == case_id:
            caso_encontrado = caso
            break
    
    if not caso_encontrado:
        raise HTTPException(status_code=404, detail=f"Caso {case_id} no encontrado")
    
    checklist = caso_encontrado.get("checklist", {})
    item_encontrado = False
    
    for category in ["client_information", "evidence_review", "legal_compliance"]:
        for item in checklist.get(category, []):
            if item["id"] == item_id:
                item["validated"] = update.validated
                item_encontrado = True
                break
        if item_encontrado:
            break
    
    if not item_encontrado:
        raise HTTPException(status_code=404, detail=f"Item {item_id} no encontrado")
    
    # Guardar cambios
    if case_id not in cases_store:
        cases_store[case_id] = {}
    cases_store[case_id]["checklist"] = checklist
    
    return {"message": "Item del checklist actualizado", "item": item}

@router.post("/casos/{case_id}/resolucion", response_model=ResolucionResponse)
def generar_resolucion(case_id: str, request: ResolucionRequest,
                      x_app_mode: Optional[str] = Header(None, alias='X-App-Mode'),
                      mode: Optional[str] = Query(None)):
    """Genera un borrador de resolución basado en el estado del checklist"""
    app_mode = get_app_mode(x_app_mode, mode)
    casos_data = get_cases_data_with_mode(app_mode)
    
    caso_encontrado = None
    for caso in casos_data:
        if caso["compilation_metadata"]["case_id"] == case_id:
            caso_encontrado = caso
            break
    
    if not caso_encontrado:
        raise HTTPException(status_code=404, detail=f"Caso {case_id} no encontrado")
    
    checklist = caso_encontrado.get("checklist", {})
    
    # Determinar tipo de resolución basado en checklist
    has_failures = False
    for category in ["client_information", "evidence_review", "legal_compliance"]:
        for item in checklist.get(category, []):
            if item["status"] == ChecklistStatus.NO_CUMPLE.value and item.get("validated", False):
                has_failures = True
                break
        if has_failures:
            break
    
    template_type = request.template_type or ("INSTRUCCION" if has_failures else "IMPROCEDENTE")
    
    unified_context = caso_encontrado.get('unified_context', {})
    client_name = unified_context.get('client_name', 'N/A')
    rut_client = unified_context.get('rut_client', 'N/A')
    empresa = caso_encontrado.get('empresa', '')
    materia = caso_encontrado.get('materia', '')
    
    # Generar borrador
    if template_type == "INSTRUCCION":
        borrador = f"""INSTRUCCIÓN A LA EMPRESA {empresa}

Caso SEC: {case_id}
Cliente: {client_name}
RUT: {rut_client}
Materia: {materia}

CONSIDERANDO:
1. Que se ha recibido el reclamo del cliente indicado.
2. Que tras el análisis de la documentación presentada, se han detectado las siguientes irregularidades:

"""
        # Agregar argumentos por cada item fallido
        irregularidades = []
        for category in ["client_information", "evidence_review", "legal_compliance"]:
            for item in checklist.get(category, []):
                if item["status"] == ChecklistStatus.NO_CUMPLE.value and item.get("validated", False):
                    irregularidades.append(f"- {item['title']}: {item.get('description', 'No se cumplió con el requisito establecido.')}")
        
        if irregularidades:
            borrador += "\n".join(irregularidades) + "\n"
        else:
            borrador += "- Se requiere revisión adicional de la documentación presentada.\n"
        
        borrador += f"""
POR TANTO:
Se instruye a la empresa {empresa} a revisar y corregir las irregularidades señaladas, conforme a lo establecido en la normativa vigente, en particular lo dispuesto en el Decreto con Fuerza de Ley N°1/2006 del Ministerio de Economía, Fomento y Reconstrucción, que fija el texto refundido, coordinado y sistematizado de la Ley General de Servicios Eléctricos, y sus normas complementarias.

La empresa deberá informar a esta Superintendencia, dentro del plazo de 15 días hábiles, las medidas adoptadas para subsanar las irregularidades detectadas.
"""
        # Solo agregar contenido personalizado si se proporciona explícitamente y no es un borrador previo
        if request.content and request.content.strip() and not request.content.strip().startswith(('INSTRUCCIÓN', 'RESOLUCIÓN')):
            borrador += f"\n\n{request.content}"
    else:  # IMPROCEDENTE
        borrador = f"""RESOLUCIÓN IMPROCEDENTE

Caso SEC: {case_id}
Cliente: {client_name}
RUT: {rut_client}
Materia: {materia}

CONSIDERANDO:
1. Que se ha recibido el reclamo del cliente indicado.
2. Que tras el análisis exhaustivo de la documentación presentada por la empresa {empresa}, se ha verificado que ésta ha actuado conforme a la normativa vigente.
3. Que todos los requisitos legales y técnicos establecidos en el Decreto con Fuerza de Ley N°1/2006 y sus normas complementarias han sido cumplidos satisfactoriamente.
4. Que la empresa ha acreditado debidamente la regularidad de su actuación mediante la documentación técnica y legal correspondiente.

POR TANTO:
Se declara IMPROCEDENTE el presente reclamo, ratificando que la empresa {empresa} ha actuado conforme a la normativa vigente y no se han detectado irregularidades en su proceder.
"""
        # Solo agregar contenido personalizado si se proporciona explícitamente y no es un borrador previo
        if request.content and request.content.strip() and not request.content.strip().startswith(('INSTRUCCIÓN', 'RESOLUCIÓN')):
            borrador += f"\n\n{request.content}"
    
    return ResolucionResponse(borrador=borrador, template_type=template_type)

@router.post("/casos/{case_id}/cerrar")
def cerrar_caso(case_id: str, request: CerrarCasoRequest,
                x_app_mode: Optional[str] = Header(None, alias='X-App-Mode'),
                mode: Optional[str] = Query(None)):
    """Cierra un caso, actualizando su estado a CERRADO y guardando la resolución"""
    app_mode = get_app_mode(x_app_mode, mode)
    
    # Solo permitir en modo validate (casos reales)
    if app_mode == 'test':
        raise HTTPException(status_code=400, detail="No se puede cerrar caso en modo test")
    
    # Buscar caso en JSON DB
    casos_path = current_dir.parent / "data" / "DataBase" / "casos.json"
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
        fecha_cierre = request.fecha_cierre or datetime.now().isoformat()
        caso_encontrado["fecha_cierre"] = fecha_cierre
        
        # Guardar resolución si se proporciona
        if request.resolucion_content:
            if "resolucion" not in caso_encontrado:
                caso_encontrado["resolucion"] = {}
            caso_encontrado["resolucion"]["content"] = request.resolucion_content
            caso_encontrado["resolucion"]["fecha_firma"] = fecha_cierre
        
        # Guardar cambios en JSON
        casos[caso_index] = caso_encontrado
        with open(casos_path, "w", encoding="utf-8") as f:
            json.dump(casos, f, indent=2, ensure_ascii=False)
        
        # Recargar el caso desde la base de datos
        json_db_manager.reload_case(case_id)
        
        # Limpiar cache en memoria
        if case_id in cases_store:
            del cases_store[case_id]
        
        return {
            "message": "Caso cerrado exitosamente",
            "case_id": case_id,
            "estado": CaseStatus.CERRADO.value,
            "fecha_cierre": fecha_cierre
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
                          x_app_mode: Optional[str] = Header(None, alias='X-App-Mode'),
                          mode: Optional[str] = Query(None)):
    """Actualiza el contexto unificado y campos del caso, guardando en DataBase"""
    app_mode = get_app_mode(x_app_mode, mode)
    
    # Solo permitir en modo validate (casos reales)
    if app_mode == 'test':
        raise HTTPException(status_code=400, detail="No se puede editar en modo test")
    
    # Buscar caso en JSON DB
    casos_path = current_dir.parent / "data" / "DataBase" / "casos.json"
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
        
        # Actualizar unified_context
        if update.unified_context:
            if "unified_context" not in caso_encontrado["edn"]:
                caso_encontrado["edn"]["unified_context"] = {}
            
            for key, value in update.unified_context.items():
                caso_encontrado["edn"]["unified_context"][key] = value if value else None
        
        # Actualizar otros campos del caso
        if update.materia is not None:
            caso_encontrado["edn"]["materia"] = update.materia
            caso_encontrado["materia"] = update.materia
        
        if update.monto_disputa is not None:
            caso_encontrado["edn"]["monto_disputa"] = update.monto_disputa
            caso_encontrado["monto_disputa"] = update.monto_disputa
        
        if update.empresa is not None:
            caso_encontrado["edn"]["empresa"] = update.empresa
            caso_encontrado["empresa"] = update.empresa
        
        if update.fecha_ingreso is not None:
            caso_encontrado["edn"]["fecha_ingreso"] = update.fecha_ingreso
            caso_encontrado["fecha_ingreso"] = update.fecha_ingreso
        
        # Actualizar personas y suministros si cambió RUT o NIS
        if update.unified_context:
            unified_context = caso_encontrado["edn"]["unified_context"]
            
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
        
        # Guardar cambios en JSON
        casos[caso_index] = caso_encontrado
        with open(casos_path, "w", encoding="utf-8") as f:
            json.dump(casos, f, indent=2, ensure_ascii=False)
        
        # Recargar el caso desde la base de datos para reflejar cambios
        json_db_manager.reload_case(case_id)
        
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
    documentos_path = current_dir.parent / "data" / "DataBase" / "documentos.json"
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
        json_db_manager.reload()
    except Exception as e:
        print(f"Error guardando documento en DataBase: {e}")

def _update_persona_in_database(rut: str, nombre: str = None, email: str = None, telefono: str = None):
    """Actualiza persona en personas.json"""
    personas_path = current_dir.parent / "data" / "DataBase" / "personas.json"
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
        json_db_manager.reload()
    except Exception as e:
        print(f"Error actualizando persona: {e}")

def _update_suministro_in_database(nis: str, comuna: str = None, direccion: str = None):
    """Actualiza suministro en suministros.json"""
    suministros_path = current_dir.parent / "data" / "DataBase" / "suministros.json"
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
        json_db_manager.reload()
    except Exception as e:
        print(f"Error actualizando suministro: {e}")

@router.get("/casos/{case_id}/documentos/{file_id}/preview")
def preview_documento(case_id: str, file_id: str,
                     x_app_mode: Optional[str] = Header(None, alias='X-App-Mode'),
                     mode: Optional[str] = Query(None)):
    """Sirve el archivo del documento para vista previa"""
    current_dir = Path(__file__).parent
    
    # Buscar documento en documentos.json primero (más confiable)
    documento_encontrado = None
    documentos_path = current_dir.parent / "data" / "DataBase" / "documentos.json"
    
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
        app_mode = get_app_mode(x_app_mode, mode)
        casos_data = get_cases_data_with_mode(app_mode)
        
        for caso in casos_data:
            if caso["compilation_metadata"]["case_id"] == case_id:
                doc_inventory = caso["document_inventory"]
                for level in ["level_1_critical", "level_2_supporting"]:
                    for doc in doc_inventory.get(level, []):
                        if doc.get("file_id") == file_id:
                            documento_encontrado = doc
                            break
                    if documento_encontrado:
                        break
                if documento_encontrado:
                    break
    
    if not documento_encontrado:
        raise HTTPException(status_code=404, detail=f"Documento {file_id} no encontrado")
    
    # Determinar ruta del archivo
    file_path = None
    
    # Prioridad 1: absolute_path (puede ser ruta WSL o Windows)
    if documento_encontrado.get("absolute_path"):
        absolute_path_str = documento_encontrado["absolute_path"]
        file_path = Path(absolute_path_str)
        
        # Si es ruta WSL (/mnt/c/...), convertir a Windows si es necesario
        if absolute_path_str.startswith("/mnt/c/"):
            # Convertir /mnt/c/Users/... a C:/Users/...
            windows_path = absolute_path_str.replace("/mnt/c/", "C:/").replace("/", "\\")
            file_path = Path(windows_path)
        
        if file_path.exists():
            return _serve_file(file_path, documento_encontrado.get("original_name", "documento.pdf"))
    
    # Prioridad 2: file_path relativo desde example_cases
    if documento_encontrado.get("file_path"):
        example_cases_dir = current_dir.parent / "data" / "example_cases" / case_id
        file_path = example_cases_dir / documento_encontrado["file_path"]
        
        if file_path.exists():
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

