"""
Script para procesar los casos reales de ejemplo y almacenarlos en base de datos
"""

import sys
import os
from pathlib import Path

# Obtener el directorio backend (padre del directorio scripts)
backend_dir = Path(__file__).parent.parent
backend_dir_str = str(backend_dir.resolve())

# Agregar el directorio backend al path para imports
if backend_dir_str not in sys.path:
    sys.path.insert(0, backend_dir_str)

# Cambiar al directorio backend para asegurar imports correctos
os.chdir(backend_dir_str)

# Ahora podemos importar los módulos
try:
    from engine.omc import DocumentProcessor
    from database import DBManager
except ImportError as e:
    print(f"Error de importación: {e}")
    print(f"Python path: {sys.path}")
    print(f"Directorio actual: {os.getcwd()}")
    print(f"Backend dir: {backend_dir_str}")
    raise

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_all_cases():
    """Procesa todos los casos en example_cases"""
    
    # Rutas
    base_dir = Path(__file__).parent.parent
    cases_dir = base_dir / "data" / "example_cases"
    db_path = base_dir / "data" / "sec_reclamos.db"
    
    if not cases_dir.exists():
        logger.error(f"Directorio de casos no encontrado: {cases_dir}")
        return
    
    # Inicializar componentes
    processor = DocumentProcessor()
    db = DBManager(str(db_path))
    
    # Procesar cada carpeta de caso
    case_folders = [d for d in cases_dir.iterdir() if d.is_dir()]
    
    logger.info(f"Encontrados {len(case_folders)} casos para procesar")
    
    for case_folder in case_folders:
        case_id = case_folder.name
        logger.info(f"\n{'='*60}")
        logger.info(f"Procesando caso: {case_id}")
        logger.info(f"{'='*60}")
        
        try:
            # Procesar caso
            edn = processor.process_case(case_id, case_folder)
            
            # Extraer información para BD
            unified_context = edn.get('unified_context', {})
            rut = unified_context.get('rut_client')
            nis = unified_context.get('service_nis')
            comuna = unified_context.get('commune') or 'Desconocida'
            
            if not rut:
                logger.warning(f"Caso {case_id}: No se encontró RUT, usando placeholder")
                rut = f"RUT-{case_id}"
            
            if not nis:
                logger.warning(f"Caso {case_id}: No se encontró NIS, usando placeholder")
                nis = f"NIS-{case_id}"
            
            # Upsert Persona
            persona_id = db.upsert_persona(
                rut=rut,
                nombre=unified_context.get('client_name'),
                email=unified_context.get('email'),
                telefono=unified_context.get('phone')
            )
            logger.info(f"Persona ID: {persona_id} (RUT: {rut})")
            
            # Upsert Suministro
            suministro_id = db.upsert_suministro(
                nis=nis,
                comuna=comuna,
                direccion=unified_context.get('address_standard'),
                numero_cliente=nis
            )
            logger.info(f"Suministro ID: {suministro_id} (NIS: {nis}, Comuna: {comuna})")
            
            # Determinar empresa y materia desde documentos
            empresa = None
            materia = None
            monto_disputa = None
            
            # Buscar en documentos
            for doc in edn['document_inventory']['level_1_critical'] + edn['document_inventory']['level_2_supporting']:
                if doc.get('extracted_data', {}).get('total_amount'):
                    monto_disputa = doc['extracted_data']['total_amount']
            
            # Upsert Caso
            caso_id_db = db.upsert_caso(
                case_id=case_id,
                persona_id=persona_id,
                suministro_id=suministro_id,
                edn=edn,
                empresa=empresa,
                materia=materia,
                monto_disputa=monto_disputa,
                fecha_ingreso=None  # Se puede extraer del case_id si es necesario
            )
            logger.info(f"Caso ID: {caso_id_db}")
            
            # Upsert Documentos
            doc_count = 0
            for level in ['level_1_critical', 'level_2_supporting']:
                for doc in edn['document_inventory'].get(level, []):
                    db.upsert_documento(
                        caso_id=caso_id_db,
                        file_id=doc['file_id'],
                        original_name=doc['original_name'],
                        doc_type=doc['type'],
                        level=level,
                        file_path=doc.get('file_path'),
                        standardized_name=doc.get('standardized_name'),
                        extracted_data=doc.get('extracted_data'),
                        metadata=doc.get('metadata')
                    )
                    doc_count += 1
            
            logger.info(f"Documentos procesados: {doc_count}")
            logger.info(f"✓ Caso {case_id} procesado exitosamente")
            
        except Exception as e:
            logger.error(f"Error procesando caso {case_id}: {e}", exc_info=True)
            continue
    
    logger.info(f"\n{'='*60}")
    logger.info("Procesamiento completado")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    process_all_cases()

