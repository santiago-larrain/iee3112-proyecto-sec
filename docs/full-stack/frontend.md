# Documentación Técnica: Frontend del Sistema de Análisis de Reclamos SEC

## 1. Visión General

El frontend del sistema está implementado en **Vue.js 3** como una **Single Page Application (SPA)** que proporciona una interfaz de usuario interactiva para funcionarios de la SEC. La arquitectura sigue un patrón de componentes modulares que se comunican con el backend mediante servicios REST.

## 2. Estructura de Carpetas

```
frontend/
├── index.html              # HTML base
├── vite.config.js          # Configuración de Vite
├── package.json            # Dependencias npm
├── src/
│   ├── main.js            # Punto de entrada Vue
│   ├── App.vue            # Componente raíz
│   ├── router/
│   │   └── index.js        # Configuración de rutas
│   ├── services/
│   │   └── api.js          # Servicio de API (Axios)
│   ├── views/              # Vistas principales
│   │   ├── Dashboard.vue   # Panel de casos
│   │   └── CasoDetalle.vue # Vista de detalle
│   └── components/         # Componentes reutilizables
│       ├── SeccionA.vue    # Resumen de contexto
│       ├── SeccionB.vue    # Gestor documental
│       ├── SeccionC.vue    # Checklist
│       ├── ChecklistItem.vue # Item de checklist
│       ├── SeccionD.vue    # Motor de resolución
│       └── AIChatPanel.vue # Panel de chat con IA
```

## 3. Componentes Principales

### 3.1. `main.js` - Punto de Entrada

**Responsabilidades:**
- Crear instancia de aplicación Vue
- Registrar router
- Montar aplicación en `#app`

**Código Base:**
```javascript
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

createApp(App).use(router).mount('#app')
```

### 3.2. `App.vue` - Componente Raíz

**Funcionalidad:**
- Header global con título y navegación
- Toggle de modo Test/Validate
- Persistencia de modo en `localStorage`
- Router-view para vistas dinámicas
- Integración del panel de chat con IA

**Características:**
- Botón de modo que cambia entre `test` y `validate`
- Botón de chat IA (🤖) que togglea el panel lateral
- Estado del chat persistido en `localStorage`
- Ajuste dinámico del contenido principal cuando el chat está abierto

**Estilos Globales:**
- Reset CSS básico
- Fuentes del sistema
- Colores y gradientes principales
- Transiciones suaves

### 3.3. `router/index.js` - Enrutamiento

**Rutas:**
- `/`: Dashboard (lista de casos)
- `/caso/:id`: CasoDetalle (vista de detalle)

**Configuración:**
- History mode habilitado
- Props automáticas para rutas con parámetros

### 3.4. `services/api.js` - Servicio de API

**Clase `casosAPI`:**

**Métodos:**
- `getCasos(tipoCaso)`: Obtiene lista de casos, opcionalmente filtrados por tipo
- `searchCasos(query)`: Busca casos por texto en campos del EDN
- `getCaso(caseId)`: Obtiene caso completo
- `updateDocumento(caseId, fileId, tipo, customName)`: Actualiza documento
- `updateChecklistItem(caseId, itemId, validated)`: Actualiza checklist
- `updateUnifiedContext(caseId, updates)`: Actualiza contexto
- `generarResolucion(caseId, templateType, content)`: Genera borrador
- `cerrarCaso(caseId, resolucionContent)`: Cierra caso

**Interceptor Axios:**
- Agrega header `X-App-Mode` en cada request
- Agrega query param `mode` para compatibilidad
- Lee modo desde `localStorage`

### 3.5. `views/Dashboard.vue` - Panel Principal

**Layout:**
- Diseño estilo Mail con sidebar izquierdo fijo y área principal flexible
- Sidebar con estadísticas y sección de análisis
- Barra de búsqueda con debouncing
- Filtros por estado y tipo de caso
- Tabla interactiva con casos

**Funcionalidad:**
- Carga lista de casos al montar
- Búsqueda con debouncing (300ms) que busca en campos del EDN
- Filtros por estado y tipo de caso
- Estadísticas en sidebar que se actualizan con filtros
- Tabla interactiva con casos
- Navegación a detalle de caso

**Computed Properties:**
- `totalCasos`: Total de casos
- `pendientes`: Casos pendientes
- `resueltos`: Casos resueltos
- `casosFiltrados`: Casos filtrados por estado y tipo

