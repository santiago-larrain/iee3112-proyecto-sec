"""
Selector de estrategia para extracción de features desde múltiples fuentes
Implementa heurísticas de fallback para decidir la mejor fuente de datos
"""

from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def extraer_desde_fuentes(
    documentos_procesados: List[Dict[str, Any]],
    expediente: Dict[str, Any]
) -> Tuple[Dict[str, Any], Dict[str, List[Dict[str, Any]]]]:
    """
    Decide desde dónde obtener el gráfico de consumo y otros features.
    Estrategia de fallback: informe → fotos → boleta/webscraping
    
    Args:
        documentos_procesados: Lista de documentos procesados
        expediente: Expediente completo con contexto
        
    Returns:
        Tuple de (features, evidencias) asociados al gráfico de consumo y otros datos
    """
    features = {}
    evidencias = {}
    
    # Estrategia 1: Buscar gráfico en Informe Técnico
    grafico_info, evidencia_grafico = _buscar_grafico_en_informe(documentos_procesados)
    if grafico_info:
        features.update(grafico_info)
        evidencias.update(evidencia_grafico)
        logger.info("Gráfico encontrado en Informe Técnico")
        return features, evidencias
    
    # Estrategia 2: Buscar gráfico en Fotos
    grafico_info, evidencia_grafico = _buscar_grafico_en_fotos(documentos_procesados)
    if grafico_info:
        features.update(grafico_info)
        evidencias.update(evidencia_grafico)
        logger.info("Gráfico encontrado en Fotos")
        return features, evidencias
    
    # Estrategia 3: Intentar extraer desde Boleta (requiere OCR/webscraping)
    grafico_info, evidencia_grafico = _buscar_grafico_en_boleta(documentos_procesados, expediente)
    if grafico_info:
        features.update(grafico_info)
        evidencias.update(evidencia_grafico)
        logger.info("Gráfico encontrado en Boleta")
        return features, evidencias
    
    # Si no se encuentra, marcar como no disponible
    features["tiene_grafico_consumo"] = False
    features["grafico_fuente"] = None
    logger.warning("No se encontró gráfico de consumo en ninguna fuente")
    
    return features, evidencias


