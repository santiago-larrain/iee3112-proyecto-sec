# 🎨 Frontend: Interfaz de Usuario SEC

Aplicación Vue.js 3 que proporciona una interfaz web moderna para que los funcionarios SEC gestionen y analicen reclamos. La aplicación orquesta cuatro secciones principales que interactúan con los motores backend (OMC, MIN, MGR).

## 🏗 Arquitectura de Componentes

### Vista Principal

**`CasoDetalle.vue`** es el componente orquestador que coordina las cuatro secciones:

```
CasoDetalle.vue
├── SeccionA.vue    # Resumen de Contexto (Unified Context)
├── SeccionB.vue    # Gestor Documental (Document Inventory)
├── SeccionC.vue    # Checklist de Validación (MIN Output)
└── SeccionD.vue    # Motor de Resolución (MGR Output)
```

### Componentes Principales

- **`Dashboard.vue`**: Vista de lista con filtros, búsqueda y paginación
- **`CasoDetalle.vue`**: Vista detallada que orquesta las 4 secciones
- **`SeccionA.vue`**: Muestra información unificada del cliente, suministro y caso
- **`SeccionB.vue`**: Gestor documental con re-clasificación y vista previa
- **`SeccionC.vue`**: Checklist interactivo con estados visuales (✅/❌/⚠️)
- **`SeccionD.vue`**: Editor de resoluciones con generación automática
- **`AIChatPanel.vue`**: Panel lateral de asistente IA (colapsable)

## 🔄 Gestión de Estado

### Modos de Operación

La aplicación soporta dos modos que se persisten en `localStorage`:

- **`test`**: Usa datos mock del backend (`mode=test`)
- **`validate`**: Usa datos reales del backend (`mode=validate`)

El modo se puede cambiar desde el botón en el header y se guarda automáticamente.

### Estado Local

- **Vue 3 Composition API**: Para lógica reactiva en componentes
- **Props y Events**: Comunicación padre-hijo entre secciones
- **localStorage**: Persistencia del modo de operación

## 🚀 Instalación

### Pre-requisitos

- **Node.js 18+**
- **npm** o **yarn**

### Pasos

```bash
npm install
```

Esto instalará todas las dependencias definidas en `package.json`:
- Vue.js 3
- Vue Router 4
- Axios
- Vite (build tool)

## ▶️ Ejecución

### Modo Desarrollo

```bash
npm run dev
```

La aplicación estará disponible en `http://localhost:5173` (puerto por defecto de Vite).

### Build de Producción

```bash
npm run build
```

Genera los archivos optimizados en `dist/`.

### Preview de Producción

```bash
npm run preview
```

Sirve la versión de producción localmente para pruebas.

## 🔌 Conexión con el Backend

### Configuración de API

El archivo `src/services/api.js` centraliza todas las llamadas HTTP al backend usando Axios.

La configuración del backend se define en `vite.config.js`:

```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true
    }
  }
}
```

### Endpoints Utilizados

- `GET /api/casos?mode={mode}` - Listar casos
- `GET /api/casos/{case_id}?mode={mode}` - Obtener caso
- `PUT /api/casos/{case_id}/checklist/{item_id}` - Actualizar checklist
- `POST /api/casos/{case_id}/resolucion` - Generar resolución
- `GET /api/casos/{case_id}/documentos/{file_id}/preview` - Vista previa

## 📂 Estructura de Archivos

```
frontend/
├── src/
│   ├── components/
│   │   ├── SeccionA.vue      # Resumen de contexto
│   │   ├── SeccionB.vue      # Gestor documental
│   │   ├── SeccionC.vue      # Checklist
│   │   ├── SeccionD.vue      # Motor de resolución
│   │   ├── Sidebar.vue       # Navegación lateral
│   │   └── AIChatPanel.vue   # Panel de IA
│   ├── views/
│   │   ├── Dashboard.vue     # Vista principal
│   │   └── CasoDetalle.vue  # Vista de caso
│   ├── services/
│   │   └── api.js           # Cliente HTTP
│   ├── App.vue              # Componente raíz
│   └── main.js              # Punto de entrada
├── index.html
├── vite.config.js           # Configuración Vite
└── package.json
```

## 🎯 Flujo de Datos

1. **Dashboard** carga lista de casos desde `/api/casos`
2. Al abrir un caso, **CasoDetalle** carga el caso completo desde `/api/casos/{id}`
3. **SeccionC** muestra el checklist generado por MIN
4. Al validar items, se actualiza el checklist vía `PUT /api/casos/{id}/checklist/{item_id}`
5. **SeccionD** genera borradores usando `POST /api/casos/{id}/resolucion`
6. **SeccionB** permite re-clasificar documentos, lo que dispara regeneración automática del checklist

## 🎨 Características de UI

- **Responsive Design**: Adaptable a diferentes tamaños de pantalla
- **Estados Visuales**: Colores y emojis para estados del checklist (✅/❌/⚠️)
- **Vista Previa de Documentos**: Integración con visor de PDFs
- **Panel IA Colapsable**: Chat lateral que se puede mostrar/ocultar
- **Modo Toggle**: Cambio rápido entre modos test/validate

## 🛠 Tecnologías

- **Vue.js 3.3+** - Framework principal
- **Vite 5.0+** - Build tool y dev server
- **Vue Router 4** - Enrutamiento SPA
- **Axios 1.6+** - Cliente HTTP
- **CSS3** - Estilos personalizados (sin frameworks CSS)

## 📚 Documentación Adicional

- [Manual de Arquitectura](../../docs/manual_tecnico/7_Checklist.md) - Detalles del Checklist UI
- [Documentación Técnica](../../docs/full-stack/frontend.md) - Implementación detallada
- [Vue.js Docs](https://vuejs.org/) - Documentación oficial
- [Vite Docs](https://vitejs.dev/) - Documentación de Vite

