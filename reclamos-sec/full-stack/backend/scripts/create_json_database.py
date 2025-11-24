"""
Script para crear base de datos JSON relacional basada en los casos de ejemplo
"""

import json
from pathlib import Path
from datetime import datetime, timezone
import re

def extract_case_info(case_id: str, case_folder: Path):
    """Extrae información básica del caso desde nombres de archivos y estructura"""
    
    # Extraer fecha del case_id (formato: YYMMDD-XXXXXX)
    fecha_match = re.match(r'(\d{6})-(\d{6})', case_id)
    fecha_ingreso = None
    if fecha_match:
        year = '20' + fecha_match.group(1)[:2]
        month = fecha_match.group(1)[2:4]
        day = fecha_match.group(1)[4:6]
        fecha_ingreso = f"{year}-{month}-{day}"
    
    # Buscar información en nombres de archivos y carpetas
    nis = None
    numero_cliente = None
    rut = None
    empresa = None
    client_name = None
    
    # Buscar en nombres de archivos y carpetas
    for item_path in case_folder.rglob('*'):
        item_name = item_path.name if item_path.is_file() else item_path.name
        
        # Buscar NIS en nombres como "nrocliente_585416-4" o "nrocliente 585416-4"
        nis_match = re.search(r'nrocliente[_\s]+(\d+[-]?\d*)', item_name, re.IGNORECASE)
        if nis_match:
            # Priorizar este NIS sobre otros encontrados
            nis = nis_match.group(1).replace('-', '')
            numero_cliente = nis_match.group(1)
        
        # Buscar NIS en formato "NIS 608749"
        nis_match2 = re.search(r'\bNIS\s+(\d+)', item_name, re.IGNORECASE)
        if nis_match2 and not nis:
            nis = nis_match2.group(1)
        
        # Buscar número de cliente en nombres como "cliente Nº 4421" o "cliente N° 4421"
        cliente_match = re.search(r'cliente\s*N[°º]\s*(\d+)', item_name, re.IGNORECASE)
        if cliente_match:
            numero_cliente = cliente_match.group(1)
            if not nis:
                nis = cliente_match.group(1)
        
        # Buscar número de caso SEC en nombres como "Caso SEC N° 1994324"
        caso_match = re.search(r'caso\s+sec\s+n[°º]\s*(\d+)', item_name, re.IGNORECASE)
        if caso_match:
            numero_cliente = caso_match.group(1)
        
        # Buscar número de cliente en nombres como "1982860" (al inicio del nombre)
        # Solo si no se encontró un NIS más específico
        num_match = re.match(r'^(\d{7,10})', item_name)
        if num_match and not nis:
            nis = num_match.group(1)
            numero_cliente = num_match.group(1)
        
        # Buscar en nombres como "Caso585416_4" o "585416-4"
        caso_nis_match = re.search(r'(\d{6,8}[-_]?\d*)', item_name)
        if caso_nis_match and 'nrocliente' not in item_name.lower() and not nis:
            potential_nis = caso_nis_match.group(1).replace('-', '').replace('_', '')
            if len(potential_nis) >= 6:
                nis = potential_nis
                numero_cliente = caso_nis_match.group(1)
    
    # Clasificar documentos
    documentos = []
    for file_path in case_folder.rglob('*'):
        if file_path.is_file() and not file_path.name.startswith('.'):
            relative_path = str(file_path.relative_to(case_folder))
            
            # Clasificar por nombre
            doc_type = "OTROS"
            level = "level_2_supporting"
            
            file_name_lower = file_path.name.lower()
            
            if any(x in file_name_lower for x in ['respuesta', 'rpt_cnr', 'resolucion']):
                doc_type = "CARTA_RESPUESTA"
                level = "level_1_critical"
            elif any(x in file_name_lower for x in ['calculo', 'cálculo', 'cnr']):
                doc_type = "TABLA_CALCULO"
                level = "level_1_critical"
            elif any(x in file_name_lower for x in ['orden', 'trabajo', 'ot_']):
                doc_type = "ORDEN_TRABAJO"
                level = "level_1_critical"
            elif any(x in file_name_lower for x in ['foto', 'fachada', 'imagen', '.jpg', '.jpeg', '.png']):
                doc_type = "EVIDENCIA_FOTOGRAFICA"
            elif any(x in file_name_lower for x in ['consumo', 'consumos', 'periodo']):
                doc_type = "GRAFICO_CONSUMO"
            elif any(x in file_name_lower for x in ['informe', 'instalacion']):
                doc_type = "INFORME_CNR"
            
            documentos.append({
                "file_id": f"{case_id}-{len(documentos)+1}",
                "original_name": file_path.name,
                "type": doc_type,
                "level": level,
                "file_path": relative_path,
                "absolute_path": str(file_path.resolve())
            })
    
    return {
        "case_id": case_id,
        "nis": nis or f"NIS-{case_id}",
        "numero_cliente": numero_cliente,
        "rut": rut or f"RUT-{case_id}",
        "empresa": empresa,
        "fecha_ingreso": fecha_ingreso,
        "documentos": documentos
    }


