"""
Procesador principal de documentos - Orquesta el pipeline completo
"""

import uuid
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from .pdf_extractor import PDFExtractor
from .docx_extractor import DOCXExtractor
from .document_classifier import DocumentClassifier
from .entity_extractor import EntityExtractor
from .document_categorizer import add_functional_categories
from .fact_extractor import construir_features
from .strategy_selector import extraer_desde_fuentes

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Procesa lotes de archivos y genera Expediente Digital Normalizado (EDN)"""
    
    def __init__(self):
        self.pdf_extractor = PDFExtractor()
        self.docx_extractor = DOCXExtractor()
        self.classifier = DocumentClassifier()
        self.entity_extractor = EntityExtractor()
    
    def process_case(self, case_id: str, case_folder: Path) -> Dict[str, Any]:
        """
        Procesa un caso completo desde una carpeta
        
        Args:
            case_id: ID del caso (ej: "231220-000557")
            case_folder: Carpeta que contiene los archivos del caso
            
        Returns:
            Expediente Digital Normalizado (EDN) como diccionario
        """
        logger.info(f"Procesando caso {case_id}")
        
        # Inicializar estructuras
        unified_context = {
            'rut_client': None,
            'client_name': None,
            'service_nis': None,
            'address_standard': None,
            'commune': None,
            'email': None,
            'phone': None
        }
        
        document_inventory = {
            'level_1_critical': [],
            'level_2_supporting': [],
            'level_0_missing': []
        }
        
        all_entities = {
            'ruts': set(),
            'nis': set(),
            'addresses': [],
            'communes': set(),
            'amounts': []
        }
        
        # Procesar todos los archivos
        files = list(case_folder.rglob('*'))
        files = [f for f in files if f.is_file() and not f.name.startswith('.')]
        
        for file_path in files:
            try:
                result = self.process_file(file_path, case_folder)
                if result:
                    # Agregar a inventario
                    level = result['level']
                    doc_entry = {
                        'type': result['type'],
                        'file_id': result['file_id'],
                        'original_name': result['original_name'],
                        'standardized_name': result.get('standardized_name'),
                        'extracted_data': result.get('extracted_data'),
                        'metadata': result.get('metadata')
                    }
                    
                    if level == 'level_1_critical':
                        document_inventory['level_1_critical'].append(doc_entry)
                    else:
                        document_inventory['level_2_supporting'].append(doc_entry)
                    
                    # Acumular entidades
                    entities = result.get('entities', {})
                    if entities.get('rut'):
                        all_entities['ruts'].add(entities['rut'])
                    if entities.get('nis'):
                        all_entities['nis'].add(entities['nis'])
                    if entities.get('address'):
                        all_entities['addresses'].append(entities['address'])
                    if entities.get('commune'):
                        all_entities['communes'].add(entities['commune'])
                    # Manejar amounts que pueden ser lista simple o lista con source
                    amounts = entities.get('amounts', [])
                    if amounts:
                        if isinstance(amounts[0], dict) and 'value' in amounts[0]:
                            # Formato con source
                            all_entities['amounts'].extend([a['value'] for a in amounts])
                        else:
                            # Formato simple
                            all_entities['amounts'].extend(amounts)
                    
            except Exception as e:
                logger.error(f"Error procesando archivo {file_path}: {e}")
                # Marcar como faltante si es crítico
                continue
        
        # Consolidar contexto unificado
        if all_entities['ruts']:
            unified_context['rut_client'] = list(all_entities['ruts'])[0]
        if all_entities['nis']:
            unified_context['service_nis'] = list(all_entities['nis'])[0]
        if all_entities['addresses']:
            unified_context['address_standard'] = all_entities['addresses'][0]
        if all_entities['communes']:
            unified_context['commune'] = list(all_entities['communes'])[0]
        
        # Determinar monto en disputa (el mayor encontrado)
        if all_entities['amounts']:
            max_amount = max(all_entities['amounts'])
        else:
            max_amount = None
        
        # Verificar documentos faltantes críticos
        doc_types = {doc['type'] for doc in document_inventory['level_1_critical'] + document_inventory['level_2_supporting']}
        required_types = ['CARTA_RESPUESTA', 'TABLA_CALCULO', 'ORDEN_TRABAJO']
        for req_type in required_types:
            if req_type not in doc_types:
                document_inventory['level_0_missing'].append({
                    'required_type': req_type,
                    'alert_level': 'HIGH' if req_type in ['CARTA_RESPUESTA', 'TABLA_CALCULO'] else 'MEDIUM',
                    'description': f'No se detectó documento de tipo {req_type}'
                })
        
        # Determinar tipo de caso
        tipo_caso = self.classifier.classify_tipo_caso(document_inventory, unified_context)
        
        # Agregar categorías funcionales al inventario
        document_inventory = add_functional_categories(document_inventory)
        
        # Construir EDN base
        edn = {
            'compilation_metadata': {
                'case_id': case_id,
                'processing_timestamp': datetime.utcnow().isoformat() + 'Z',
                'status': 'COMPLETED',
                'tipo_caso': tipo_caso
            },
            'unified_context': unified_context,
            'document_inventory': document_inventory,
            'materia': None,  # Se puede extraer de metadatos
            'monto_disputa': max_amount,
            'empresa': None,  # Se puede extraer de metadatos
            'fecha_ingreso': None  # Se puede extraer de metadatos
        }
        
        # Fase de Extracción de Features (Fact-Centric)
        # Consolidar texto de todos los documentos
        texto_normalizado = self._consolidar_texto_documentos(document_inventory, case_folder)
        
        # Separar boletas y fotos
        boletas = [
            doc for doc in document_inventory.get('level_1_critical', [])
            if 'boleta' in doc.get('original_name', '').lower()
        ]
        fotos = [
            doc for doc in document_inventory.get('level_2_supporting', [])
            if doc.get('type') == 'EVIDENCIA_FOTOGRAFICA'
        ]
        
        # Construir features consolidados
        try:
            consolidated_facts, evidence_map = construir_features(
                expediente=edn,
                texto_normalizado=texto_normalizado,
                boletas=boletas,
                fotos=fotos
            )
            
            # Aplicar estrategia de selección de fuentes (para gráfico, etc.)
            features_fuentes, evidencias_fuentes = extraer_desde_fuentes(
                documentos_procesados=document_inventory.get('level_1_critical', []) + 
                                     document_inventory.get('level_2_supporting', []),
                expediente=edn
            )
            
            # Consolidar features (prioridad: fact_extractor > strategy_selector)
            if features_fuentes:
                for key, value in features_fuentes.items():
                    if key not in consolidated_facts:
                        consolidated_facts[key] = value
            
            # Consolidar evidencias
            if evidencias_fuentes:
                for key, value in evidencias_fuentes.items():
                    if key not in evidence_map:
                        evidence_map[key] = value
            
            # Agregar al EDN
            edn['consolidated_facts'] = consolidated_facts
            edn['evidence_map'] = evidence_map
            
        except Exception as e:
            logger.error(f"Error en extracción de features: {e}")
            # Continuar sin features si hay error
            edn['consolidated_facts'] = {}
            edn['evidence_map'] = {}
        
        return edn
    
    def process_file(self, file_path: Path, base_path: Path) -> Optional[Dict[str, Any]]:
        """
        Procesa un archivo individual
        
        Args:
            file_path: Ruta al archivo
            base_path: Ruta base del caso (para rutas relativas)
            
        Returns:
            Diccionario con información del documento procesado
        """
        file_ext = file_path.suffix.lower()
        
        # Extraer texto según tipo
        content = None
        metadata = {}
        positions_data = None
        
        if file_ext == '.pdf':
            # Extraer con posiciones para documentos críticos
            content = self.pdf_extractor.extract_text(file_path, include_positions=False)
            # Para documentos críticos, también extraer posiciones
            # Primero clasificar para saber si es crítico
            doc_type_preview = self.classifier.classify(file_path, content)
            if doc_type_preview in ['CARTA_RESPUESTA', 'TABLA_CALCULO', 'ORDEN_TRABAJO']:
                positions_data = self.pdf_extractor.extract_text(file_path, include_positions=True)
            metadata = self.pdf_extractor.extract_metadata(file_path)
        elif file_ext == '.docx':
            content = self.docx_extractor.extract_text(file_path)
            metadata = self.docx_extractor.extract_metadata(file_path)
        elif file_ext in ['.jpg', '.jpeg', '.png']:
            # Por ahora, solo metadatos para imágenes
            metadata = {
                'file_name': file_path.name,
                'file_size': file_path.stat().st_size,
                'type': 'image'
            }
        else:
            logger.warning(f"Tipo de archivo no soportado: {file_ext}")
            return None
        
        # Clasificar documento
        doc_type = self.classifier.classify(file_path, content)
        level = self.classifier.determine_level(doc_type)
        
        # Extraer entidades (con posiciones si están disponibles)
        entities = {}
        if content:
            entities = self.entity_extractor.extract_all(content, file_path, positions_data)
        
        # Generar file_id único
        file_id = str(uuid.uuid4())
        
        # Ruta relativa para almacenamiento
        relative_path = str(file_path.relative_to(base_path))
        
        # Construir resultado
        result = {
            'type': doc_type,
            'file_id': file_id,
            'original_name': file_path.name,
            'standardized_name': self._generate_standardized_name(file_path, doc_type),
            'level': level,
            'file_path': relative_path,
            'entities': entities,
            'metadata': metadata
        }
        
        # Agregar extracted_data según tipo
        if doc_type == 'CARTA_RESPUESTA' and content:
            result['extracted_data'] = self._extract_response_data(content)
        elif doc_type == 'TABLA_CALCULO' and entities.get('amounts'):
            result['extracted_data'] = {
                'total_amount': max(entities['amounts']) if entities['amounts'] else None,
                'cim_kwh': None  # Se puede extraer con más detalle después
            }
        elif doc_type == 'EVIDENCIA_FOTOGRAFICA':
            result['metadata'] = {
                **metadata,
                'quantity': 1,
                'tags': self._extract_image_tags(file_path.name)
            }
        
        return result
    
    def _generate_standardized_name(self, file_path: Path, doc_type: str) -> str:
        """Genera un nombre estandarizado para el documento"""
        type_names = {
            'CARTA_RESPUESTA': 'Carta de Respuesta',
            'ORDEN_TRABAJO': 'Orden de Trabajo',
            'TABLA_CALCULO': 'Tabla de Cálculo',
            'EVIDENCIA_FOTOGRAFICA': 'Evidencia Fotográfica',
            'GRAFICO_CONSUMO': 'Gráfico de Consumo',
            'INFORME_CNR': 'Informe CNR',
            'OTROS': 'Documento'
        }
        return f"{type_names.get(doc_type, 'Documento')} - {file_path.stem}"
    
    def _extract_response_data(self, content: str) -> Dict[str, Any]:
        """Extrae datos específicos de una carta de respuesta"""
        content_lower = content.lower()
        data = {}
        
        # Buscar fecha de respuesta
        date_match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', content)
        if date_match:
            data['response_date'] = date_match.group(1)
        
        # Buscar decisión
        if any(word in content_lower for word in ['rechazado', 'rechaza', 'improcedente']):
            data['decision'] = 'REJECTED'
        elif any(word in content_lower for word in ['aceptado', 'acepta', 'procede']):
            data['decision'] = 'ACCEPTED'
        else:
            data['decision'] = 'PENDING'
        
        return data
    
    def _extract_image_tags(self, file_name: str) -> List[str]:
        """Extrae tags de nombres de archivos de imágenes"""
        tags = []
        file_lower = file_name.lower()
        
        if 'medidor' in file_lower or 'medicion' in file_lower:
            tags.append('medidor')
        if 'fachada' in file_lower:
            tags.append('fachada')
        if 'sello' in file_lower:
            tags.append('sello')
        if 'instalacion' in file_lower or 'instalación' in file_lower:
            tags.append('instalacion')
        
        return tags if tags else ['general']
    
    def _consolidar_texto_documentos(
        self, 
        document_inventory: Dict[str, Any], 
        case_folder: Path
    ) -> str:
        """
        Consolida el texto de todos los documentos procesados
        """
        textos = []
        
        # Procesar documentos críticos
        for doc in document_inventory.get('level_1_critical', []):
            file_id = doc.get('file_id')
            file_path = case_folder / doc.get('file_path', '')
            
            if file_path.exists():
                try:
                    if file_path.suffix.lower() == '.pdf':
                        content = self.pdf_extractor.extract_text(file_path, include_positions=False)
                        if content:
                            textos.append(content)
                    elif file_path.suffix.lower() == '.docx':
                        content = self.docx_extractor.extract_text(file_path)
                        if content:
                            textos.append(content)
                except Exception as e:
                    logger.warning(f"Error extrayendo texto de {file_path}: {e}")
        
        # Procesar documentos soportantes (solo algunos tipos)
        tipos_soportantes_texto = ['INFORME_CNR', 'GRAFICO_CONSUMO']
        for doc in document_inventory.get('level_2_supporting', []):
            if doc.get('type') in tipos_soportantes_texto:
                file_path = case_folder / doc.get('file_path', '')
                if file_path.exists():
                    try:
                        if file_path.suffix.lower() == '.pdf':
                            content = self.pdf_extractor.extract_text(file_path, include_positions=False)
                            if content:
                                textos.append(content)
                    except Exception as e:
                        logger.warning(f"Error extrayendo texto de {file_path}: {e}")
        
        return '\n\n'.join(textos)

