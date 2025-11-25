import axios from 'axios'

// Función para obtener el modo actual desde localStorage o default
function getMode() {
  return localStorage.getItem('app_mode') || 'validate'
}

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json'
  }
})

// Interceptor para agregar el header del modo en cada request
api.interceptors.request.use(config => {
  const mode = getMode()
  config.headers['X-App-Mode'] = mode
  // También agregar como query param para compatibilidad
  if (config.params) {
    config.params.mode = mode
  } else {
    config.params = { mode }
  }
  return config
})

export const casosAPI = {
  // Obtener lista de casos con búsqueda, filtrado, ordenamiento y paginación
  getCasos: (searchQuery = '', tipoCaso = '', estado = '', sortBy = null, sortOrder = 'asc', page = 1, pageSize = 100) => {
    const mode = getMode()
    const params = { 
      mode, 
      page: page || 1, 
      page_size: pageSize || 100 
    }
    if (searchQuery && searchQuery.trim()) {
      params.q = searchQuery.trim()
    }
    if (tipoCaso && tipoCaso.trim()) {
      params.tipo_caso = tipoCaso.trim()
    }
    if (estado && estado.trim()) {
      params.estado = estado.trim()
    }
    if (sortBy && sortBy.trim()) {
      params.sort_by = sortBy.trim()
      params.sort_order = (sortOrder || 'asc').toLowerCase()
    }
    return api.get('/casos', { params })
  },
  
  // Buscar casos
  searchCasos: (query) => {
    const mode = getMode()
    return api.get('/casos/search', { params: { q: query, mode } })
  },
  
  // Obtener caso por ID
  getCaso: (caseId) => {
    const mode = getMode()
    return api.get(`/casos/${caseId}`, { params: { mode } })
  },
  
  // Actualizar tipo de documento
  updateDocumento: (caseId, fileId, tipo, customName = null) => {
    const body = { type: tipo }
    if (customName) {
      body.custom_name = customName
    }
    return api.put(`/casos/${caseId}/documentos/${fileId}`, body)
  },
  
  // Actualizar item del checklist
  updateChecklistItem: (caseId, itemId, validated) =>
    api.put(`/casos/${caseId}/checklist/${itemId}`, { validated }),
  
  // Generar resolución
  generarResolucion: (caseId, templateType, content) =>
    api.post(`/casos/${caseId}/resolucion`, { 
      template_type: templateType,
      content 
    }),
  
  // Actualizar contexto unificado y campos del caso
  updateUnifiedContext: (caseId, updates) =>
    api.put(`/casos/${caseId}/contexto`, updates),
  
  // Previsualizar PDF de resolución
  previewResolucionPDF: (caseId, resolucionContent) => {
    const mode = getMode()
    return api.post(`/casos/${caseId}/resolucion/pdf-preview`, {
      template_type: 'INSTRUCCION', // No importa para preview
      content: resolucionContent
    }, {
      params: { mode },
      responseType: 'blob'
    })
  },
  
  // Cerrar caso
  cerrarCaso: (caseId, resolucionContent) =>
    api.post(`/casos/${caseId}/cerrar`, {
      resolucion_content: resolucionContent,
      fecha_cierre: new Date().toISOString()
    })
}

export default api

