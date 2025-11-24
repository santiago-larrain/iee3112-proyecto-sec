"""
Motor de Inferencia Normativa (MIN)
Carga JSONs de checklist y ejecuta reglas Python asociadas
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from models import Checklist, ChecklistItem, ChecklistStatus

from .rules import get_rule


class RuleEngine:
    """Motor que ejecuta reglas de validación basadas en JSONs configurables"""
    
    def __init__(self, checklist_dir: Optional[Path] = None):
        """
        Inicializa el motor
        
        Args:
            checklist_dir: Directorio donde están los JSONs de checklist
        """
        if checklist_dir is None:
            # Por defecto, buscar en backend/checklist_tipo/
            current_dir = Path(__file__).parent.parent.parent
            checklist_dir = current_dir / "checklist_tipo"
        
        self.checklist_dir = Path(checklist_dir)
    
    def load_checklist_config(self, tipo_caso: str) -> Optional[Dict[str, Any]]:
        """
        Carga el JSON de configuración de checklist para un tipo de caso
        
        Args:
            tipo_caso: Tipo de caso (CNR, CORTE_SUMINISTRO, etc.)
            
        Returns:
            Diccionario con la configuración del checklist o None si no existe
        """
        config_file = self.checklist_dir / f"{tipo_caso.lower()}.json"
        
        if not config_file.exists():
            # Fallback a template si no existe el específico
            config_file = self.checklist_dir / "template.json"
            if not config_file.exists():
                return None
        
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error cargando configuración de checklist {config_file}: {e}")
            return None
    
    def generate_checklist(self, edn: Dict[str, Any]) -> Checklist:
        """
        Genera un checklist completo basado en el EDN y el tipo de caso
        
        Args:
            edn: Expediente Digital Normalizado
            
        Returns:
            Checklist completo con items evaluados
        """
        # Obtener tipo de caso del EDN
        tipo_caso = edn.get("compilation_metadata", {}).get("tipo_caso")
        
        # Si no existe tipo_caso, inferirlo desde documentos y materia
        if not tipo_caso:
            tipo_caso = self._infer_tipo_caso(edn)
            # Guardar en el EDN para futuras referencias
            if "compilation_metadata" not in edn:
                edn["compilation_metadata"] = {}
            edn["compilation_metadata"]["tipo_caso"] = tipo_caso
        
        print(f"[MIN] Tipo de caso detectado/inferido: {tipo_caso}")
        
        # Cargar configuración
        config = self.load_checklist_config(tipo_caso)
        if not config:
            print(f"[MIN] No se encontró configuración para {tipo_caso}, intentando CNR por defecto")
            print(f"[MIN] Checklist dir: {self.checklist_dir}")
            print(f"[MIN] Archivos disponibles: {list(self.checklist_dir.glob('*.json'))}")
            # Fallback a CNR si no existe el específico
            tipo_caso = "CNR"
            config = self.load_checklist_config("CNR")
            if not config:
                print(f"[MIN] Error: No se pudo cargar configuración ni CNR")
                # Retornar checklist vacío si no hay configuración
                return Checklist(
                    group_a_admisibilidad=[],
                    group_b_instruccion=[],
                    group_c_analisis=[]
                )
        
        # Generar items para cada grupo
        checklist_items = {
            "group_a_admisibilidad": [],
            "group_b_instruccion": [],
            "group_c_analisis": []
        }
        
        groups_config = config.get("groups", {})
        
        print(f"[MIN] Config cargado: {len(groups_config)} grupos encontrados")
        
        # Procesar Grupo A
        group_a_config = groups_config.get("group_a_admisibilidad", {})
        items_a = group_a_config.get("items", [])
        print(f"[MIN] Grupo A: {len(items_a)} items en configuración")
        for item_config in items_a:
            item = self._evaluate_item(item_config, edn)
            if item:
                checklist_items["group_a_admisibilidad"].append(item)
        
        # Procesar Grupo B
        group_b_config = groups_config.get("group_b_instruccion", {})
        items_b = group_b_config.get("items", [])
        print(f"[MIN] Grupo B: {len(items_b)} items en configuración")
        for item_config in items_b:
            item = self._evaluate_item(item_config, edn)
            if item:
                checklist_items["group_b_instruccion"].append(item)
        
        # Procesar Grupo C
        group_c_config = groups_config.get("group_c_analisis", {})
        items_c = group_c_config.get("items", [])
        print(f"[MIN] Grupo C: {len(items_c)} items en configuración")
        for item_config in items_c:
            item = self._evaluate_item(item_config, edn)
            if item:
                checklist_items["group_c_analisis"].append(item)
        
        print(f"[MIN] Checklist generado: A={len(checklist_items['group_a_admisibilidad'])}, B={len(checklist_items['group_b_instruccion'])}, C={len(checklist_items['group_c_analisis'])}")
        
        return Checklist(**checklist_items)
    
    def _evaluate_item(self, item_config: Dict[str, Any], edn: Dict[str, Any]) -> Optional[ChecklistItem]:
        """
        Evalúa un item del checklist ejecutando su regla asociada
        
        Args:
            item_config: Configuración del item desde JSON
            edn: Expediente Digital Normalizado
            
        Returns:
            ChecklistItem evaluado o None si hay error
        """
        rule_ref = item_config.get("rule_ref")
        if not rule_ref:
            # Si no hay regla, crear item sin evaluación
            return ChecklistItem(
                id=item_config.get("id", ""),
                title=item_config.get("title", ""),
                status=ChecklistStatus.REVISION_MANUAL,
                evidence="No hay regla asociada",
                evidence_type=item_config.get("evidence_type", "dato"),
                description=item_config.get("description", ""),
                validated=False,
                rule_ref=rule_ref
            )
        
        # Obtener y ejecutar regla
        rule_func = get_rule(rule_ref)
        if not rule_func:
            # Si la regla no existe, crear item con error
            return ChecklistItem(
                id=item_config.get("id", ""),
                title=item_config.get("title", ""),
                status=ChecklistStatus.REVISION_MANUAL,
                evidence=f"Regla {rule_ref} no encontrada",
                evidence_type=item_config.get("evidence_type", "dato"),
                description=item_config.get("description", ""),
                validated=False,
                rule_ref=rule_ref
            )
        
        # Ejecutar regla
        try:
            result = rule_func(edn)
            
            # Construir ChecklistItem
            return ChecklistItem(
                id=item_config.get("id", ""),
                title=item_config.get("title", ""),
                status=ChecklistStatus(result.get("status", ChecklistStatus.REVISION_MANUAL.value)),
                evidence=result.get("evidence", ""),
                evidence_type=item_config.get("evidence_type", "dato"),
                description=item_config.get("description", ""),
                validated=False,
                rule_ref=rule_ref,
                evidence_data=result.get("evidence_data")  # Datos con deep linking
            )
        except Exception as e:
            print(f"Error ejecutando regla {rule_ref}: {e}")
            import traceback
            traceback.print_exc()
            return ChecklistItem(
                id=item_config.get("id", ""),
                title=item_config.get("title", ""),
                status=ChecklistStatus.REVISION_MANUAL,
                evidence=f"Error ejecutando regla: {str(e)}",
                evidence_type=item_config.get("evidence_type", "dato"),
                description=item_config.get("description", ""),
                validated=False,
                rule_ref=rule_ref
            )
    
    def _infer_tipo_caso(self, edn: Dict[str, Any]) -> str:
        """
        Infiere el tipo de caso basado en documentos y materia si no está definido
        
        Args:
            edn: Expediente Digital Normalizado
            
        Returns:
            Tipo de caso inferido (CNR, CORTE_SUMINISTRO, etc.)
        """
        # Importar DocumentClassifier para usar su lógica
        import sys
        from pathlib import Path
        backend_dir = Path(__file__).parent.parent.parent.parent
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        
        try:
            from engine.omc.document_classifier import DocumentClassifier
            
            classifier = DocumentClassifier()
            document_inventory = edn.get("document_inventory", {})
            unified_context = edn.get("unified_context", {})
            
            # Usar el método del clasificador
            tipo_inferido = classifier.classify_tipo_caso(document_inventory, unified_context)
            print(f"[MIN] Tipo de caso inferido: {tipo_inferido}")
            return tipo_inferido
        except Exception as e:
            print(f"[MIN] Error inferiendo tipo_caso: {e}")
            import traceback
            traceback.print_exc()
            # Por defecto, asumir CNR
            return "CNR"

