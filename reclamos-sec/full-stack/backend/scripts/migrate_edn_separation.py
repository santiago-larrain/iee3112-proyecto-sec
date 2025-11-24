"""
Script de migración para separar EDNs de casos.json a edn.json
Extrae EDNs anidados y los mueve a un archivo separado
"""

import json
from pathlib import Path

def migrate_edn_separation():
    """Migra EDNs desde casos.json (estructura antigua) a edn.json (estructura nueva)"""
    
    base_dir = Path(__file__).parent.parent
    db_dir = base_dir / "data" / "DataBase"
    casos_path = db_dir / "casos.json"
    edn_path = db_dir / "edn.json"
    
    if not casos_path.exists():
        print(f"Error: No se encontró {casos_path}")
        return
    
    # Cargar casos existentes
    with open(casos_path, "r", encoding="utf-8") as f:
        casos = json.load(f)
    
    # Extraer EDNs
    edns = {}
    casos_updated = []
    
    for caso in casos:
        case_id = caso.get('case_id')
        if not case_id:
            continue
        
        # Extraer EDN si existe
        if 'edn' in caso:
            edns[case_id] = caso['edn']
        
        # Crear caso sin EDN anidado
        caso_updated = {
            "id": caso.get('id'),
            "case_id": caso.get('case_id'),
            "persona_id": caso.get('persona_id'),
            "suministro_id": caso.get('suministro_id'),
            "empresa": caso.get('empresa'),
            "materia": caso.get('materia'),
            "monto_disputa": caso.get('monto_disputa'),
            "fecha_ingreso": caso.get('fecha_ingreso'),
            "estado": caso.get('estado', 'PENDIENTE')
        }
        casos_updated.append(caso_updated)
    
    # Guardar casos actualizados (sin EDN)
    with open(casos_path, "w", encoding="utf-8") as f:
        json.dump(casos_updated, f, indent=2, ensure_ascii=False)
    
    # Guardar EDNs en archivo separado
    with open(edn_path, "w", encoding="utf-8") as f:
        json.dump(edns, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Migración completada:")
    print(f"  - {len(casos_updated)} casos actualizados en casos.json")
    print(f"  - {len(edns)} EDNs extraídos a edn.json")
    print(f"  - Archivo edn.json creado en {edn_path}")

if __name__ == "__main__":
    migrate_edn_separation()