def _buscar_grafico_en_informe(
    documentos: List[Dict[str, Any]]
) -> Tuple[Optional[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
    """
    Busca gráfico de consumo en Informe Técnico o documentos similares
    """
    features = {}
    evidencias = {}
    
    # Buscar documentos de tipo INFORME_CNR o que contengan "informe" en el nombre
    for doc in documentos:
        doc_type = doc.get("type", "")
        original_name = doc.get("original_name", "").lower()
        
        if doc_type == "INFORME_CNR" or "informe" in original_name:
            # Verificar si tiene gráfico (por ahora, asumir que sí si es informe)
            extracted_data = doc.get("extracted_data", {})
            metadata = doc.get("metadata", {})
            
            # Buscar referencias a gráfico en extracted_data o metadata
            if _tiene_referencia_grafico(extracted_data, metadata):
                features["tiene_grafico_consumo"] = True
                features["grafico_fuente"] = doc.get("original_name", "informe_tecnico.pdf")
                features["historial_fuente"] = "grafico_informe"
                features["historial_12_meses_disponible"] = True
                
                evidencias["tiene_grafico_consumo"] = [{
                    "tipo": "imagen",
                    "documento": doc.get("original_name", ""),
                    "pagina": 0,  # Se puede mejorar extrayendo página específica
                    "descripcion": "gráfico de consumo histórico de 12 meses"
                }]
                
                evidencias["historial_12_meses_disponible"] = [{
                    "tipo": "texto",
                    "documento": doc.get("original_name", ""),
                    "pagina": 0,
                    "snippet": "historial de 12 meses disponible en informe"
                }]
                
                return features, evidencias
    
    return None, {}


def _buscar_grafico_en_fotos(
    documentos: List[Dict[str, Any]]
) -> Tuple[Optional[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
    """
    Busca gráfico de consumo en fotos (requiere análisis de imágenes)
    """
    features = {}
    evidencias = {}
    
    # Buscar fotos que puedan contener gráficos
    for doc in documentos:
        if doc.get("type") == "EVIDENCIA_FOTOGRAFICA":
            metadata = doc.get("metadata", {})
            tags = metadata.get("tags", [])
            original_name = doc.get("original_name", "").lower()
            
            # Buscar indicadores de gráfico en nombre o tags
            if any(keyword in original_name for keyword in ["grafico", "consumo", "historial"]):
                features["tiene_grafico_consumo"] = True
                features["grafico_fuente"] = doc.get("original_name", "")
                features["historial_fuente"] = "grafico_foto"
                
                evidencias["tiene_grafico_consumo"] = [{
                    "tipo": "foto",
                    "archivo": doc.get("original_name", ""),
                    "etiqueta": "grafico_consumo"
                }]
                
                return features, evidencias
    
    return None, {}


def _buscar_grafico_en_boleta(
    documentos: List[Dict[str, Any]],
    expediente: Dict[str, Any]
) -> Tuple[Optional[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
    """
    Intenta extraer gráfico desde boleta (requiere OCR o webscraping)
    Esta función activaría el módulo de boleta/webscraping si está disponible
    """
    features = {}
    evidencias = {}
    
    # Buscar boletas en documentos
    boletas = [
        doc for doc in documentos
        if "boleta" in doc.get("original_name", "").lower()
        or doc.get("type") == "TABLA_CALCULO"
    ]
    
    if not boletas:
        return None, {}
    
    # Por ahora, solo marcar que se intentó desde boleta
    # En el futuro, aquí se activaría el módulo de boleta/webscraping
    logger.info("Intentando extraer gráfico desde boleta (módulo no implementado aún)")
    
    # Placeholder: asumir que no se encontró si llegamos aquí
    # En implementación futura, se llamaría a un módulo de boleta
    # boleta_module = BoletaExtractor()
    # grafico_data = boleta_module.extract_consumption_graph(boleta_path)
    
    return None, {}


def _tiene_referencia_grafico(
    extracted_data: Dict[str, Any],
    metadata: Dict[str, Any]
) -> bool:
    """
    Verifica si un documento tiene referencia a gráfico de consumo
    """
    # Buscar en extracted_data
    if isinstance(extracted_data, dict):
        texto = str(extracted_data).lower()
        keywords = ["grafico", "gráfico", "consumo", "historial", "chart", "graph"]
        if any(keyword in texto for keyword in keywords):
            return True
    
    # Buscar en metadata
    if isinstance(metadata, dict):
        texto = str(metadata).lower()
        keywords = ["grafico", "gráfico", "consumo", "historial"]
        if any(keyword in texto for keyword in keywords):
            return True
    
    return False


def seleccionar_mejor_fuente_monto(
    documentos: List[Dict[str, Any]]
) -> Tuple[Optional[float], Dict[str, Any]]:
    """
    Selecciona la mejor fuente para el monto CNR
    Prioridad: TABLA_CALCULO > CARTA_RESPUESTA > otros
    """
    # Buscar en TABLA_CALCULO primero
    for doc in documentos:
        if doc.get("type") == "TABLA_CALCULO":
            extracted_data = doc.get("extracted_data", {})
            monto = extracted_data.get("total_amount")
            if monto:
                return monto, {
                    "tipo": "texto",
                    "documento": doc.get("original_name", ""),
                    "pagina": 0,
                    "snippet": f"Total: ${monto}"
                }
    
    # Buscar en CARTA_RESPUESTA
    for doc in documentos:
        if doc.get("type") == "CARTA_RESPUESTA":
            extracted_data = doc.get("extracted_data", {})
            monto = extracted_data.get("monto_cnr") or extracted_data.get("total_amount")
            if monto:
                return monto, {
                    "tipo": "texto",
                    "documento": doc.get("original_name", ""),
                    "pagina": 0,
                    "snippet": f"Monto CNR: ${monto}"
                }
    
    return None, {}


def seleccionar_mejor_fuente_periodo(
    documentos: List[Dict[str, Any]]
) -> Tuple[Optional[int], Dict[str, Any]]:
    """
    Selecciona la mejor fuente para el período en meses
    Prioridad: TABLA_CALCULO > ORDEN_TRABAJO > otros
    """
    # Buscar en TABLA_CALCULO primero
    for doc in documentos:
        if doc.get("type") == "TABLA_CALCULO":
            extracted_data = doc.get("extracted_data", {})
            periodo = extracted_data.get("period_months") or extracted_data.get("periodo_meses")
            if periodo:
                return periodo, {
                    "tipo": "texto",
                    "documento": doc.get("original_name", ""),
                    "pagina": 0,
                    "snippet": f"Periodo: {periodo} meses"
                }
    
    # Buscar en ORDEN_TRABAJO
    for doc in documentos:
        if doc.get("type") == "ORDEN_TRABAJO":
            extracted_data = doc.get("extracted_data", {})
            periodo = extracted_data.get("period_months")
            if periodo:
                return periodo, {
                    "tipo": "texto",
                    "documento": doc.get("original_name", ""),
                    "pagina": 0,
                    "snippet": f"Periodo: {periodo} meses"
                }
    
    return None, {}

