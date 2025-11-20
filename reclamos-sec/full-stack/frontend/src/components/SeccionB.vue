<template>
  <div class="seccion-b">
    <h3>Sección B: Gestor Documental Inteligente</h3>
    
    <!-- Nivel 1: Críticos -->
    <div class="document-group" v-if="documentInventory.level_1_critical.length > 0">
      <h4 class="group-title critical">
        📌 Nivel 1: Documentos Críticos
      </h4>
      <div class="documents-list">
        <div 
          v-for="doc in documentInventory.level_1_critical" 
          :key="doc.file_id"
          class="document-item"
        >
          <div class="doc-info">
            <span class="doc-icon">📄</span>
            <div class="doc-details">
              <div class="doc-name">{{ doc.standardized_name || doc.original_name }}</div>
              <div class="doc-original">Original: {{ doc.original_name }}</div>
            </div>
          </div>
          <div class="doc-actions">
            <select 
              :value="doc.type" 
              @change="actualizarTipoDocumento(doc.file_id, $event.target.value, doc)"
              class="type-select"
            >
              <option value="CARTA_RESPUESTA">Carta de Respuesta</option>
              <option value="ORDEN_TRABAJO">Orden de Trabajo</option>
              <option value="TABLA_CALCULO">Tabla de Cálculo</option>
              <option value="EVIDENCIA_FOTOGRAFICA">Evidencia Fotográfica</option>
              <option value="GRAFICO_CONSUMO">Gráfico de Consumo</option>
              <option value="OTROS">Otros</option>
            </select>
            <button @click="verDocumento(doc)" class="btn-view">Ver</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Nivel 2: Soportantes -->
    <div class="document-group" v-if="documentInventory.level_2_supporting.length > 0">
      <h4 class="group-title supporting">
        📎 Nivel 2: Documentos Soportantes
      </h4>
      <div class="documents-list">
        <div 
          v-for="doc in documentInventory.level_2_supporting" 
          :key="doc.file_id"
          class="document-item"
        >
          <div class="doc-info">
            <span class="doc-icon">📎</span>
            <div class="doc-details">
              <div class="doc-name">{{ doc.standardized_name || doc.original_name }}</div>
              <div class="doc-original">Original: {{ doc.original_name }}</div>
            </div>
          </div>
          <div class="doc-actions">
            <select 
              :value="doc.type" 
              @change="actualizarTipoDocumento(doc.file_id, $event.target.value, doc)"
              class="type-select"
            >
              <option value="CARTA_RESPUESTA">Carta de Respuesta</option>
              <option value="ORDEN_TRABAJO">Orden de Trabajo</option>
              <option value="TABLA_CALCULO">Tabla de Cálculo</option>
              <option value="EVIDENCIA_FOTOGRAFICA">Evidencia Fotográfica</option>
              <option value="GRAFICO_CONSUMO">Gráfico de Consumo</option>
              <option value="OTROS">Otros</option>
            </select>
            <button @click="verDocumento(doc)" class="btn-view">Ver</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Nivel 0: Ausentes -->
    <div class="document-group" v-if="documentInventory.level_0_missing.length > 0">
      <h4 class="group-title missing">
        ⚠️ Nivel 0: Documentos Ausentes
      </h4>
      <div class="documents-list">
        <div 
          v-for="missing in documentInventory.level_0_missing" 
          :key="missing.required_type"
          class="document-item missing-item"
        >
          <div class="doc-info">
            <span class="doc-icon">❌</span>
            <div class="doc-details">
              <div class="doc-name">{{ missing.required_type }}</div>
              <div class="doc-original">{{ missing.description }}</div>
            </div>
          </div>
          <div class="alert-level">
            <span :class="['alert-badge', `alert-${missing.alert_level.toLowerCase()}`]">
              {{ missing.alert_level }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal Visor de Documento -->
    <div v-if="documentoSeleccionado" class="modal-overlay" @click="cerrarVisor">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h4>{{ documentoSeleccionado.standardized_name || documentoSeleccionado.original_name }}</h4>
          <button @click="cerrarVisor" class="btn-close">×</button>
        </div>
        <div class="modal-body">
          <div class="document-preview">
            <!-- Loading state -->
            <div v-if="loadingDocument" class="loading-state">
              <p>Cargando documento...</p>
            </div>
            
            <!-- Error state -->
            <div v-if="documentError" class="error-state">
              <p>❌ Error al cargar el documento: {{ documentError }}</p>
              <button @click="cargarDocumento" class="btn-retry">Reintentar</button>
            </div>
            
            <!-- PDF Viewer -->
            <iframe
              v-if="documentUrl && !loadingDocument && !documentError && isPdf"
              :src="documentUrl"
              class="pdf-viewer"
              frameborder="0"
            ></iframe>
            
            <!-- Image Viewer -->
            <img
              v-if="documentUrl && !loadingDocument && !documentError && isImage"
              :src="documentUrl"
              class="image-viewer"
              alt="Vista previa"
            />
            
            <!-- Fallback para otros tipos -->
            <div v-if="documentUrl && !loadingDocument && !documentError && !isPdf && !isImage" class="other-document">
              <p>📄 Documento: {{ documentoSeleccionado.original_name }}</p>
              <a :href="documentUrl" target="_blank" class="btn-download">
                Descargar Documento
              </a>
            </div>
            
            <!-- Datos extraídos -->
            <div v-if="documentoSeleccionado.extracted_data" class="extracted-data">
              <h5>Datos Extraídos:</h5>
              <pre>{{ JSON.stringify(documentoSeleccionado.extracted_data, null, 2) }}</pre>
            </div>
            
            <!-- Metadatos -->
            <div v-if="documentoSeleccionado.metadata" class="extracted-data">
              <h5>Metadatos:</h5>
              <pre>{{ JSON.stringify(documentoSeleccionado.metadata, null, 2) }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SeccionB',
  inject: ['actualizarDocumento'],
  props: {
    documentInventory: {
      type: Object,
      required: true
    },
    caseId: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      documentoSeleccionado: null,
      documentUrl: null,
      loadingDocument: false,
      documentError: null,
      editingDocumentName: null,
      customNameInput: ''
    }
  },
  computed: {
    isPdf() {
      if (!this.documentoSeleccionado) return false
      const name = this.documentoSeleccionado.original_name || ''
      return name.toLowerCase().endsWith('.pdf')
    },
    isImage() {
      if (!this.documentoSeleccionado) return false
      const name = this.documentoSeleccionado.original_name || ''
      const ext = name.toLowerCase().split('.').pop()
      return ['jpg', 'jpeg', 'png', 'gif'].includes(ext)
    }
  },
  watch: {
    documentoSeleccionado(newDoc) {
      if (newDoc) {
        this.cargarDocumento()
      } else {
        this.documentUrl = null
        this.documentError = null
      }
    }
  },
  methods: {
    async actualizarTipoDocumento(fileId, nuevoTipo, doc) {
      // Preguntar si quiere personalizar el nombre
      const tipoNombres = {
        'CARTA_RESPUESTA': 'Carta de Respuesta',
        'ORDEN_TRABAJO': 'Orden de Trabajo',
        'TABLA_CALCULO': 'Tabla de Cálculo',
        'EVIDENCIA_FOTOGRAFICA': 'Evidencia Fotográfica',
        'GRAFICO_CONSUMO': 'Gráfico de Consumo',
        'OTROS': 'Otros'
      }
      
      const nombreDefault = `${tipoNombres[nuevoTipo]} - ${doc.original_name}`
      const customName = prompt(
        `¿Desea personalizar el nombre del documento?\n\nNombre por defecto: ${nombreDefault}\n\n(Deje vacío para usar el nombre por defecto)`,
        doc.standardized_name || nombreDefault
      )
      
      try {
        const response = await this.actualizarDocumento(
          this.caseId, 
          fileId, 
          nuevoTipo,
          customName && customName.trim() ? customName.trim() : null
        )
        // Emitir evento para actualizar checklist
        this.$emit('documento-actualizado', response.data)
        alert('Documento actualizado y guardado en la base de datos. El checklist se ha recalculado automáticamente.')
      } catch (error) {
        console.error('Error al actualizar documento:', error)
        alert('Error al actualizar el tipo de documento')
      }
    },
    verDocumento(doc) {
      this.documentoSeleccionado = doc
    },
    cerrarVisor() {
      this.documentoSeleccionado = null
      this.documentUrl = null
      this.documentError = null
    },
    async cargarDocumento() {
      if (!this.documentoSeleccionado) return
      
      this.loadingDocument = true
      this.documentError = null
      
      try {
        // Construir URL del endpoint de preview
        const fileId = this.documentoSeleccionado.file_id
        const apiUrl = `http://localhost:8000/api/casos/${this.caseId}/documentos/${fileId}/preview`
        
        // Para PDFs e imágenes, usar directamente la URL
        this.documentUrl = apiUrl
        this.loadingDocument = false
      } catch (error) {
        console.error('Error cargando documento:', error)
        this.documentError = error.message || 'Error desconocido'
        this.loadingDocument = false
      }
    }
  }
}
</script>

