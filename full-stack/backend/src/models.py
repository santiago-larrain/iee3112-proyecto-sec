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
    INFORME_CNR = "INFORME_CNR"
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
    tipo_caso: Optional[str] = None  # CNR, CORTE_SUMINISTRO, DAÑO_EQUIPOS, ATENCION_COMERCIAL

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
    # Categorías funcionales (nueva estructura)
    reclamo_respuesta: Optional[List[Document]] = None  # Reclamo y respuesta de la empresa
    informe_evidencias: Optional[List[Document]] = None  # Informe de laboratorio/evidencias
    historial_calculos: Optional[List[Document]] = None  # Historial de consumo y cálculos
    otros: Optional[List[Document]] = None  # Otros documentos
    
    # Estructura antigua (compatibilidad)
    level_1_critical: List[Document] = []
    level_2_supporting: List[Document] = []
    level_0_missing: List[MissingDocument] = []
    
    class Config:
        extra = "allow"  # Permitir campos adicionales

class SourceReference(BaseModel):
    """Referencia a la fuente de un dato extraído con información de posición"""
    file_ref: str  # file_id del documento
    page_index: Optional[int] = None  # Índice de página (0-based)
    coordinates: Optional[List[float]] = None  # [x, y, width, height] para bbox

class ExtractedDataWithSource(BaseModel):
    """Dato extraído con referencia a su fuente"""
    value: Any  # El valor extraído (número, texto, etc.)
    source: Optional[SourceReference] = None

class ChecklistItem(BaseModel):
    id: str
    title: str
    status: ChecklistStatus
    evidence: Optional[str] = None
    evidence_type: Optional[str] = None  # "dato" o "archivo"
    validated: bool = False
    description: Optional[str] = None
    evidence_data: Optional[Dict[str, Any]] = None  # Datos con deep linking
    rule_ref: Optional[str] = None  # Referencia a la regla que lo generó

class Checklist(BaseModel):
    # Estructura nueva (CNR)
    group_a_admisibilidad: Optional[List[ChecklistItem]] = None
    group_b_instruccion: Optional[List[ChecklistItem]] = None
    group_c_analisis: Optional[List[ChecklistItem]] = None  # Lista plana de items (subgrupos aplanados)
    metadata: Optional[Dict[str, Any]] = None
    
    # Estructura antigua (compatibilidad)
    client_information: Optional[List[ChecklistItem]] = None
    evidence_review: Optional[List[ChecklistItem]] = None
    legal_compliance: Optional[List[ChecklistItem]] = None
    
    class Config:
        extra = "allow"  # Permitir campos adicionales

class EvidenceEntry(BaseModel):
    """Entrada individual en el mapa de evidencias"""
    tipo: str  # "texto", "foto", "imagen"
    documento: Optional[str] = None  # Nombre del documento o file_id
    archivo: Optional[str] = None  # Nombre del archivo (para fotos)
    pagina: Optional[int] = None  # Número de página (0-based o 1-based según contexto)
    snippet: Optional[str] = None  # Fragmento de texto extraído exacto
    descripcion: Optional[str] = None  # Descripción de la evidencia
    etiqueta: Optional[str] = None  # Etiqueta para fotos (ej: "irregularidad_medidor")
    coordinates: Optional[List[float]] = None  # [x, y, width, height] para bbox

class EvidenceMap(BaseModel):
    """Mapa que vincula cada fact con su fuente exacta"""
    # El mapa es un diccionario donde cada key es el nombre de un feature
    # y el value es una lista de EvidenceEntry
    # Ejemplo: {"periodo_meses": [EvidenceEntry(...)], "monto_cnr": [EvidenceEntry(...)]}
    pass  # Se implementa como Dict[str, List[EvidenceEntry]] en el modelo principal

class ExpedienteDigitalNormalizado(BaseModel):
    compilation_metadata: CompilationMetadata
    unified_context: UnifiedContext
    document_inventory: DocumentInventory
    consolidated_facts: Optional[Dict[str, Any]] = None  # Features consolidados (alias: features)
    evidence_map: Optional[Dict[str, List[Dict[str, Any]]]] = None  # Mapa de evidencias (alias: evidencias)
    checklist: Optional[Checklist] = None
    materia: Optional[str] = None
    monto_disputa: Optional[float] = None
    empresa: Optional[str] = None
    fecha_ingreso: Optional[str] = None
    alertas: Optional[List[str]] = None  # ["Electrodependiente", "Reincidente", etc.]
    
    class Config:
        # Permitir acceso por alias
        populate_by_name = True

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

