# 🚀 Implementación Full-Stack: Sistema de Análisis de Reclamos SEC

Este directorio contiene el código fuente completo de la solución full-stack para el análisis y gestión de reclamos de la Superintendencia de Electricidad y Combustibles (SEC). La implementación sigue una arquitectura modular basada en tres motores principales: **OMC** (Objeto Maestro de Compilación), **MIN** (Motor de Inferencia Normativa) y **MGR** (Motor de Generación de Resoluciones).

## 📚 Navegación Rápida

- **[Backend README](./backend/README.md)** - Lógica de negocio y motores (OMC, MIN, MGR)
- **[Frontend README](./frontend/README.md)** - Interfaz de usuario y componentes Vue.js
- **[Manual de Arquitectura](../docs/manual_de_uso/0_Indice.md)** - Documentación completa de ingeniería básica

## 🛠 Stack Tecnológico

### Backend
- **Python 3.11+** - Lenguaje principal
- **FastAPI** - Framework web asíncrono
- **Pydantic v2** - Validación de datos y modelos
- **Uvicorn** - Servidor ASGI de alto rendimiento

### Frontend
- **Vue.js 3** - Framework progresivo de JavaScript
- **Vite** - Build tool y dev server
- **Vue Router 4** - Enrutamiento SPA
- **Axios** - Cliente HTTP

## 📋 Pre-requisitos Globales

- **Node.js 18+** y npm (para frontend)
- **Python 3.11+** y pip (para backend)
- **Git** (para clonar el repositorio)
- **Docker** (opcional, para contenedores)

## 🏗 Arquitectura General

El sistema implementa un patrón **Pipeline & Filters** donde los datos fluyen a través de tres motores principales:

```
Documentos → OMC → EDN → MIN → Checklist → MGR → Resolución
```

- **OMC**: Procesa documentos, extrae datos y genera el Expediente Digital Normalizado (EDN)
- **MIN**: Evalúa el EDN contra reglas normativas y genera checklists configurables
- **MGR**: Genera borradores de resoluciones legales usando templates Markdown

## 🚦 Inicio Rápido

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

El servidor estará disponible en `http://localhost:8000`  
API Docs: `http://localhost:8000/docs`

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

La aplicación estará disponible en `http://localhost:5173`

## 📖 Documentación Adicional

Para detalles técnicos profundos sobre cada componente:

- **Backend**: Ver [backend/README.md](./backend/README.md)
- **Frontend**: Ver [frontend/README.md](./frontend/README.md)
- **Arquitectura**: Ver [docs/manual_de_uso/](../docs/manual_de_uso/)
- **Implementación**: Ver [docs/full-stack/](../docs/full-stack/)

## 🔗 Enlaces Útiles

- [Documentación de FastAPI](https://fastapi.tiangolo.com/)
- [Documentación de Vue.js](https://vuejs.org/)
- [Documentación de Vite](https://vitejs.dev/)
