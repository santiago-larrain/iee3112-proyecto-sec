"""
Clasificador de documentos basado en heurísticas
"""

import re
from pathlib import Path
from typing import Optional, Dict
from enum import Enum

class DocumentType(str, Enum):
    CARTA_RESPUESTA = "CARTA_RESPUESTA"
    ORDEN_TRABAJO = "ORDEN_TRABAJO"
    TABLA_CALCULO = "TABLA_CALCULO"
    EVIDENCIA_FOTOGRAFICA = "EVIDENCIA_FOTOGRAFICA"
    GRAFICO_CONSUMO = "GRAFICO_CONSUMO"
    INFORME_CNR = "INFORME_CNR"
    OTROS = "OTROS"


class DocumentClassifier:
    """Clasifica documentos según heurísticas de nombre y contenido"""
    
    def classify_tipo_caso(self, document_inventory: Dict, unified_context: Dict) -> str:
        """
        Determina el tipo de caso (CNR, CORTE_SUMINISTRO, etc.) basado en documentos y contexto
        
        Args:
            document_inventory: Inventario de documentos procesados
            unified_context: Contexto unificado del caso
            
        Returns:
            Tipo de caso: CNR, CORTE_SUMINISTRO, DAÑO_EQUIPOS, ATENCION_COMERCIAL
        """
        # Obtener tipos de documentos presentes
        doc_types = set()
        for level in ["level_1_critical", "level_2_supporting"]:
            for doc in document_inventory.get(level, []):
                doc_types.add(doc.get("type"))
        
        # Heurística 1: Si hay Orden de Trabajo y Tabla de Cálculo -> CNR
        if "ORDEN_TRABAJO" in doc_types and "TABLA_CALCULO" in doc_types:
            return "CNR"
        
        # Heurística 2: Si hay palabras clave de corte de suministro
        # (esto se puede mejorar con análisis de contenido)
        for level in ["level_1_critical", "level_2_supporting"]:
            for doc in document_inventory.get(level, []):
                name = doc.get("original_name", "").lower()
                if any(keyword in name for keyword in ["corte", "suspension", "suministro"]):
                    return "CORTE_SUMINISTRO"
        
        # Heurística 3: Si hay evidencia fotográfica de daños
        if "EVIDENCIA_FOTOGRAFICA" in doc_types:
            # Verificar tags de imágenes
            for level in ["level_1_critical", "level_2_supporting"]:
                for doc in document_inventory.get(level, []):
                    if doc.get("type") == "EVIDENCIA_FOTOGRAFICA":
                        metadata = doc.get("metadata", {})
                        tags = metadata.get("tags", [])
                        if any(tag in ["daño", "rotura", "averia"] for tag in tags):
                            return "DAÑO_EQUIPOS"
        
        # Por defecto, si no se puede determinar, asumir CNR (más común)
        return "CNR"
    
    def classify(self, file_path: Path, content: Optional[str] = None) -> str:
        """
        Clasifica un documento según su nombre y contenido
        
        Args:
            file_path: Ruta al archivo
            content: Contenido de texto extraído (opcional)
            
        Returns:
            Tipo de documento según DocumentType
        """
        file_name_lower = file_path.name.lower()
        file_ext = file_path.suffix.lower()
        content_lower = (content or "").lower()
        
        # EVIDENCIA_FOTOGRAFICA - Por extensión
        if file_ext in ['.jpg', '.jpeg', '.png', '.gif']:
            return DocumentType.EVIDENCIA_FOTOGRAFICA.value
        
        # Patrones en nombre de archivo
        if self._matches_pattern(file_name_lower, [
            'fotografias', 'fotos', 'fachada', 'imagen', 'cam_', 'foto'
        ]):
            return DocumentType.EVIDENCIA_FOTOGRAFICA.value
        
        # CARTA_RESPUESTA
        if self._matches_pattern(file_name_lower, [
            'respuesta', 'rpt_cnr', 'resolucion', 'resolución', 'rpt_'
        ]):
            return DocumentType.CARTA_RESPUESTA.value
        
        if self._matches_pattern(content_lower, [
            'respuesta al reclamo', 'resolución', 'resolucion', 'cnr'
        ]):
            return DocumentType.CARTA_RESPUESTA.value
        
        # ORDEN_TRABAJO
        if self._matches_pattern(file_name_lower, [
            'orden de trabajo', 'orden_trabajo', 'ot_', 'ot ', 'trabajo técnico'
        ]):
            return DocumentType.ORDEN_TRABAJO.value
        
        if self._matches_pattern(content_lower, [
            'orden de trabajo', 'orden n°', 'trabajo técnico', 'visita técnica'
        ]):
            return DocumentType.ORDEN_TRABAJO.value
        
        # TABLA_CALCULO
        if self._matches_pattern(file_name_lower, [
            'calculo', 'cálculo', 'calculacion', 'cnr', 'tabla'
        ]):
            return DocumentType.TABLA_CALCULO.value
        
        if self._matches_pattern(content_lower, [
            'cálculo', 'calculo', 'consumo indicado mensual', 'cim', 'kwh'
        ]):
            return DocumentType.TABLA_CALCULO.value
        
        # GRAFICO_CONSUMO
        if self._matches_pattern(file_name_lower, [
            'consumos', 'consumo', 'grafico', 'gráfico', 'periodo'
        ]):
            return DocumentType.GRAFICO_CONSUMO.value
        
        if self._matches_pattern(content_lower, [
            'gráfico de consumo', 'historial de consumo', 'periodo de consumo'
        ]):
            return DocumentType.GRAFICO_CONSUMO.value
        
        # INFORME_CNR
        if self._matches_pattern(file_name_lower, [
            'informe', 'informe cnr', 'informe instalación', 'instalación'
        ]):
            return DocumentType.INFORME_CNR.value
        
        if self._matches_pattern(content_lower, [
            'informe técnico', 'informe de instalación', 'equipo de medida'
        ]):
            return DocumentType.INFORME_CNR.value
        
        return DocumentType.OTROS.value
    
    def _matches_pattern(self, text: str, patterns: list) -> bool:
        """Verifica si el texto coincide con alguno de los patrones"""
        for pattern in patterns:
            if pattern in text:
                return True
        return False
    
    def determine_level(self, doc_type: str) -> str:
        """
        Determina el nivel de importancia del documento
        
        Args:
            doc_type: Tipo de documento
            
        Returns:
            'level_1_critical' o 'level_2_supporting'
        """
        critical_types = [
            DocumentType.CARTA_RESPUESTA.value,
            DocumentType.TABLA_CALCULO.value,
            DocumentType.ORDEN_TRABAJO.value
        ]
        
        if doc_type in critical_types:
            return 'level_1_critical'
        else:
            return 'level_2_supporting'

