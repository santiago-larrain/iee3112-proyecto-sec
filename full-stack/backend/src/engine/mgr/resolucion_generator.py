"""
Generador de Resoluciones usando templates Markdown
Motor de Generación de Resoluciones (MGR)
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import re
from src.config import RESOLUCION_TEMPLATES_DIR


class ResolucionGenerator:
    """
    Genera resoluciones legales utilizando un sistema de plantillas Markdown.
    Combina una plantilla "master" con "snippets" de argumentos legales
    basados en las irregularidades detectadas en el checklist.
    """
    def __init__(self, templates_dir: Path = None):
        """
        Inicializa el generador de resoluciones.

        Args:
            templates_dir (Path, optional): Directorio de plantillas de resolución.
                                            Si es None, usa la ruta del config.
        """
        if templates_dir is None:
            self.templates_dir = RESOLUCION_TEMPLATES_DIR
        else:
            self.templates_dir = templates_dir
        
        self.snippets_dir = self.templates_dir / "snippets"

    def load_template(self, template_name: str) -> str:
        """
        Carga una plantilla master de resolución desde el disco.

        Args:
            template_name (str): Nombre de la plantilla (ej: "master_instruccion").

        Returns:
            str: Contenido de la plantilla.
        
        Raises:
            FileNotFoundError: Si la plantilla no se encuentra.
        """
        template_path = self.templates_dir / f"{template_name}.md"
        if not template_path.exists():
            raise FileNotFoundError(f"Template no encontrado: {template_path}")
        
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()
        
        return template

    def generate_resolucion(self, 
                          case_id: str,
                          client_name: str,
                          rut_client: str,
                          empresa: str,
                          materia: str,
                          checklist: Dict[str, Any],
                          template_type: str = "INSTRUCCION",
                          contenido_personalizado: Optional[str] = None) -> str:
        """
        Genera una resolución completa basada en el template y el estado del checklist
        
        Args:
            case_id: ID del caso
            client_name: Nombre del cliente
            rut_client: RUT del cliente
            empresa: Nombre de la empresa
            materia: Materia del caso
            checklist: Checklist con items evaluados
            template_type: Tipo de template ("INSTRUCCION" o "IMPROCEDENTE")
            contenido_personalizado: Contenido adicional opcional
            
        Returns:
            Texto completo de la resolución
        """
        # Cargar template master
        if template_type == "INSTRUCCION":
            template_path = self.templates_dir / "master_instruccion.md"
        else:
            template_path = self.templates_dir / "master_improcedente.md"
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template no encontrado: {template_path}")
        
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()
        
        # Generar irregularidades si es INSTRUCCION
        irregularidades = ""
        if template_type == "INSTRUCCION":
            irregularidades = self._generate_irregularidades(checklist)
        
        # Reemplazar variables en el template
        resolucion = template.replace("{{case_id}}", case_id)
        resolucion = resolucion.replace("{{client_name}}", client_name or "N/A")
        resolucion = resolucion.replace("{{rut_client}}", rut_client or "N/A")
        resolucion = resolucion.replace("{{empresa}}", empresa or "N/A")
        resolucion = resolucion.replace("{{materia}}", materia or "N/A")
        resolucion = resolucion.replace("{{irregularidades}}", irregularidades)
        
        # Agregar contenido personalizado si existe
        if contenido_personalizado and contenido_personalizado.strip():
            # Solo agregar si no es un borrador previo
            if not contenido_personalizado.strip().startswith(('INSTRUCCIÓN', 'RESOLUCIÓN')):
                resolucion = resolucion.replace("{{contenido_personalizado}}", f"\n\n{contenido_personalizado}")
            else:
                resolucion = resolucion.replace("{{contenido_personalizado}}", "")
        else:
            resolucion = resolucion.replace("{{contenido_personalizado}}", "")
        
        return resolucion.strip()
    
    def _generate_irregularidades(self, checklist: Dict[str, Any]) -> str:
        """
        Genera la lista de irregularidades basada en items fallidos del checklist
        
        Args:
            checklist: Checklist con items evaluados
            
        Returns:
            Texto con lista de irregularidades
        """
        irregularidades = []
        
        # Buscar en todas las categorías del checklist
        categories = ["group_a_admisibilidad", "group_b_instruccion", "group_c_analisis"]
        
        for category in categories:
            items = checklist.get(category, [])
            if isinstance(items, list):
                for item in items:
                    # Verificar si el item está fallido y validado
                    status = item.get("status")
                    validated = item.get("validated", False)
                    
                    # NO_CUMPLE puede ser string o enum value
                    if (status == "NO_CUMPLE" or 
                        (hasattr(status, 'value') and status.value == "NO_CUMPLE")) and validated:
                        title = item.get("title", "Requisito no cumplido")
                        description = item.get("description", "No se cumplió con el requisito establecido.")
                        
                        # Intentar cargar snippet específico si existe
                        snippet = self._load_snippet_for_item(item)
                        if snippet:
                            irregularidades.append(f"- {title}: {snippet}")
                        else:
                            irregularidades.append(f"- {title}: {description}")
        
        if irregularidades:
            return "\n".join(irregularidades) + "\n"
        else:
            return "- Se requiere revisión adicional de la documentación presentada.\n"
    
    def _load_snippet_for_item(self, item: Dict[str, Any]) -> Optional[str]:
        """
        Intenta cargar un snippet específico para un item del checklist
        
        Args:
            item: Item del checklist
            
        Returns:
            Contenido del snippet o None si no existe
        """
        # Mapeo de reglas a snippets
        rule_to_snippet = {
            "RULE_CHECK_PHOTOS_EXISTENCE": "arg_falta_fotos.md",
            "RULE_CHECK_CALCULATION_TABLE": "arg_calculo_erroneo.md",
            "RULE_CHECK_OT_EXISTS": "arg_falta_ot.md",
            "RULE_CHECK_RETROACTIVE_PERIOD": "arg_periodo_excesivo.md",
            "RULE_CHECK_CIM_VALIDATION": "arg_cim_invalido.md"
        }
        
        rule_ref = item.get("rule_ref")
        if rule_ref and rule_ref in rule_to_snippet:
            snippet_path = self.snippets_dir / rule_to_snippet[rule_ref]
            if snippet_path.exists():
                try:
                    with open(snippet_path, "r", encoding="utf-8") as f:
                        return f.read().strip()
                except Exception:
                    pass
        
        return None

