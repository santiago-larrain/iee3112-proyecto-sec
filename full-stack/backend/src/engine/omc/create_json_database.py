"""
Script para crear base de datos JSON relacional usando el motor OMC
Procesa casos desde data/Files/ y genera la estructura completa de base de datos
"""

import json
from pathlib import Path
from datetime import datetime, timezone
import sys
import os
import logging

# Obtener el directorio backend (padre del directorio src)
# Este script está en: full-stack/backend/src/engine/omc/create_json_database.py
# Necesitamos llegar a: full-stack/backend/
# Desde create_json_database.py: .parent = omc/, .parent = engine/, .parent = src/, .parent = backend/
current_file = Path(__file__).resolve()
# current_file.parent = src/engine/omc/
# current_file.parent.parent = src/engine/
# current_file.parent.parent.parent = src/
# current_file.parent.parent.parent.parent = backend/
backend_dir = current_file.parent.parent.parent.parent
backend_dir_str = str(backend_dir)

# Agregar el directorio backend al path para imports
if backend_dir_str not in sys.path:
    sys.path.insert(0, backend_dir_str)

# Cambiar al directorio backend para asegurar imports correctos
os.chdir(backend_dir_str)

try:
    from src.config import EXAMPLE_CASES_DIR, DATABASE_DIR, FILES_DIR
    from src.engine.omc.document_processor import DocumentProcessor
except ImportError as e:
    print(f"Error de importación: {e}")
    print(f"Por favor, asegúrate de que:")
    print(f"1. Estás ejecutando el script desde el directorio 'backend/'")
    print(f"2. Todas las dependencias están instaladas: pip install -r requirements.txt")
    sys.exit(1)

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def extract_fecha_ingreso(case_id: str) -> str:
    """Extrae la fecha de ingreso desde el case_id (formato: YYMMDD-XXXXXX)"""
    import re
    fecha_match = re.match(r'(\d{6})-(\d{6})', case_id)
    if fecha_match:
        year = '20' + fecha_match.group(1)[:2]
        month = fecha_match.group(1)[2:4]
        day = fecha_match.group(1)[4:6]
        return f"{year}-{month}-{day}"
    return None


