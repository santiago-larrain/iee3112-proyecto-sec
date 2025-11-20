from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class DocumentType(str, Enum):
    CARTA_RESPUESTA = "CARTA_RESPUESTA"
    ORDEN_TRABAJO = "ORDEN_TRABAJO"
    TABLA_CALCULO = "TABLA_CALCULO"
    EVIDENCIA_FOTOGRAFICA = "EVIDENCIA_FOTOGRAFICA"
    GRAFICO_CONSUMO = "GRAFICO_CONSUMO"
    OTROS = "OTROS"

class ChecklistStatus(str, Enum):
    CUMPLE = "CUMPLE"  # Verde ✅
    NO_CUMPLE = "NO_CUMPLE"  # Rojo ❌
    REVISION_MANUAL = "REVISION_MANUAL"  # Amarillo ⚠️

class CaseStatus(str, Enum):
    PENDIENTE = "PENDIENTE"
    EN_REVISION = "EN_REVISION"
    RESUELTO = "RESUELTO"
    CERRADO = "CERRADO"

class CerrarCasoRequest(BaseModel):
    resolucion_content: Optional[str] = None
    fecha_cierre: Optional[str] = None

class CompilationMetadata(BaseModel):
    case_id: str
    processing_timestamp: str
    status: str

class UnifiedContext(BaseModel):
    rut_client: str = "N/A"
    client_name: str = "N/A"
    service_nis: str = "N/A"
    address_standard: Optional[str] = None
    commune: str = "Desconocida"
    email: Optional[str] = None
    phone: Optional[str] = None

class Document(BaseModel):
    type: str
    file_id: str
    original_name: str
    standardized_name: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class MissingDocument(BaseModel):
    required_type: str
    alert_level: str
    description: str

class DocumentInventory(BaseModel):
    level_1_critical: List[Document]
    level_2_supporting: List[Document]
    level_0_missing: List[MissingDocument]

class ChecklistItem(BaseModel):
    id: str
    title: str
    status: ChecklistStatus
    evidence: Optional[str] = None
    evidence_type: Optional[str] = None  # "dato" o "archivo"
    validated: bool = False
    description: Optional[str] = None

class Checklist(BaseModel):
    # Estructura nueva (CNR)
    group_a_admisibilidad: Optional[List[ChecklistItem]] = None
    group_b_instruccion: Optional[List[ChecklistItem]] = None
    group_c_analisis: Optional[Dict[str, Any]] = None  # {c1_acreditacion_hecho: [], c2_legalidad_cobro: []}
    metadata: Optional[Dict[str, Any]] = None
    
    # Estructura antigua (compatibilidad)
    client_information: Optional[List[ChecklistItem]] = None
    evidence_review: Optional[List[ChecklistItem]] = None
    legal_compliance: Optional[List[ChecklistItem]] = None
    
    class Config:
        extra = "allow"  # Permitir campos adicionales

class ExpedienteDigitalNormalizado(BaseModel):
    compilation_metadata: CompilationMetadata
    unified_context: UnifiedContext
    document_inventory: DocumentInventory
    checklist: Optional[Checklist] = None
    materia: Optional[str] = None
    monto_disputa: Optional[float] = None
    empresa: Optional[str] = None
    fecha_ingreso: Optional[str] = None
    alertas: Optional[List[str]] = None  # ["Electrodependiente", "Reincidente", etc.]

class CaseSummary(BaseModel):
    case_id: str
    client_name: str
    rut_client: str
    materia: str
    monto_disputa: float
    status: CaseStatus
    fecha_ingreso: str
    empresa: str

class DocumentUpdateRequest(BaseModel):
    type: DocumentType
    custom_name: Optional[str] = None  # Nombre personalizado del documento

class ChecklistItemUpdateRequest(BaseModel):
    validated: bool

class ResolucionRequest(BaseModel):
    template_type: str  # "INSTRUCCION" o "IMPROCEDENTE"
    content: Optional[str] = None

class ResolucionResponse(BaseModel):
    borrador: str
    template_type: str

class UnifiedContextUpdateRequest(BaseModel):
    unified_context: Optional[Dict[str, Any]] = None
    materia: Optional[str] = None
    monto_disputa: Optional[float] = None
    empresa: Optional[str] = None
    fecha_ingreso: Optional[str] = None