def create_json_database():
    """Crea la estructura JSON de base de datos"""
    
    base_dir = Path(__file__).parent.parent
    cases_dir = base_dir / "data" / "example_cases"
    db_dir = base_dir / "data" / "DataBase"
    
    # Crear directorio DataBase
    db_dir.mkdir(parents=True, exist_ok=True)
    
    # Estructuras de datos
    personas = {}
    suministros = {}
    casos = []
    
    # Procesar cada caso
    case_folders = [d for d in cases_dir.iterdir() if d.is_dir()]
    
    for case_folder in case_folders:
        case_id = case_folder.name
        print(f"Procesando caso: {case_id}")
        
        info = extract_case_info(case_id, case_folder)
        
        # Crear/actualizar persona
        rut = info['rut']
        if rut not in personas:
            # Intentar extraer nombre del cliente si está disponible
            nombre = info.get('client_name') or f"Cliente {case_id}"
            personas[rut] = {
                "id": len(personas) + 1,
                "rut": rut,
                "nombre": nombre,
                "email": None,
                "telefono": None
            }
        persona_id = personas[rut]["id"]
        
        # Crear/actualizar suministro
        nis = info['nis']
        comuna = "Desconocida"  # Se puede extraer de archivos si es necesario
        suministro_key = f"{nis}-{comuna}"
        
        if suministro_key not in suministros:
            suministros[suministro_key] = {
                "id": len(suministros) + 1,
                "nis": nis,
                "comuna": comuna,
                "direccion": None,
                "numero_cliente": info.get('numero_cliente')
            }
        suministro_id = suministros[suministro_key]["id"]
        
        # Organizar documentos por nivel
        doc_inventory = {
            "level_1_critical": [],
            "level_2_supporting": [],
            "level_0_missing": []
        }
        
        for doc in info['documentos']:
            doc_entry = {
                "type": doc['type'],
                "file_id": doc['file_id'],
                "original_name": doc['original_name'],
                "standardized_name": f"{doc['type']} - {doc['original_name']}",
                "file_path": doc['file_path'],
                "absolute_path": doc['absolute_path']
            }
            
            if doc['level'] == 'level_1_critical':
                doc_inventory['level_1_critical'].append(doc_entry)
            else:
                doc_inventory['level_2_supporting'].append(doc_entry)
        
        # Verificar documentos faltantes
        doc_types = {d['type'] for d in info['documentos']}
        if 'CARTA_RESPUESTA' not in doc_types:
            doc_inventory['level_0_missing'].append({
                "required_type": "CARTA_RESPUESTA",
                "alert_level": "HIGH",
                "description": "No se detectó carta de respuesta"
            })
        if 'TABLA_CALCULO' not in doc_types:
            doc_inventory['level_0_missing'].append({
                "required_type": "TABLA_CALCULO",
                "alert_level": "HIGH",
                "description": "No se detectó tabla de cálculo"
            })
        
        # Crear EDN
        edn = {
            "compilation_metadata": {
                "case_id": case_id,
                "processing_timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "COMPLETED"
            },
            "unified_context": {
                "rut_client": rut,
                "client_name": personas[rut]["nombre"],
                "service_nis": nis,
                "address_standard": None,
                "commune": comuna,
                "email": None,
                "phone": None
            },
            "document_inventory": doc_inventory,
            "materia": "Reclamo SEC",
            "monto_disputa": None,
            "empresa": info.get('empresa'),
            "fecha_ingreso": info.get('fecha_ingreso'),
            "alertas": []
        }
        
        # Crear caso (sin EDN anidado)
        caso = {
            "id": len(casos) + 1,
            "case_id": case_id,
            "persona_id": persona_id,
            "suministro_id": suministro_id,
            "empresa": info.get('empresa'),
            "materia": "Reclamo SEC",
            "monto_disputa": None,
            "fecha_ingreso": info.get('fecha_ingreso'),
            "estado": "PENDIENTE"
        }
        
        casos.append(caso)
        
        # Guardar EDN en estructura separada
        edns[case_id] = edn
    
    # Guardar archivos JSON
    with open(db_dir / "personas.json", "w", encoding="utf-8") as f:
        json.dump(list(personas.values()), f, indent=2, ensure_ascii=False)
    
    with open(db_dir / "suministros.json", "w", encoding="utf-8") as f:
        json.dump(list(suministros.values()), f, indent=2, ensure_ascii=False)
    
    with open(db_dir / "casos.json", "w", encoding="utf-8") as f:
        json.dump(casos, f, indent=2, ensure_ascii=False)
    
    # Guardar EDNs en archivo separado
    with open(db_dir / "edn.json", "w", encoding="utf-8") as f:
        json.dump(edns, f, indent=2, ensure_ascii=False)
    
    # Crear índice de documentos (usando EDNs)
    documentos = []
    for caso in casos:
        case_id = caso['case_id']
        if case_id in edns:
            for level in ['level_1_critical', 'level_2_supporting']:
                for doc in edns[case_id]['document_inventory'].get(level, []):
                    documentos.append({
                        "id": len(documentos) + 1,
                        "caso_id": caso['id'],
                        "case_id": caso['case_id'],
                        **doc
                    })
    
    with open(db_dir / "documentos.json", "w", encoding="utf-8") as f:
        json.dump(documentos, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Base de datos JSON creada en {db_dir}")
    print(f"  - {len(personas)} personas")
    print(f"  - {len(suministros)} suministros")
    print(f"  - {len(casos)} casos")
    print(f"  - {len(edns)} EDNs")
    print(f"  - {len(documentos)} documentos")


if __name__ == "__main__":
    create_json_database()