**Métodos:**
- `cargarCasos(tipoCaso)`: Fetch de casos desde API con filtro opcional
- `onSearch(query)`: Maneja búsqueda, llama a `casosAPI.searchCasos()`
- `onFilter(filters)`: Maneja filtros de estado y tipo
- `abrirCaso(caseId)`: Navegación a detalle

### 3.6. `views/CasoDetalle.vue` - Vista de Detalle

**Funcionalidad:**
- Carga caso completo al montar
- Orquesta las 4 secciones (A, B, C, D)
- Proporciona funciones compartidas mediante `provide/inject`
- Maneja estados de carga y error
- Normaliza datos para robustez

**Provide/Inject:**
- `actualizarDocumento`: Función para actualizar tipo de documento
- `actualizarChecklistItem`: Función para validar items
- `generarResolucion`: Función para generar borrador

**Métodos:**
- `cargarCaso()`: Fetch de caso desde API
- `normalizeCaso()`: Asegura estructura completa con valores por defecto
- `createEmptyCaso()`: Crea caso vacío en caso de error
- `recargarCaso()`: Recarga caso después de actualizaciones
- `onDocumentoActualizado()`: Handler de actualización de documento

**Robustez:**
- Maneja errores de red mostrando estructura parcial
- Valores por defecto ("—") para campos faltantes
- Recarga automática después de cambios

### 3.7. `components/SeccionA.vue` - Resumen de Contexto

**Props:**
- `unifiedContext`: Contexto unificado
- `compilationMetadata`: Metadatos del caso
- `materia`, `montoDisputa`, `empresa`, `fechaIngreso`, `alertas`

**Funcionalidad:**
- Modo visualización: Muestra información en tarjetas
- Modo edición: Inputs editables para todos los campos
- Toggle entre modos con botón "Editar"/"Guardar"
- Guarda cambios mediante `updateUnifiedContext`
- Emite evento `contexto-actualizado` para recargar caso

**Diseño:**
- Grid responsive de 3 tarjetas
- Headers con gradiente púrpura
- Iconos distintivos por categoría (👤 Cliente, 🏠 Suministro, 📋 Caso)

### 3.8. `components/SeccionB.vue` - Gestor Documental

**Props:**
- `documentInventory`: Inventario de documentos
- `caseId`: ID del caso

**Funcionalidad:**
- Lista documentos por nivel (critical, supporting, missing)
- Dropdown para cambiar tipo de documento
- Prompt para nombre personalizado al cambiar tipo
- Modal de vista previa de documentos
- Soporte para PDFs (iframe) e imágenes (img tag)

**Métodos:**
- `actualizarTipoDocumento()`: Actualiza tipo y nombre
- `verDocumento()`: Abre modal de vista previa
- `cerrarVisor()`: Cierra modal
- `cargarDocumento()`: Construye URL de preview

**Estados:**
- `documentoSeleccionado`: Documento actual en modal
- `documentUrl`: URL del documento para preview
- `loadingDocument`: Estado de carga
- `documentError`: Error al cargar documento

### 3.9. `components/SeccionC.vue` - Checklist

**Props:**
- `checklist`: Objeto Checklist con 3 grupos
- `caseId`: ID del caso

**Funcionalidad:**
- Renderiza 3 grupos de checklist
- Usa componente `ChecklistItem` para cada item
- Emite evento `checklist-actualizado` cuando se valida un item

**Diseño:**
- Títulos de grupo con estilo distintivo
- Lista de items con espaciado consistente

### 3.10. `components/ChecklistItem.vue` - Item de Checklist

**Props:**
- `item`: Objeto ChecklistItem
- `caseId`: ID del caso

**Funcionalidad:**
- Header expandible/colapsable
- Icono de estado visual (✅/❌/⚠️)
- Checkbox "Validado" para marcado manual
- Detalles expandidos: evidencia, descripción, tipo
- Deep linking a documentos (botón "Abrir Documento")

**Inyecta:**
- `actualizarChecklistItem`: Función del padre para actualizar validación

**Métodos:**
- `toggleExpand()`: Expande/colapsa detalles
- `getStatusIcon()`: Retorna emoji según estado
- `getStatusClass()`: Retorna clase CSS según estado
- `actualizarValidacion()`: Actualiza validación en backend

**Estilos Dinámicos:**
- Colores de borde y fondo según estado
- Transiciones suaves