<style scoped>
.seccion-b {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.seccion-b h3 {
  margin-bottom: 1.5rem;
  color: #333;
  font-size: 1.5rem;
  border-bottom: 2px solid #667eea;
  padding-bottom: 0.5rem;
}

.document-group {
  margin-bottom: 2rem;
}

.group-title {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 1rem;
  padding: 0.75rem;
  border-radius: 4px;
}

.group-title.critical {
  background: #ffebee;
  color: #c62828;
}

.group-title.supporting {
  background: #e3f2fd;
  color: #1565c0;
}

.group-title.missing {
  background: #fff3e0;
  color: #e65100;
}

.documents-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.document-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background: #fafafa;
  transition: all 0.2s;
}

.document-item:hover {
  background: #f5f5f5;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.document-item.missing-item {
  background: #fff3e0;
  border-color: #ff9800;
}

.doc-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex: 1;
}

.doc-icon {
  font-size: 1.5rem;
}

.doc-details {
  flex: 1;
}

.doc-name {
  font-weight: 600;
  color: #333;
  margin-bottom: 0.25rem;
}

.doc-original {
  font-size: 0.85rem;
  color: #666;
}

.doc-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.type-select {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
  background: white;
  cursor: pointer;
}

.btn-view {
  background: #667eea;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background 0.2s;
}

