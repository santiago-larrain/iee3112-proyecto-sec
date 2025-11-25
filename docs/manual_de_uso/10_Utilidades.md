# Capítulo 10: Utilidades

[← Anterior: Resolución](9_Resolucion.md) | [Siguiente: Futuras Analíticas →](11_Futuras_analiticas.md)

## 10.1. Visión General

Este capítulo describe las herramientas auxiliares, modos de operación y utilidades de desarrollo que facilitan el uso, testing y mantenimiento del sistema.

## 10.2. Modos de Operación

### 10.2.1. Modo Test (🧪)

**Propósito:** Desarrollo y pruebas con datos simulados.

**Características:**
- **Fuente de Datos:** `mock_casos.json` (datos de prueba)
- **Limitaciones:**
  - No se pueden editar casos (solo lectura)
  - No se pueden cerrar casos
  - Cambios no se persisten
- **Uso:** Desarrollo frontend, testing de UI, demostraciones

**Activación:**
- Toggle en header de la aplicación
- Persistido en `localStorage` como `app_mode: 'test'`

### 10.2.2. Modo Validate (✅)

**Propósito:** Trabajo con casos reales y producción.

**Características:**
- **Fuente de Datos:** `DataBase/casos.json`, `personas.json`, `suministros.json`, `documentos.json`
- **Capacidades Completas:**
  - Edición de información contextual
  - Re-clasificación de documentos
  - Validación de checklist
  - Generación y firma de resoluciones
  - Cierre de casos
  - Todos los cambios se persisten en la base de datos
- **Uso:** Operación normal del sistema, trabajo con casos reales

**Activación:**
- Toggle en header de la aplicación
- Persistido en `localStorage` como `app_mode: 'validate'`

### 10.2.3. Cambio de Modo

**Proceso:**
1. Usuario hace clic en toggle de modo
2. Sistema actualiza `localStorage`
3. Página se recarga para aplicar cambio
4. Backend lee modo desde header `X-App-Mode` o query param `mode`

**Consideraciones:**
- Cambio de modo requiere recarga de página
- Datos en memoria se pierden al cambiar
- Modo se mantiene entre sesiones

## 10.3. Scripts de Procesamiento

### 10.3.1. `create_json_database.py`

**Propósito:** Crear la base de datos JSON completa a partir de los casos de ejemplo, utilizando toda la potencia del motor OMC.

**Ubicación:** `full-stack/backend/src/engine/omc/create_json_database.py`

**Funcionalidad:**
- Escanea las carpetas de casos en `data/Files/` (directamente, sin subcarpeta `example_cases`)
- Para cada caso, invoca al **`DocumentProcessor` (OMC)**, que realiza:
  - Extracción de texto con OCR (PDFs)
  - Extracción de texto (DOCX)
  - Clasificación automática de documentos
  - Extracción de entidades clave (RUT, NIS, montos, direcciones, etc.)
  - Generación del Expediente Digital Normalizado (EDN)
- A partir de los EDNs generados, construye la base de datos relacional en formato JSON:
  - `personas.json`
  - `suministros.json`
  - `casos.json`
  - `documentos.json`
  - `edn.json`
- Organiza documentos por nivel (critical, supporting, missing)
- Crea relaciones entre entidades usando el modelo estrella

**Uso:**
Este script es fundamental para la configuración inicial del sistema y para agregar nuevos casos de ejemplo.

```bash
cd full-stack/backend
python src/engine/omc/create_json_database.py
```

**Output:**
- Archivos JSON actualizados en `data/DataBase/`
- Logging detallado del proceso de ingesta y normalización de cada caso
- Cada caso procesado muestra: RUT, NIS, comuna, cantidad de documentos críticos y soportantes

## 10.4. Herramientas de Debugging

### 10.4.1. Logging del Sistema

**Niveles de Log:**
- **DEBUG**: Información detallada para debugging
- **INFO**: Eventos normales del sistema
- **WARNING**: Situaciones anómalas pero manejables
- **ERROR**: Errores que requieren atención

**Configuración:**
- Backend: Logging a consola y archivo (opcional)
- Frontend: Console.log para desarrollo, deshabilitado en producción

### 10.4.2. Inspección de Datos

**Archivos JSON:**
- Fácil inspeccionar y editar manualmente
- Compatible con editores de texto y herramientas JSON
- Útil para debugging y corrección manual