def create_json_database():
    """Crea la estructura JSON de base de datos usando el motor OMC"""
    
    cases_dir = EXAMPLE_CASES_DIR
    db_dir = DATABASE_DIR
    
    # Verificar que el directorio de casos existe
    if not cases_dir.exists():
        logger.error(f"Error: No se encontró el directorio de casos: {cases_dir}")
        logger.error(f"Por favor, asegúrate de que los casos estén en: {cases_dir}")
        return
    
    # Crear directorio DataBase
    db_dir.mkdir(parents=True, exist_ok=True)
    
    # Inicializar el procesador OMC
    processor = DocumentProcessor()
    logger.info("Motor OMC inicializado")
    
    # Estructuras de datos
    personas = {}  # {rut: persona_dict}
    suministros = {}  # {f"{nis}-{comuna}": suministro_dict}
    casos = []
    edns = {}  # {case_id: edn_dict}
    
    # Procesar cada caso usando el OMC
    case_folders = [d for d in cases_dir.iterdir() if d.is_dir()]
    logger.info(f"Encontrados {len(case_folders)} casos para procesar")
    
    for case_folder in case_folders:
        case_id = case_folder.name
        logger.info(f"\n{'='*60}")
        logger.info(f"Procesando caso: {case_id}")
        logger.info(f"{'='*60}")
        
        try:
            # Usar el OMC para procesar el caso completo
            edn = processor.process_case(case_id, case_folder)
            
            # Extraer información del EDN generado por el OMC
            unified_context = edn.get('unified_context', {})
            compilation_metadata = edn.get('compilation_metadata', {})
            document_inventory = edn.get('document_inventory', {})
            
            # Obtener datos del contexto unificado
            rut = unified_context.get('rut_client')
            client_name = unified_context.get('client_name')
            nis = unified_context.get('service_nis')
            comuna = unified_context.get('commune') or 'Desconocida'
            direccion = unified_context.get('address_standard')
            email = unified_context.get('email')
            phone = unified_context.get('phone')
            
            # Valores por defecto si no se encontraron
            if not rut:
                logger.warning(f"Caso {case_id}: No se encontró RUT, usando placeholder")
                rut = f"RUT-{case_id}"
            if not nis:
                logger.warning(f"Caso {case_id}: No se encontró NIS, usando placeholder")
                nis = f"NIS-{case_id}"
            if not client_name:
                client_name = f"Cliente {case_id}"
            
            # Crear/actualizar persona
            if rut not in personas:
                personas[rut] = {
                    "id": len(personas) + 1,
                    "rut": rut,
                    "nombre": client_name,
                    "email": email,
                    "telefono": phone
                }
            else:
                # Actualizar si hay más información
                if client_name and client_name != f"Cliente {case_id}":
                    personas[rut]["nombre"] = client_name
                if email:
                    personas[rut]["email"] = email
                if phone:
                    personas[rut]["telefono"] = phone
            persona_id = personas[rut]["id"]
            
            # Crear/actualizar suministro
            suministro_key = f"{nis}-{comuna}"
            if suministro_key not in suministros:
                suministros[suministro_key] = {
                    "id": len(suministros) + 1,
                    "nis": nis,
                    "comuna": comuna,
                    "direccion": direccion,
                    "numero_cliente": nis  # Usar NIS como número de cliente por defecto
                }
            else:
                # Actualizar si hay más información
                if direccion:
                    suministros[suministro_key]["direccion"] = direccion
            suministro_id = suministros[suministro_key]["id"]
            
            # Extraer información adicional del EDN
            # Usar tipo_caso del EDN como materia si no existe materia específica
            tipo_caso = compilation_metadata.get('tipo_caso')
            materia = edn.get('materia') or tipo_caso or "Reclamo SEC"
            monto_disputa = edn.get('monto_disputa')
            empresa = edn.get('empresa')
            fecha_ingreso = edn.get('fecha_ingreso') or extract_fecha_ingreso(case_id)
            
            # Actualizar documentos con rutas relativas correctas desde FILES_DIR
            for level in ['level_1_critical', 'level_2_supporting']:
                for doc in document_inventory.get(level, []):
                    # El OMC genera file_path relativo desde la carpeta del caso
                    # Necesitamos agregar relative_path desde FILES_DIR
                    file_path_relativo = doc.get('file_path', '')
                    if file_path_relativo:
                        # Construir ruta completa y luego relativa desde FILES_DIR
                        file_path_completo = case_folder / file_path_relativo
                        if file_path_completo.exists():
                            doc['relative_path'] = str(file_path_completo.relative_to(FILES_DIR))
                        else:
                            # Fallback: construir desde case_id y file_path
                            doc['relative_path'] = f"{case_id}/{file_path_relativo}"
                    else:
                        # Si no hay file_path, intentar desde original_name
                        file_path_completo = case_folder / doc.get('original_name', '')
                        if file_path_completo.exists():
                            doc['relative_path'] = str(file_path_completo.relative_to(FILES_DIR))
                            doc['file_path'] = doc.get('original_name', '')
            
            # Actualizar EDN con información adicional
            edn['materia'] = materia
            edn['monto_disputa'] = monto_disputa
            edn['empresa'] = empresa
            edn['fecha_ingreso'] = fecha_ingreso
            
            # Crear caso (sin EDN anidado)
            caso = {
                "id": len(casos) + 1,
                "case_id": case_id,
                "persona_id": persona_id,
                "suministro_id": suministro_id,
                "empresa": empresa,
                "materia": materia,
                "monto_disputa": monto_disputa,
                "fecha_ingreso": fecha_ingreso,
                "estado": "PENDIENTE"
            }
            casos.append(caso)
            
            # Guardar EDN en estructura separada
            edns[case_id] = edn
            
            logger.info(f"✓ Caso {case_id} procesado exitosamente")
            logger.info(f"  - RUT: {rut}, NIS: {nis}, Comuna: {comuna}")
            logger.info(f"  - Documentos: {len(document_inventory.get('level_1_critical', []))} críticos, "
                       f"{len(document_inventory.get('level_2_supporting', []))} soportantes")
            
        except Exception as e:
            logger.error(f"Error procesando caso {case_id}: {e}", exc_info=True)
            continue
    
    # Crear índice de documentos desde los EDNs
    documentos = []
    for caso in casos:
        case_id = caso['case_id']
        if case_id in edns:
            doc_inventory = edns[case_id].get('document_inventory', {})
            for level in ['level_1_critical', 'level_2_supporting']:
                for doc in doc_inventory.get(level, []):
                    doc_entry = {
                        "id": len(documentos) + 1,
                        "caso_id": caso['id'],
                        "case_id": case_id,
                        "type": doc.get('type'),
                        "file_id": doc.get('file_id'),
                        "original_name": doc.get('original_name'),
                        "standardized_name": doc.get('standardized_name'),
                        "file_path": doc.get('file_path'),  # Relativo desde carpeta del caso
                        "relative_path": doc.get('relative_path'),  # Relativo desde FILES_DIR
                        "level": level
                    }
                    # Agregar extracted_data y metadata si existen
                    if doc.get('extracted_data'):
                        doc_entry['extracted_data'] = doc['extracted_data']
                    if doc.get('metadata'):
                        doc_entry['metadata'] = doc['metadata']
                    
                    documentos.append(doc_entry)
    
    # Guardar archivos JSON
    logger.info(f"\nGuardando archivos JSON en {db_dir}...")
    
    with open(db_dir / "personas.json", "w", encoding="utf-8") as f:
        json.dump(list(personas.values()), f, indent=2, ensure_ascii=False)
    
    with open(db_dir / "suministros.json", "w", encoding="utf-8") as f:
        json.dump(list(suministros.values()), f, indent=2, ensure_ascii=False)
    
    with open(db_dir / "casos.json", "w", encoding="utf-8") as f:
        json.dump(casos, f, indent=2, ensure_ascii=False)
    
    with open(db_dir / "edn.json", "w", encoding="utf-8") as f:
        json.dump(edns, f, indent=2, ensure_ascii=False)
    
    with open(db_dir / "documentos.json", "w", encoding="utf-8") as f:
        json.dump(documentos, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n{'='*60}")
    logger.info("✓ Base de datos JSON creada exitosamente")
    logger.info(f"{'='*60}")
    logger.info(f"  - {len(personas)} personas")
    logger.info(f"  - {len(suministros)} suministros")
    logger.info(f"  - {len(casos)} casos")
    logger.info(f"  - {len(edns)} EDNs")
    logger.info(f"  - {len(documentos)} documentos")
    logger.info(f"\nUbicación: {db_dir}")


if __name__ == "__main__":
    print("Iniciando creación de base de datos JSON...")
    print(f"Directorio de trabajo: {os.getcwd()}")
    print(f"Backend dir: {backend_dir_str}")
    create_json_database()
    print("Proceso completado.")