.btn-view:hover {
  background: #5568d3;
}

.alert-level {
  display: flex;
  align-items: center;
}

.alert-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 500;
}

.alert-high {
  background: #ffcdd2;
  color: #c62828;
}

.alert-medium {
  background: #ffe0b2;
  color: #e65100;
}

.alert-low {
  background: #fff9c4;
  color: #f57f17;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 95%;
  max-width: 1200px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}

.modal-header {
  padding: 1.5rem;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h4 {
  margin: 0;
  color: #333;
}

.btn-close {
  background: none;
  border: none;
  font-size: 2rem;
  color: #666;
  cursor: pointer;
  line-height: 1;
  padding: 0;
  width: 30px;
  height: 30px;
}

.btn-close:hover {
  color: #333;
}

.modal-body {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
}

.document-preview {
  min-height: 400px;
  display: flex;
  flex-direction: column;
}

.loading-state,
.error-state {
  text-align: center;
  padding: 4rem 2rem;
  color: #666;
  font-size: 1.1rem;
}

.error-state {
  color: #d32f2f;
}

.btn-retry {
  margin-top: 1rem;
  padding: 0.5rem 1rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-retry:hover {
  background: #5568d3;
}

.pdf-viewer {
  width: 100%;
  height: 70vh;
  min-height: 500px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.image-viewer {
  max-width: 100%;
  max-height: 70vh;
  margin: 0 auto;
  display: block;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.other-document {
  text-align: center;
  padding: 4rem 2rem;
  color: #666;
}

.btn-download {
  display: inline-block;
  margin-top: 1rem;
  padding: 0.75rem 1.5rem;
  background: #667eea;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  font-weight: 500;
  transition: background 0.2s;
}

.btn-download:hover {
  background: #5568d3;
}

.extracted-data {
  margin-top: 2rem;
  padding: 1rem;
  background: #f5f5f5;
  border-radius: 4px;
}

.extracted-data h5 {
  margin-bottom: 0.75rem;
  color: #333;
}

.extracted-data pre {
  background: white;
  padding: 1rem;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 0.85rem;
}
</style>