**Base de Datos SQLite:**
- Herramientas: `sqlite3` CLI, DB Browser for SQLite
- Consultas directas para debugging
- Exportación de datos

### 10.4.3. Endpoints de Debugging

**Futuro:**
- `GET /api/debug/caso/{case_id}/edn`: Ver EDN completo
- `GET /api/debug/caso/{case_id}/checklist`: Ver checklist generado
- `GET /api/debug/stats`: Estadísticas del sistema

## 10.5. Utilidades de Desarrollo

### 10.5.1. Hot Reload

**Backend:**
- FastAPI con `--reload` para desarrollo
- Cambios en código se reflejan automáticamente
- No requiere reiniciar servidor

**Frontend:**
- Vite con Hot Module Replacement (HMR)
- Cambios en componentes se reflejan instantáneamente
- Estado de la aplicación se preserva

### 10.5.2. Validación de Esquemas

**Backend:**
- Pydantic valida modelos automáticamente
- Errores de validación se reportan claramente
- Type hints para mejor IDE support

**Frontend:**
- TypeScript (futuro) para type safety
- Validación de props en componentes Vue
- Linting con ESLint

### 10.5.3. Testing

**Backend (Futuro):**
- Tests unitarios con `pytest`
- Tests de integración para endpoints
- Mocks para dependencias externas

**Frontend (Futuro):**
- Tests unitarios con Vitest
- Tests E2E con Playwright
- Coverage reporting

## 10.6. Configuración y Variables de Entorno

### 10.6.1. Variables de Entorno

**Backend:**
- `DATABASE_PATH`: Ruta a base de datos
- `TEMPLATES_DIR`: Directorio de plantillas
- `LOG_LEVEL`: Nivel de logging
- `API_PORT`: Puerto del servidor

**Frontend:**
- `VITE_API_URL`: URL del backend
- `VITE_APP_MODE`: Modo por defecto

### 10.6.2. Archivos de Configuración

**Backend:**
- `requirements.txt`: Dependencias Python
- `main.py`: Configuración de FastAPI

**Frontend:**
- `package.json`: Dependencias npm
- `vite.config.js`: Configuración de Vite

## 10.7. Mantenimiento de Datos

### 10.7.1. Backup de Base de Datos

**JSON:**
- Copiar archivos `DataBase/*.json` periódicamente
- Versionado con Git (opcional)
- Backup automático (futuro)

**SQLite:**
- Exportar base de datos periódicamente
- Scripts de backup automatizados (futuro)

### 10.7.2. Limpieza de Datos

**Archivos Temporales:**
- `temp_pdfs/`: PDFs procesados temporalmente
- Limpieza automática después de procesamiento
- Limpieza manual periódica

**Cache:**
- Limpiar cache en memoria periódicamente
- Recargar datos desde disco
- Invalidar cache después de actualizaciones

### 10.7.3. Migración de Datos

**Futuro:**
- Scripts de migración entre versiones
- Validación de integridad post-migración
- Rollback en caso de errores

## 10.8. Monitoreo y Métricas

### 10.8.1. Métricas del Sistema

**Futuro:**
- Tiempo de procesamiento por caso
- Tasa de éxito de OCR
- Precisión de clasificación
- Tiempo de respuesta de API

### 10.8.2. Alertas

**Futuro:**
- Alertas de errores críticos
- Notificaciones de casos pendientes
- Alertas de rendimiento

## 10.9. Documentación de API

### 10.9.1. Swagger UI

**URL:** `http://localhost:8000/docs`

**Características:**
- Documentación interactiva generada automáticamente
- Prueba de endpoints directamente desde el navegador
- Esquemas de request/response

### 10.9.2. ReDoc

**URL:** `http://localhost:8000/redoc`

**Características:**
- Documentación alternativa más legible
- Navegación mejorada
- Exportación de documentación

## 10.10. Conclusión

Las utilidades y herramientas auxiliares facilitan el desarrollo, testing y mantenimiento del sistema. Los modos de operación permiten trabajar con datos de prueba o producción según necesidad. Los scripts automatizan tareas comunes como creación de base de datos y procesamiento de casos. Las herramientas de debugging y monitoreo ayudan a identificar y resolver problemas rápidamente. La documentación de API facilita la integración y el desarrollo.

---

[← Anterior: Resolución](9_Resolucion.md) | [Siguiente: Futuras Analíticas →](11_Futuras_analiticas.md)