### 3.11. `components/SeccionD.vue` - Motor de Resolución

**Props:**
- `caseId`: ID del caso
- `checklist`: Checklist para determinar tipo de resolución

**Funcionalidad:**
- Selector de tipo de resolución (Instrucción/Improcedente)
- Auto-generación de borrador al cargar
- Generación de borrador al cambiar tipo
- Editor de texto para editar borrador
- Botón "Firmar y Cerrar Caso"

**Métodos:**
- `onTemplateChange()`: Handler de cambio de tipo
- `generarBorrador()`: Genera nuevo borrador (reemplaza contenido)
- `firmarYCerrar()`: Cierra caso y guarda resolución

**Validaciones:**
- Verifica que haya contenido antes de cerrar
- Muestra confirmación antes de cerrar
- Estado de carga durante cierre

### 3.12. `components/AIChatPanel.vue` - Panel de Chat con IA

**Props:**
- `isOpen`: Boolean que controla la visibilidad del panel

**Funcionalidad:**
- Panel lateral derecho fijo
- Chat con mensajes del usuario y respuestas de IA
- Respuestas simuladas basadas en palabras clave
- Botón de colapsar/expandir en el header del panel
- Animaciones y diseño responsive

**Características:**
- Escribir mensajes y enviar con Enter
- Respuestas contextuales básicas (caso, documento, checklist, resolución)
- Respuesta genérica para otros mensajes
- Timestamps en cada mensaje
- Scroll automático a nuevos mensajes
- Diseño con avatares diferenciados (usuario vs IA)

**Diseño Responsive:**
- Ancho de 380px en desktop
- Se ajusta en tablets (320px)
- Ocupa toda la pantalla en móviles
- Transiciones suaves

## 4. Gestión de Estado

### 4.1. Estado Local por Componente

Cada componente gestiona su propio estado local mediante `data()` de Vue.

### 4.2. Comunicación entre Componentes

**Provide/Inject:**
- `CasoDetalle` proporciona funciones a `SeccionA`, `SeccionB`, `SeccionC`, `SeccionD`
- Permite actualizaciones coordinadas sin prop drilling

**Eventos:**
- Componentes emiten eventos (`contexto-actualizado`, `checklist-actualizado`)
- El componente padre escucha y recarga datos

### 4.3. Persistencia en `localStorage`

**Datos Persistidos:**
- `app_mode`: Modo de operación (`test` o `validate`)
- `ai_chat_open`: Estado del panel de chat

**Carga al Iniciar:**
- Los componentes leen `localStorage` en `mounted()`
- Restauran el estado previo de la sesión

## 5. Comunicación con Backend

### 5.1. Servicio API

El servicio `api.js` encapsula todas las llamadas HTTP al backend usando Axios.

### 5.2. Manejo de Errores

- Try-catch en métodos async
- Mensajes de error amigables al usuario
- Fallbacks a datos vacíos en caso de error

### 5.3. Estados de Carga

- Indicadores de carga durante fetch de datos
- Deshabilitación de botones durante operaciones
- Feedback visual de acciones exitosas

## 6. Dependencias Principales

Ver `package.json`:
- `vue`: Framework frontend
- `vue-router`: Enrutamiento
- `axios`: Cliente HTTP
- `vite`: Build tool y dev server

## 7. Configuración y Ejecución

### 7.1. Instalación

```bash
cd reclamos-sec/full-stack/frontend
npm install
```

### 7.2. Ejecución en Desarrollo

```bash
npm run dev
```

El frontend estará disponible en `http://localhost:5173`

### 7.3. Build de Producción

```bash
npm run build
```

Genera archivos estáticos en `dist/`

## 8. Modos de Operación

### 8.1. Modo Test (🧪)

**Propósito:** Desarrollo y pruebas

**Fuente de Datos:** `mock_casos.json`

**Limitaciones:**
- No se pueden editar casos (solo lectura)
- No se pueden cerrar casos
- Cambios no se persisten

### 8.2. Modo Validate (✅)

**Propósito:** Trabajo con casos reales

**Fuente de Datos:** `DataBase/casos.json`, `personas.json`, `suministros.json`, `documentos.json`

**Capacidades Completas:**
- Edición de información contextual
- Re-clasificación de documentos
- Validación de checklist
- Generación y firma de resoluciones
- Cierre de casos
- Todos los cambios se persisten en la base de datos

