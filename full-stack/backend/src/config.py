from pathlib import Path

# La raíz del directorio del backend, definida como el directorio padre de 'src'.
# Esto sirve como un ancla robusta para todas las demás rutas.
BACKEND_ROOT = Path(__file__).resolve().parent.parent

# --- Directorios de Datos ---
DATA_DIR = BACKEND_ROOT / "data"
DATABASE_DIR = DATA_DIR / "DataBase"
FILES_DIR = DATA_DIR / "Files"
# Los casos están directamente en FILES_DIR (ej: data/Files/230125-000509/)
# Las resoluciones se guardan en: data/Files/{case_id}/resoluciones/
EXAMPLE_CASES_DIR = FILES_DIR
RESOLUCIONES_DIR = DATA_DIR / "resoluciones"  # DEPRECATED: Las resoluciones ahora se guardan en la carpeta del caso
TEMP_PDFS_DIR = DATA_DIR / "temp_pdfs"  # Para previews temporales

# --- Archivos de Datos Específicos ---
MOCK_CASOS_PATH = DATA_DIR / "mock_casos.json"

# --- Directorios de Plantillas ---
TEMPLATES_DIR = BACKEND_ROOT / "templates"
CHECKLIST_TEMPLATES_DIR = TEMPLATES_DIR / "checklist"
RESOLUCION_TEMPLATES_DIR = TEMPLATES_DIR / "resolucion"
EXPEDIENTE_TEMPLATES_DIR = TEMPLATES_DIR / "expediente"
