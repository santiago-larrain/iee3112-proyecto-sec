"""
Generador de Checklist según las reglas de validación definidas
para casos CNR (Recuperación de Consumo)
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from models import ChecklistStatus, DocumentType


class ChecklistGenerator:
    """Genera checklist estructurado según reglas de negocio CNR"""
    
    def generate_checklist(self, edn: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera checklist completo basado en el EDN
        
        Args:
            edn: Expediente Digital Normalizado
            
        Returns:
            Checklist estructurado con grupos A, B, C
        """
        doc_inventory = edn.get("document_inventory", {})
        unified_context = edn.get("unified_context", {})
        compilation_metadata = edn.get("compilation_metadata", {})
        
        # Obtener documentos por tipo
        doc_types = self._get_document_types(doc_inventory)
        
        # Grupo A: Admisibilidad y Forma
        group_a = self._generate_group_a(edn, doc_inventory, compilation_metadata)
        
        # Grupo B: Instrucción (Integridad Probatoria)
        group_b = self._generate_group_b(doc_inventory, doc_types)
        
        # Grupo C: Análisis Técnico-Jurídico
        group_c = self._generate_group_c(doc_inventory, doc_types, unified_context)
        
        return {
            "group_a_admisibilidad": group_a,
            "group_b_instruccion": group_b,
            "group_c_analisis": group_c,
            "metadata": {
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "case_id": compilation_metadata.get("case_id", "UNKNOWN")
            }
        }
    
    def _get_document_types(self, doc_inventory: Dict) -> Dict[str, List[Dict]]:
        """Extrae documentos agrupados por tipo"""
        docs_by_type = {}
        
        for level in ["level_1_critical", "level_2_supporting"]:
            for doc in doc_inventory.get(level, []):
                doc_type = doc.get("type")
                if doc_type not in docs_by_type:
                    docs_by_type[doc_type] = []
                docs_by_type[doc_type].append(doc)
        
        return docs_by_type
    
    def _generate_group_a(self, edn: Dict, doc_inventory: Dict, 
                         compilation_metadata: Dict) -> List[Dict[str, Any]]:
        """Genera Grupo A: Admisibilidad y Forma"""
        items = []
        
        # A.1. Validación de Plazo de Respuesta
        items.append(self._check_plazo_respuesta(edn, compilation_metadata))
        
        # A.2. Trazabilidad del Reclamo Previo
        items.append(self._check_trazabilidad_reclamo(doc_inventory))
        
        # A.3. Competencia de la Materia
        items.append(self._check_competencia_materia(edn, doc_inventory))
        
        return items
    
    def _check_plazo_respuesta(self, edn: Dict, compilation_metadata: Dict) -> Dict[str, Any]:
        """A.1. Validación de Plazo de Respuesta"""
        # Buscar fecha de respuesta en CARTA_RESPUESTA
        fecha_respuesta = None
        fecha_reclamo = compilation_metadata.get("case_id", "")
        
        # Extraer fecha del case_id (formato: YYMMDD-XXXXXX)
        try:
            if len(fecha_reclamo) >= 6:
                year = '20' + fecha_reclamo[:2]
                month = fecha_reclamo[2:4]
                day = fecha_reclamo[4:6]
                fecha_reclamo_dt = datetime(int(year), int(month), int(day))
            else:
                fecha_reclamo_dt = None
        except:
            fecha_reclamo_dt = None
        
        # Buscar fecha en carta de respuesta
        doc_inventory = edn.get("document_inventory", {})
        for doc in doc_inventory.get("level_1_critical", []):
            if doc.get("type") == DocumentType.CARTA_RESPUESTA.value:
                extracted_data = doc.get("extracted_data", {})
                fecha_str = extracted_data.get("response_date")
                if fecha_str:
                    try:
                        fecha_respuesta = datetime.fromisoformat(fecha_str.replace('Z', '+00:00'))
                    except:
                        pass
        
        # Calcular diferencia
        if fecha_reclamo_dt and fecha_respuesta:
            diferencia = (fecha_respuesta - fecha_reclamo_dt).days
            if diferencia <= 30:
                status = ChecklistStatus.CUMPLE.value
                evidence = f"En Plazo ({diferencia} días)"
            else:
                status = ChecklistStatus.NO_CUMPLE.value
                evidence = f"Fuera de Plazo ({diferencia} días) - **Causal de Instrucción Inmediata**"
        else:
            status = ChecklistStatus.REVISION_MANUAL.value
            evidence = "No se pudo determinar el plazo (fechas no disponibles)"
        
        return {
            "id": "A.1",
            "title": "Validación de Plazo de Respuesta",
            "status": status,
            "evidence": evidence,
            "evidence_type": "dato",
            "description": "La empresa debe responder dentro de 30 días corridos desde la fecha del reclamo.",
            "validated": False
        }
    
    def _check_trazabilidad_reclamo(self, doc_inventory: Dict) -> Dict[str, Any]:
        """A.2. Trazabilidad del Reclamo Previo"""
        # Buscar ID de reclamo en cartas de respuesta
        id_reclamo = None
        
        for doc in doc_inventory.get("level_1_critical", []):
            if doc.get("type") == DocumentType.CARTA_RESPUESTA.value:
                extracted_data = doc.get("extracted_data", {})
                id_reclamo = extracted_data.get("cnr_reference") or extracted_data.get("resolution_number")
                if not id_reclamo:
                    # Buscar en nombre de archivo
                    original_name = doc.get("original_name", "")
                    import re
                    match = re.search(r'(\d{6,10})', original_name)
                    if match:
                        id_reclamo = match.group(1)
        
        if id_reclamo:
            status = ChecklistStatus.CUMPLE.value
            evidence = f"Vinculación Correcta (Ticket #{id_reclamo})"
        else:
            status = ChecklistStatus.REVISION_MANUAL.value
            evidence = "No se detecta referencia a reclamo previo"
        
        return {
            "id": "A.2",
            "title": "Trazabilidad del Reclamo Previo",
            "status": status,
            "evidence": evidence,
            "evidence_type": "dato",
            "description": "Debe existir un ID de reclamo interno citado en la Carta de Respuesta.",
            "validated": False
        }
    
    def _check_competencia_materia(self, edn: Dict, doc_inventory: Dict) -> Dict[str, Any]:
        """A.3. Competencia de la Materia"""
        materia = edn.get("materia", "").upper()
        has_ot = any(
            doc.get("type") == DocumentType.ORDEN_TRABAJO.value
            for doc in doc_inventory.get("level_1_critical", [])
        )
        
        # Verificar coherencia: si materia es CNR, debe haber OT
        if "CNR" in materia or "RECUPERACION" in materia:
            if has_ot:
                status = ChecklistStatus.CUMPLE.value
                evidence = f"Coherencia Documental (Mat: {materia})"
            else:
                status = ChecklistStatus.NO_CUMPLE.value
                evidence = f"Incoherencia: Materia '{materia}' pero no hay Orden de Trabajo"
        else:
            status = ChecklistStatus.REVISION_MANUAL.value
            evidence = f"Materia: {materia}"
        
        return {
            "id": "A.3",
            "title": "Competencia de la Materia",
            "status": status,
            "evidence": evidence,
            "evidence_type": "dato",
            "description": "La materia clasificada debe coincidir con los documentos adjuntos.",
            "validated": False
        }
    
    def _generate_group_b(self, doc_inventory: Dict, doc_types: Dict) -> List[Dict[str, Any]]:
        """Genera Grupo B: Instrucción (Integridad Probatoria)"""
        items = []
        
        # B.1. Existencia de Orden de Trabajo
        items.append(self._check_orden_trabajo(doc_types))
        
        # B.2. Existencia de Evidencia Fotográfica
        items.append(self._check_evidencia_fotografica(doc_types))
        
        # B.3. Existencia de Memoria de Cálculo
        items.append(self._check_memoria_calculo(doc_types))
        
        # B.4. Acreditación de Notificación
        items.append(self._check_notificacion(doc_inventory))
        
        return items
    
    def _check_orden_trabajo(self, doc_types: Dict) -> Dict[str, Any]:
        """B.1. Existencia de Orden de Trabajo"""
        ot_docs = doc_types.get(DocumentType.ORDEN_TRABAJO.value, [])
        
        if ot_docs:
            # Extraer número de OT si está disponible
            ot_number = None
            for doc in ot_docs:
                extracted_data = doc.get("extracted_data", {})
                ot_number = extracted_data.get("ot_number")
                if ot_number:
                    break
            
            if ot_number:
                evidence = f"OT Adjunta (Folio {ot_number})"
            else:
                evidence = "OT Adjunta"
            
            status = ChecklistStatus.CUMPLE.value
        else:
            status = ChecklistStatus.NO_CUMPLE.value
            evidence = "Falta OT - **Imposible acreditar hecho**"
        
        return {
            "id": "B.1",
            "title": "Existencia de Orden de Trabajo (OT)",
            "status": status,
            "evidence": evidence,
            "evidence_type": "archivo",
            "description": "Debe existir una Orden de Trabajo que acredite la visita técnica.",
            "validated": False
        }
    
    def _check_evidencia_fotografica(self, doc_types: Dict) -> Dict[str, Any]:
        """B.2. Existencia de Evidencia Fotográfica"""
        foto_docs = doc_types.get(DocumentType.EVIDENCIA_FOTOGRAFICA.value, [])
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
        else:
            status = ChecklistStatus.NO_CUMPLE.value
            evidence = "Sin evidencia visual"
        
        return {
            "id": "B.2",
            "title": "Existencia de Evidencia Fotográfica",
            "status": status,
            "evidence": evidence,
            "evidence_type": "archivo",
            "description": "Debe existir al menos una fotografía que corrobore los hallazgos técnicos.",
            "validated": False
        }
    
    def _check_memoria_calculo(self, doc_types: Dict) -> Dict[str, Any]:
        """B.3. Existencia de Memoria de Cálculo"""
        calculo_docs = doc_types.get(DocumentType.TABLA_CALCULO.value, [])
        
        if calculo_docs:
            status = ChecklistStatus.CUMPLE.value
            evidence = "Tabla Detallada Disponible"
        else:
            status = ChecklistStatus.NO_CUMPLE.value
            evidence = "Falta desglose de deuda"
        
        return {
            "id": "B.3",
            "title": "Existencia de Memoria de Cálculo",
            "status": status,
            "evidence": evidence,
            "evidence_type": "archivo",
            "description": "Debe existir una tabla de cálculo que detalle el monto a cobrar.",
            "validated": False
        }
    
    def _check_notificacion(self, doc_inventory: Dict) -> Dict[str, Any]:
        """B.4. Acreditación de Notificación"""
        # Buscar palabras clave en todos los documentos
        keywords = ["carta certificada", "notificación personal", "firma", "notificado"]
        found_keywords = []
        
        for level in ["level_1_critical", "level_2_supporting"]:
            for doc in doc_inventory.get(level, []):
                original_name = doc.get("original_name", "").lower()
                # También buscar en extracted_data si hay texto
                extracted_data = doc.get("extracted_data", {})
                text_content = str(extracted_data).lower()
                
                for keyword in keywords:
                    if keyword in original_name or keyword in text_content:
                        if keyword not in found_keywords:
                            found_keywords.append(keyword)
        
        if found_keywords:
            status = ChecklistStatus.CUMPLE.value
            keyword_display = found_keywords[0].title()
            evidence = f"Cliente Notificado (Ref: {keyword_display})"
        else:
            status = ChecklistStatus.REVISION_MANUAL.value
            evidence = "No se acredita entrega de notificación de cobro"
        
        return {
            "id": "B.4",
            "title": "Acreditación de Notificación",
            "status": status,
            "evidence": evidence,
            "evidence_type": "dato",
            "description": "Debe acreditarse que el cliente fue notificado del cobro.",
            "validated": False
        }
    
    def _generate_group_c(self, doc_inventory: Dict, doc_types: Dict, 
                         unified_context: Dict) -> Dict[str, Any]:
        """Genera Grupo C: Análisis Técnico-Jurídico"""
        return {
            "c1_acreditacion_hecho": self._generate_c1(doc_inventory, doc_types),
            "c2_legalidad_cobro": self._generate_c2(doc_inventory, doc_types, unified_context)
        }
    
    def _generate_c1(self, doc_inventory: Dict, doc_types: Dict) -> List[Dict[str, Any]]:
        """C.1. Acreditación del Hecho (El Fraude)"""
        items = []
        
        # C.1.1. Consistencia del Hallazgo
        items.append(self._check_consistencia_hallazgo(doc_inventory, doc_types))
        
        # C.1.2. Prueba de Exactitud
        items.append(self._check_prueba_exactitud(doc_types))
        
        return items
    
    def _check_consistencia_hallazgo(self, doc_inventory: Dict, doc_types: Dict) -> Dict[str, Any]:
        """C.1.1. Consistencia del Hallazgo"""
        ot_docs = doc_types.get(DocumentType.ORDEN_TRABAJO.value, [])
        foto_docs = doc_types.get(DocumentType.EVIDENCIA_FOTOGRAFICA.value, [])
        
        if not ot_docs or not foto_docs:
            status = ChecklistStatus.REVISION_MANUAL.value
            evidence = "No se puede verificar (falta OT o fotos)"
        else:
            # Extraer hallazgo de OT
            ot_finding = None
            for doc in ot_docs:
                extracted_data = doc.get("extracted_data", {})
                ot_finding = extracted_data.get("findings") or extracted_data.get("equipment_status")
                if ot_finding:
                    break
            
            # Extraer tags de fotos
            foto_tags = []
            for doc in foto_docs:
                extracted_data = doc.get("extracted_data", {})
                tags = extracted_data.get("tags", [])
                if isinstance(tags, list):
                    foto_tags.extend(tags)
            
            # Verificar consistencia básica
            if ot_finding and foto_tags:
                # Normalizar términos
                ot_lower = str(ot_finding).lower()
                tags_lower = [str(t).lower() for t in foto_tags]
                
                # Buscar coincidencias
                consistent = False
                if "sello" in ot_lower and any("sello" in t or "seal" in t for t in tags_lower):
                    consistent = True
                elif "intervencion" in ot_lower or "adulterado" in ot_lower:
                    if any("broken" in t or "adulterado" in t for t in tags_lower):
                        consistent = True
                
                if consistent:
                    status = ChecklistStatus.CUMPLE.value
                    evidence = f"Hallazgo Coherente: {ot_finding}"
                else:
                    status = ChecklistStatus.NO_CUMPLE.value
                    evidence = f"Contradicción: OT dice '{ot_finding}' pero fotos muestran medidor normal"
            else:
                status = ChecklistStatus.REVISION_MANUAL.value
                evidence = "Información insuficiente para verificar consistencia"
        
        return {
            "id": "C.1.1",
            "title": "Consistencia del Hallazgo",
            "status": status,
            "evidence": evidence,
            "evidence_type": "dato",
            "description": "La descripción en la OT debe coincidir con las etiquetas de las fotos.",
            "validated": False
        }
    
    def _check_prueba_exactitud(self, doc_types: Dict) -> Dict[str, Any]:
        """C.1.2. Prueba de Exactitud (Laboratorio)"""
        ot_docs = doc_types.get(DocumentType.ORDEN_TRABAJO.value, [])
        
        has_proof = False
        proof_details = None
        
        for doc in ot_docs:
            extracted_data = doc.get("extracted_data", {})
            recommendations = extracted_data.get("recommendations", "")
            findings = extracted_data.get("findings", "")
            
            # Buscar referencias a pruebas
            text_to_search = f"{recommendations} {findings}".lower()
            if "error" in text_to_search or "calibracion" in text_to_search or "prueba" in text_to_search:
                has_proof = True
                # Intentar extraer porcentaje de error
                import re
                error_match = re.search(r'error[:\s]+([-]?\d+)%', text_to_search)
                if error_match:
                    proof_details = f"Error {error_match.group(1)}%"
                break
        
        if has_proof:
            status = ChecklistStatus.CUMPLE.value
            evidence = f"Prueba In-Situ: {proof_details or 'Error detectado'}"
        else:
            status = ChecklistStatus.REVISION_MANUAL.value
            evidence = "No se adjunta prueba de error de medida"
        
        return {
            "id": "C.1.2",
            "title": "Prueba de Exactitud (Laboratorio)",
            "status": status,
            "evidence": evidence,
            "evidence_type": "dato",
            "description": "Si se cambió el medidor, debe existir Certificado de Calibración o prueba in-situ.",
            "validated": False
        }
    
    def _generate_c2(self, doc_inventory: Dict, doc_types: Dict, 
                    unified_context: Dict) -> List[Dict[str, Any]]:
        """C.2. Legalidad del Cobro (Las Matemáticas)"""
        items = []
        
        # C.2.1. Validación del CIM
        items.append(self._check_validacion_cim(doc_types, unified_context))
        
        # C.2.2. Periodo Retroactivo
        items.append(self._check_periodo_retroactivo(doc_types))
        
        # C.2.3. Corrección Monetaria
        items.append(self._check_correccion_monetaria(doc_types))
        
        return items
    
    def _check_validacion_cim(self, doc_types: Dict, unified_context: Dict) -> Dict[str, Any]:
        """C.2.1. Validación del CIM"""
        calculo_docs = doc_types.get(DocumentType.TABLA_CALCULO.value, [])
        
        if not calculo_docs:
            status = ChecklistStatus.REVISION_MANUAL.value
            evidence = "No se puede verificar (falta tabla de cálculo)"
        else:
            # Extraer CIM de tabla de cálculo
            cim_aplicado = None
            for doc in calculo_docs:
                extracted_data = doc.get("extracted_data", {})
                cim_aplicado = extracted_data.get("cim_kwh")
                if cim_aplicado:
                    break
            
            if cim_aplicado:
                # TODO: Obtener promedio histórico de BD (por ahora usar valor por defecto)
                promedio_historico = 600  # Esto debería venir de la BD de suministros
                
                # Calcular porcentaje
                porcentaje = (cim_aplicado / promedio_historico) * 100 if promedio_historico > 0 else 0
                
                if porcentaje <= 150:
                    status = ChecklistStatus.CUMPLE.value
                    evidence = f"CIM Razonable ({cim_aplicado} kWh vs Histórico {promedio_historico} kWh)"
                else:
                    status = ChecklistStatus.NO_CUMPLE.value
                    evidence = f"CIM Desproporcionado ({cim_aplicado} kWh vs Histórico {promedio_historico} kWh)"
            else:
                status = ChecklistStatus.REVISION_MANUAL.value
                evidence = "No se pudo extraer CIM de la tabla de cálculo"
        
        return {
            "id": "C.2.1",
            "title": "Validación del CIM (Consumo Índice Mensual)",
            "status": status,
            "evidence": evidence,
            "evidence_type": "dato",
            "description": "El CIM aplicado debe ser razonable comparado con el promedio histórico del cliente.",
            "validated": False
        }
    
    def _check_periodo_retroactivo(self, doc_types: Dict) -> Dict[str, Any]:
        """C.2.2. Periodo Retroactivo"""
        calculo_docs = doc_types.get(DocumentType.TABLA_CALCULO.value, [])
        
        if not calculo_docs:
            status = ChecklistStatus.REVISION_MANUAL.value
            evidence = "No se puede verificar (falta tabla de cálculo)"
        else:
            # Extraer fechas de periodo
            periodo_inicio = None
            periodo_fin = None
            
            for doc in calculo_docs:
                extracted_data = doc.get("extracted_data", {})
                periodo_inicio = extracted_data.get("period_start")
                periodo_fin = extracted_data.get("period_end")
                if periodo_inicio and periodo_fin:
                    break
            
            if periodo_inicio and periodo_fin:
                try:
                    inicio_dt = datetime.fromisoformat(periodo_inicio.replace('Z', '+00:00'))
                    fin_dt = datetime.fromisoformat(periodo_fin.replace('Z', '+00:00'))
                    meses = (fin_dt.year - inicio_dt.year) * 12 + (fin_dt.month - inicio_dt.month)
                    
                    if meses <= 12:
                        status = ChecklistStatus.CUMPLE.value
                        evidence = f"Periodo Normativo ({meses} meses)"
                    else:
                        status = ChecklistStatus.NO_CUMPLE.value
                        evidence = f"Cobro Excesivo ({meses} meses retroactivos)"
                except:
                    status = ChecklistStatus.REVISION_MANUAL.value
                    evidence = "No se pudo calcular el periodo"
            else:
                status = ChecklistStatus.REVISION_MANUAL.value
                evidence = "No se encontraron fechas de periodo en la tabla de cálculo"
        
        return {
            "id": "C.2.2",
            "title": "Periodo Retroactivo",
            "status": status,
            "evidence": evidence,
            "evidence_type": "dato",
            "description": "El periodo de cobro retroactivo no debe exceder 12 meses.",
            "validated": False
        }
    
    def _check_correccion_monetaria(self, doc_types: Dict) -> Dict[str, Any]:
        """C.2.3. Corrección Monetaria"""
        calculo_docs = doc_types.get(DocumentType.TABLA_CALCULO.value, [])
        
        if not calculo_docs:
            status = ChecklistStatus.REVISION_MANUAL.value
            evidence = "No se puede verificar (falta tabla de cálculo)"
        else:
            # Por ahora, marcamos como revisión manual
            # TODO: Implementar verificación de tarifa vigente contra base de datos de tarifas
            status = ChecklistStatus.REVISION_MANUAL.value
            evidence = "Verificación de tarifa requiere consulta a base de datos de tarifas vigentes"
        
        return {
            "id": "C.2.3",
            "title": "Corrección Monetaria",
            "status": status,
            "evidence": evidence,
            "evidence_type": "dato",
            "description": "El valor del kWh usado debe corresponder a la tarifa vigente en la fecha del cobro.",
            "validated": False
        }

