# Sistema de Análisis de Reclamos SEC - Interfaz Web

Aplicación web full-stack para funcionarios SEC que permite gestionar y analizar reclamos.

## Estructura del Proyecto

```
full-stack/
├── backend/          # API FastAPI
└── frontend/         # Aplicación Vue.js
```

## Requisitos Previos

- Python 3.8+
- Node.js 16+
- npm o yarn

## Instalación y Ejecución

### Backend

1. Navegar a la carpeta backend:
```bash
cd backend
```

2. Crear entorno virtual (recomendado):
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Ejecutar el servidor:
```bash
python main.py
```

El backend estará disponible en `http://localhost:8000`
La documentación de la API estará en `http://localhost:8000/docs`

### Frontend

1. Navegar a la carpeta frontend:
```bash
cd frontend
```

2. Instalar dependencias:
```bash
npm install
```

3. Ejecutar el servidor de desarrollo:
```bash
npm run dev
```

El frontend estará disponible en `http://localhost:5173`

## Uso

1. Asegúrate de que el backend esté ejecutándose
2. Abre el navegador en `http://localhost:5173`
3. Verás el dashboard con los casos de ejemplo
4. Haz click en "Abrir" en cualquier caso para ver las 4 secciones:
   - **Sección A**: Resumen de Contexto
   - **Sección B**: Gestor Documental (puedes re-clasificar documentos)
   - **Sección C**: Checklist de Validación (se actualiza automáticamente al cambiar documentos)
   - **Sección D**: Motor de Resolución

## Características

- Panel de reclamos pendientes con filtros
- Vista detallada de casos con 4 secciones interactivas
- Re-clasificación de documentos con actualización automática del checklist
- Validación manual de items del checklist
- Generación automática de borradores de resolución
- Interfaz moderna y responsive

## Datos de Ejemplo

El sistema incluye 3 casos de ejemplo con diferentes estados:
- SEC-2024-001: Facturación Excesiva (con documentos faltantes)
- SEC-2024-002: Corte de Suministro (completo)
- SEC-2024-003: Medición Incorrecta (requiere revisión manual)

## Próximos Pasos

- Conectar con datos reales de SEC
- Agregar autenticación de usuarios
- Mejorar visor de documentos (PDF.js)
- Agregar más filtros y búsqueda avanzada

