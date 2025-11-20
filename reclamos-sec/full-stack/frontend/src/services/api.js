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
  // Obtener lista de casos
  getCasos: () => {
    const mode = getMode()
    return api.get('/casos', { params: { mode } })
  },
  
  // Obtener caso por ID
  getCaso: (caseId) => {
    const mode = getMode()
    return api.get(`/casos/${caseId}`, { params: { mode } })
  },
  
  // Actualizar tipo de documento
  updateDocumento: (caseId, fileId, tipo) => 
    api.put(`/casos/${caseId}/documentos/${fileId}`, { type: tipo }),
  
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
  
  // Cerrar caso
  cerrarCaso: (caseId, resolucionContent) =>
    api.post(`/casos/${caseId}/cerrar`, {
      resolucion_content: resolucionContent,
      fecha_cierre: new Date().toISOString()
    })
}

export default api

