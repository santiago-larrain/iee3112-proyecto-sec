"""
Extractor de hechos (facts) desde documentos
Implementa la lógica de extracción de features desde texto, boletas y fotos
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def extraer_desde_texto(
    texto_normalizado: str,
    metadatos_caso: Dict[str, Any],
    documentos_procesados: List[Dict[str, Any]]
) -> Tuple[Dict[str, Any], Dict[str, List[Dict[str, Any]]]]:
    """
    Analiza el texto e identifica el período del CNR, origen, historial de 12 meses, etc.
    
    Args:
        texto_normalizado: Texto extraído de todos los documentos concatenados
        metadatos_caso: Metadatos del caso (materia, empresa, etc.)
        documentos_procesados: Lista de documentos procesados con sus metadatos
        
    Returns:
        Tuple de (features_texto, evidencias_texto)
        - features_texto: Diccionario con features extraídos
        - evidencias_texto: Mapa de evidencias con snippets y referencias
    """
    features = {}
    evidencias = {}
    
    # 1. Extraer período (meses)
    periodo_meses, evidencia_periodo = _extraer_periodo_meses(texto_normalizado, documentos_procesados)
    if periodo_meses is not None:
        features["periodo_meses"] = periodo_meses
        evidencias["periodo_meses"] = evidencia_periodo
    
    # 2. Extraer fechas de inicio y término
    fecha_inicio, fecha_termino, evidencia_fechas = _extraer_fechas_periodo(
        texto_normalizado, documentos_procesados
    )
    if fecha_inicio:
        features["fecha_inicio"] = fecha_inicio
    if fecha_termino:
        features["fecha_termino"] = fecha_termino
    if evidencia_fechas:
        evidencias["fecha_inicio"] = evidencia_fechas.get("inicio", [])
        evidencias["fecha_termino"] = evidencia_fechas.get("termino", [])
    
    # 3. Extraer origen de la irregularidad
    origen, descripcion_origen, evidencia_origen = _extraer_origen_irregularidad(
        texto_normalizado, documentos_procesados
    )
    if origen:
        features["origen"] = origen
    if descripcion_origen:
        features["descripcion_origen"] = descripcion_origen
    if evidencia_origen:
        evidencias["origen"] = evidencia_origen
    
    # 4. Detectar historial de 12 meses
    historial_12_meses, historial_fuente, evidencia_historial = _detectar_historial_12_meses(
        texto_normalizado, documentos_procesados
    )
    if historial_12_meses is not None:
        features["historial_12_meses_disponible"] = historial_12_meses
    if historial_fuente:
        features["historial_fuente"] = historial_fuente
    if evidencia_historial:
        evidencias["historial_12_meses_disponible"] = evidencia_historial
    
    # 5. Detectar gráfico de consumo
    tiene_grafico, grafico_fuente, evidencia_grafico = _detectar_grafico_consumo(
        texto_normalizado, documentos_procesados
    )
    if tiene_grafico is not None:
        features["tiene_grafico_consumo"] = tiene_grafico
    if grafico_fuente:
        features["grafico_fuente"] = grafico_fuente
    if evidencia_grafico:
        evidencias["tiene_grafico_consumo"] = evidencia_grafico
    
    # 6. Detectar fotos de irregularidad
    tiene_fotos, tiene_foto_medidor, tiene_foto_sello, evidencia_fotos = _detectar_fotos_irregularidad(
        documentos_procesados
    )
    if tiene_fotos is not None:
        features["tiene_fotos_irregularidad"] = tiene_fotos
    if tiene_foto_medidor is not None:
        features["tiene_foto_medidor"] = tiene_foto_medidor
    if tiene_foto_sello is not None:
        features["tiene_foto_sello"] = tiene_foto_sello
    if evidencia_fotos:
        evidencias["tiene_fotos_irregularidad"] = evidencia_fotos
    
    # 7. Extraer monto CNR
    monto_cnr, evidencia_monto = _extraer_monto_cnr(texto_normalizado, documentos_procesados)
    if monto_cnr is not None:
        features["monto_cnr"] = monto_cnr
        evidencias["monto_cnr"] = evidencia_monto
    
    # 8. Detectar notificación previa
    notificacion_previa, evidencia_notificacion = _detectar_notificacion_previa(
        texto_normalizado, documentos_procesados
    )
    if notificacion_previa is not None:
        features["notificacion_previa_en_boleta"] = notificacion_previa
        if evidencia_notificacion:
            evidencias["notificacion_previa_en_boleta"] = evidencia_notificacion
    
    # 9. Detectar constancia notarial
    hay_constancia, evidencia_constancia = _detectar_constancia_notarial(
        texto_normalizado, documentos_procesados
    )
    if hay_constancia is not None:
        features["hay_constancia_notarial"] = hay_constancia
        if evidencia_constancia:
            evidencias["hay_constancia_notarial"] = evidencia_constancia
    
    # 10. Detectar certificado de laboratorio
    hay_certificado, evidencia_certificado = _detectar_certificado_laboratorio(
        texto_normalizado, documentos_procesados
    )
    if hay_certificado is not None:
        features["hay_certificado_laboratorio"] = hay_certificado
        if evidencia_certificado:
            evidencias["hay_certificado_laboratorio"] = evidencia_certificado
    
    return features, evidencias


def construir_features(
    expediente: Dict[str, Any],
    texto_normalizado: str,
    boletas: List[Dict[str, Any]],
    fotos: List[Dict[str, Any]]
) -> Tuple[Dict[str, Any], Dict[str, List[Dict[str, Any]]]]:
    """
    Une la información extraída desde texto, boletas y fotos.
    
    Args:
        expediente: Expediente con documentos procesados
        texto_normalizado: Texto extraído de documentos
        boletas: Lista de boletas procesadas
        fotos: Lista de fotos procesadas
        
    Returns:
        Tuple de (features, mapa_evidencias)
    """
    metadatos_caso = {
        "materia": expediente.get("materia"),
        "empresa": expediente.get("empresa"),
        "fecha_ingreso": expediente.get("fecha_ingreso")
    }
    
    documentos_procesados = expediente.get("document_inventory", {}).get("level_1_critical", [])
    documentos_procesados.extend(expediente.get("document_inventory", {}).get("level_2_supporting", []))
    
    # Extraer desde texto
    features_texto, evidencias_texto = extraer_desde_texto(
        texto_normalizado, metadatos_caso, documentos_procesados
    )
    
    # Extraer desde boletas (si hay)
    features_boletas, evidencias_boletas = _extraer_desde_boletas(boletas)
    
    # Extraer desde fotos (si hay)
    features_fotos, evidencias_fotos = _extraer_desde_fotos(fotos)
    
    # Consolidar features (prioridad: texto > boletas > fotos)
    features_consolidados = {}
    evidencias_consolidadas = {}
    
    # Agregar features de texto
    features_consolidados.update(features_texto)
    evidencias_consolidadas.update(evidencias_texto)
    
    # Agregar features de boletas (solo si no existen en texto)
    for key, value in features_boletas.items():
        if key not in features_consolidados:
            features_consolidados[key] = value
    for key, value in evidencias_boletas.items():
        if key not in evidencias_consolidadas:
            evidencias_consolidadas[key] = value
    
    # Agregar features de fotos (solo si no existen)
    for key, value in features_fotos.items():
        if key not in features_consolidados:
            features_consolidados[key] = value
    for key, value in evidencias_fotos.items():
        if key not in evidencias_consolidadas:
            evidencias_consolidadas[key] = value
    
    return features_consolidados, evidencias_consolidadas


# Funciones auxiliares de extracción

def _extraer_periodo_meses(
    texto: str, documentos: List[Dict[str, Any]]
) -> Tuple[Optional[int], List[Dict[str, Any]]]:
    """Extrae el período en meses del CNR"""
    evidencias = []
    
    # Patrones para buscar período
    patrones = [
        r"periodo\s+de\s+(\d+)\s+meses",
        r"(\d+)\s+meses?\s+de\s+consumo",
        r"periodo\s+comprendido\s+entre.*?(\d+)\s+meses",
        r"(\d+)\s+cuotas?",
    ]
    
    for patron in patrones:
        match = re.search(patron, texto, re.IGNORECASE)
        if match:
            meses = int(match.group(1))
            # Buscar snippet en el documento
            snippet = _extraer_snippet(texto, match.start(), match.end(), 50)
            # Buscar documento fuente
            doc_fuente = _buscar_documento_fuente(texto, documentos)
            if doc_fuente:
                evidencias.append({
                    "tipo": "texto",
                    "documento": doc_fuente.get("original_name", ""),
                    "pagina": 0,  # Se puede mejorar extrayendo página específica
                    "snippet": snippet
                })
            return meses, evidencias
    
    return None, []


def _extraer_fechas_periodo(
    texto: str, documentos: List[Dict[str, Any]]
) -> Tuple[Optional[str], Optional[str], Dict[str, List[Dict[str, Any]]]]:
    """Extrae fechas de inicio y término del período"""
    evidencias = {"inicio": [], "termino": []}
    
    # Patrón para rango de fechas
    patron_rango = r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\s*(?:y|al|hasta|-\s*)\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})"
    match = re.search(patron_rango, texto, re.IGNORECASE)
    
    if match:
        fecha_inicio = match.group(1)
        fecha_termino = match.group(2)
        snippet = _extraer_snippet(texto, match.start(), match.end(), 100)
        doc_fuente = _buscar_documento_fuente(texto, documentos)
        
        if doc_fuente:
            evidencias["inicio"].append({
                "tipo": "texto",
                "documento": doc_fuente.get("original_name", ""),
                "pagina": 0,
                "snippet": snippet
            })
            evidencias["termino"] = evidencias["inicio"].copy()
        
        return fecha_inicio, fecha_termino, evidencias
    
    return None, None, {}


def _extraer_origen_irregularidad(
    texto: str, documentos: List[Dict[str, Any]]
) -> Tuple[Optional[str], Optional[str], List[Dict[str, Any]]]:
    """Extrae el origen de la irregularidad (bypass, medidor defectuoso, etc.)"""
    evidencias = []
    origen = None
    descripcion = None
    
    # Palabras clave comunes
    keywords_origen = {
        "bypass": "conexion_irregular",
        "conexión irregular": "conexion_irregular",
        "medidor defectuoso": "medidor_defectuoso",
        "medidor sin sello": "medidor_sin_sello",
        "manipulación": "manipulacion",
    }
    
    texto_lower = texto.lower()
    for keyword, tipo_origen in keywords_origen.items():
        if keyword in texto_lower:
            origen = tipo_origen
            descripcion = keyword
            # Buscar snippet
            idx = texto_lower.find(keyword)
            snippet = _extraer_snippet(texto, idx, idx + len(keyword), 100)
            doc_fuente = _buscar_documento_fuente(texto, documentos)
            
            if doc_fuente:
                evidencias.append({
                    "tipo": "texto",
                    "documento": doc_fuente.get("original_name", ""),
                    "pagina": 0,
                    "snippet": snippet
                })
            break
    
    return origen, descripcion, evidencias


def _detectar_historial_12_meses(
    texto: str, documentos: List[Dict[str, Any]]
) -> Tuple[Optional[bool], Optional[str], List[Dict[str, Any]]]:
    """Detecta si hay historial de 12 meses disponible"""
    evidencias = []
    
    # Buscar referencias a historial
    patrones = [
        r"historial\s+de\s+12\s+meses",
        r"12\s+meses\s+de\s+consumo",
        r"gráfico\s+de\s+consumo\s+histórico",
    ]
    
    for patron in patrones:
        if re.search(patron, texto, re.IGNORECASE):
            fuente = "grafico_informe"
            doc_fuente = _buscar_documento_fuente(texto, documentos)
            if doc_fuente:
                evidencias.append({
                    "tipo": "texto",
                    "documento": doc_fuente.get("original_name", ""),
                    "pagina": 0,
                    "snippet": "historial de 12 meses disponible"
                })
            return True, fuente, evidencias
    
    return None, None, []


def _detectar_grafico_consumo(
    texto: str, documentos: List[Dict[str, Any]]
) -> Tuple[Optional[bool], Optional[str], List[Dict[str, Any]]]:
    """Detecta si hay gráfico de consumo"""
    evidencias = []
    
    # Buscar referencias a gráfico
    patrones = [
        r"gráfico\s+de\s+consumo",
        r"gráfico\s+histórico",
        r"historial\s+gráfico",
    ]
    
    for patron in patrones:
        if re.search(patron, texto, re.IGNORECASE):
            # Buscar documento fuente
            doc_fuente = _buscar_documento_fuente(texto, documentos)
            fuente = doc_fuente.get("original_name", "") if doc_fuente else "informe_tecnico.pdf"
            
            evidencias.append({
                "tipo": "imagen",
                "documento": fuente,
                "pagina": 0,
                "descripcion": "gráfico de consumo histórico"
            })
            return True, fuente, evidencias
    
    return None, None, []


def _detectar_fotos_irregularidad(
    documentos: List[Dict[str, Any]]
) -> Tuple[Optional[bool], Optional[bool], Optional[bool], List[Dict[str, Any]]]:
    """Detecta fotos de irregularidad, medidor y sello"""
    evidencias = []
    tiene_fotos = False
    tiene_medidor = False
    tiene_sello = False
    
    for doc in documentos:
        if doc.get("type") == "EVIDENCIA_FOTOGRAFICA":
            tiene_fotos = True
            metadata = doc.get("metadata", {})
            tags = metadata.get("tags", [])
            
            if "medidor" in tags or "medicion" in tags:
                tiene_medidor = True
            if "sello" in tags:
                tiene_sello = True
            
            evidencias.append({
                "tipo": "foto",
                "archivo": doc.get("original_name", ""),
                "etiqueta": tags[0] if tags else "general"
            })
    
    return tiene_fotos, tiene_medidor, tiene_sello, evidencias


def _extraer_monto_cnr(
    texto: str, documentos: List[Dict[str, Any]]
) -> Tuple[Optional[float], List[Dict[str, Any]]]:
    """Extrae el monto CNR"""
    evidencias = []
    
    # Patrones para buscar monto CNR
    patrones = [
        r"consumos\s+no\s+registrados[:\s]*\$?\s*(\d{1,3}(?:\.\d{3})*(?:,\d+)?)",
        r"monto\s+cnr[:\s]*\$?\s*(\d{1,3}(?:\.\d{3})*(?:,\d+)?)",
        r"total\s+cnr[:\s]*\$?\s*(\d{1,3}(?:\.\d{3})*(?:,\d+)?)",
    ]
    
    for patron in patrones:
        match = re.search(patron, texto, re.IGNORECASE)
        if match:
            monto_str = match.group(1).replace(".", "").replace(",", ".")
            try:
                monto = float(monto_str)
                snippet = _extraer_snippet(texto, match.start(), match.end(), 50)
                doc_fuente = _buscar_documento_fuente(texto, documentos)
                
                if doc_fuente:
                    evidencias.append({
                        "tipo": "texto",
                        "documento": doc_fuente.get("original_name", ""),
                        "pagina": 0,
                        "snippet": snippet
                    })
                return monto, evidencias
            except ValueError:
                continue
    
    return None, []


def _detectar_notificacion_previa(
    texto: str, documentos: List[Dict[str, Any]]
) -> Tuple[Optional[bool], List[Dict[str, Any]]]:
    """Detecta si hay notificación previa en boleta"""
    evidencias = []
    
    keywords = ["notificación previa", "notificado en boleta", "aviso previo"]
    texto_lower = texto.lower()
    
    for keyword in keywords:
        if keyword in texto_lower:
            doc_fuente = _buscar_documento_fuente(texto, documentos)
            if doc_fuente:
                evidencias.append({
                    "tipo": "texto",
                    "documento": doc_fuente.get("original_name", ""),
                    "pagina": 0,
                    "snippet": keyword
                })
            return True, evidencias
    
    return False, []


def _detectar_constancia_notarial(
    texto: str, documentos: List[Dict[str, Any]]
) -> Tuple[Optional[bool], List[Dict[str, Any]]]:
    """Detecta si hay constancia notarial"""
    evidencias = []
    
    keywords = ["constancia notarial", "notario", "notaría"]
    texto_lower = texto.lower()
    
    for keyword in keywords:
        if keyword in texto_lower:
            doc_fuente = _buscar_documento_fuente(texto, documentos)
            if doc_fuente:
                evidencias.append({
                    "tipo": "texto",
                    "documento": doc_fuente.get("original_name", ""),
                    "pagina": 0,
                    "snippet": keyword
                })
            return True, evidencias
    
    return False, []


def _detectar_certificado_laboratorio(
    texto: str, documentos: List[Dict[str, Any]]
) -> Tuple[Optional[bool], List[Dict[str, Any]]]:
    """Detecta si hay certificado de laboratorio"""
    evidencias = []
    
    keywords = ["certificado laboratorio", "certificado de laboratorio", "prueba laboratorio"]
    texto_lower = texto.lower()
    
    for keyword in keywords:
        if keyword in texto_lower:
            doc_fuente = _buscar_documento_fuente(texto, documentos)
            if doc_fuente:
                evidencias.append({
                    "tipo": "texto",
                    "documento": doc_fuente.get("original_name", ""),
                    "pagina": 0,
                    "snippet": keyword
                })
            return True, evidencias
    
    return False, []


def _extraer_desde_boletas(boletas: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], Dict[str, List[Dict[str, Any]]]]:
    """Extrae features desde boletas"""
    features = {}
    evidencias = {}
    # Implementación futura para extraer desde boletas
    return features, evidencias


def _extraer_desde_fotos(fotos: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], Dict[str, List[Dict[str, Any]]]]:
    """Extrae features desde fotos"""
    features = {}
    evidencias = {}
    # Implementación futura para extraer desde fotos con CV
    return features, evidencias


def _extraer_snippet(texto: str, start: int, end: int, context: int = 50) -> str:
    """Extrae un snippet de texto con contexto"""
    snippet_start = max(0, start - context)
    snippet_end = min(len(texto), end + context)
    snippet = texto[snippet_start:snippet_end].strip()
    # Limpiar espacios múltiples
    snippet = re.sub(r'\s+', ' ', snippet)
    return snippet


def _buscar_documento_fuente(texto: str, documentos: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Busca el documento fuente del texto (heurística simple)"""
    # Por ahora, retornar el primer documento crítico
    # En el futuro, se puede mejorar con análisis más sofisticado
    for doc in documentos:
        if doc.get("type") in ["ORDEN_TRABAJO", "TABLA_CALCULO", "CARTA_RESPUESTA"]:
            return doc
    return documentos[0] if documentos else None

