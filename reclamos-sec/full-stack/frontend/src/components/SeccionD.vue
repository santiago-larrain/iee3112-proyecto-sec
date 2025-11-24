<template>
  <div class="seccion-d">
    <h3>Sección D: Motor de Resolución y Respuesta</h3>
    
    <div class="template-selector">
      <label>Tipo de Resolución:</label>
      <select v-model="templateType" @change="onTemplateChange">
        <option value="INSTRUCCION">Instrucción a la Empresa</option>
        <option value="IMPROCEDENTE">Improcedente</option>
      </select>
      <button @click="generarBorrador" class="btn-generate">Generar Borrador</button>
    </div>

    <div class="editor-container">
      <label>Editor de Resolución:</label>
      <textarea 
        v-model="resolucionContent"
        class="resolucion-editor"
        placeholder="El borrador se generará automáticamente..."
        rows="15"
      ></textarea>
    </div>

    <div class="actions">
      <button 
        @click="exportarYFirmar" 
        class="btn-export"
        :disabled="cerrando || !resolucionContent || resolucionContent.trim() === ''"
      >
        {{ cerrando ? '⏳ Procesando...' : '📄 Exportar y Firmar' }}
      </button>
    </div>

    <!-- Modal de previsualización del PDF -->
    <div v-if="mostrarPreview" class="modal-overlay" @click="cerrarPreview">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h4>Previsualización de Resolución</h4>
          <button @click="cerrarPreview" class="btn-close">×</button>
        </div>
        <div class="modal-body">
          <div class="pdf-preview-container">
            <div v-if="loadingPDF" class="loading-state">
              <p>Generando PDF...</p>
            </div>
            <div v-if="pdfError" class="error-state">
              <p>❌ Error al generar PDF: {{ pdfError }}</p>
              <button @click="generarPDFPreview" class="btn-retry">Reintentar</button>
            </div>
            <iframe
              v-if="pdfUrl && !loadingPDF && !pdfError"
              :src="pdfUrl"
              class="pdf-preview"
              frameborder="0"
            ></iframe>
          </div>
          <div class="modal-actions">
            <button @click="cerrarPreview" class="btn-cancel">Cancelar</button>
            <button @click="confirmarFirma" class="btn-confirm" :disabled="firmando">
              {{ firmando ? '⏳ Firmando...' : '✍️ Firmar y Cerrar Caso' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { casosAPI } from '../services/api'

export default {
  name: 'SeccionD',
  inject: ['generarResolucion'],
  props: {
    caseId: {
      type: String,
      required: true
    },
    checklist: {
      type: Object,
      default: () => ({
        client_information: [],
        evidence_review: [],
        legal_compliance: []
      })
    }
  },
  data() {
    return {
      templateType: 'INSTRUCCION',
      resolucionContent: '',
      cerrando: false,
      mostrarPreview: false,
      pdfUrl: null,
      loadingPDF: false,
      pdfError: null,
      firmando: false
    }
  },
  methods: {
    onTemplateChange() {
      // Cuando cambia el tipo de resolución, generar nuevo borrador automáticamente
      this.generarBorrador()
    },
    async generarBorrador() {
      try {
        // Limpiar el contenido existente antes de generar un nuevo borrador
        // No pasar el contenido actual para que el backend genere uno nuevo desde cero
        const response = await this.generarResolucion(
          this.caseId,
          this.templateType,
          null  // No pasar contenido existente, generar borrador nuevo
        )
        // Reemplazar completamente el contenido con el nuevo borrador
        this.resolucionContent = response.data.borrador
      } catch (error) {
        console.error('Error al generar borrador:', error)
        alert('Error al generar el borrador')
      }
    },
    async exportarYFirmar() {
      if (!this.resolucionContent || this.resolucionContent.trim() === '') {
        alert('Por favor, genere o edite la resolución antes de exportar.')
        return
      }
      
      // Mostrar modal de previsualización
      this.mostrarPreview = true
      this.generarPDFPreview()
    },
    async generarPDFPreview() {
      this.loadingPDF = true
      this.pdfError = null
      
      try {
        const response = await casosAPI.previewResolucionPDF(this.caseId, this.resolucionContent)
        // Crear URL del blob
        const blob = new Blob([response.data], { type: 'application/pdf' })
        this.pdfUrl = URL.createObjectURL(blob)
        this.loadingPDF = false
      } catch (error) {
        console.error('Error generando PDF preview:', error)
        this.pdfError = error.response?.data?.detail || error.message || 'Error desconocido'
        this.loadingPDF = false
      }
    },
    cerrarPreview() {
      this.mostrarPreview = false
      if (this.pdfUrl) {
        URL.revokeObjectURL(this.pdfUrl)
        this.pdfUrl = null
      }
      this.pdfError = null
    },
    async confirmarFirma() {
      if (!confirm('¿Está seguro de que desea firmar y cerrar este caso?\n\nUna vez cerrado, el caso cambiará su estado a CERRADO y no podrá ser modificado.')) {
        return
      }
      
      this.firmando = true
      try {
        await casosAPI.cerrarCaso(this.caseId, this.resolucionContent)
        alert('✅ Caso firmado y cerrado exitosamente. El estado ha sido actualizado a CERRADO.')
        // Cerrar preview
        this.cerrarPreview()
        // Redirigir al dashboard
        this.$router.push('/')
      } catch (error) {
        console.error('Error al firmar caso:', error)
        const errorMsg = error.response?.data?.detail || error.message || 'Error desconocido'
        alert('Error al firmar el caso: ' + errorMsg)
      } finally {
        this.firmando = false
      }
    }
  },
  mounted() {
    // Auto-generar borrador al cargar
    this.generarBorrador()
  },
  beforeUnmount() {
    // Limpiar URL del blob si existe
    if (this.pdfUrl) {
      URL.revokeObjectURL(this.pdfUrl)
    }
  }
}
</script>

<style scoped>
.seccion-d {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.seccion-d h3 {
  margin-bottom: 1.5rem;
  color: #333;
  font-size: 1.5rem;
  border-bottom: 2px solid #667eea;
  padding-bottom: 0.5rem;
}

.template-selector {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: #f5f5f5;
  border-radius: 6px;
}

.template-selector label {
  font-weight: 600;
  color: #333;
}

.template-selector select {
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  background: white;
  flex: 1;
}

.btn-generate {
  background: #667eea;
  color: white;
  border: none;
  padding: 0.5rem 1.5rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background 0.2s;
}

.btn-generate:hover {
  background: #5568d3;
}

.editor-container {
  margin-bottom: 1.5rem;
}

.editor-container label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #333;
}

.resolucion-editor {
  width: 100%;
  padding: 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  font-family: inherit;
  line-height: 1.6;
  resize: vertical;
}

.actions {
  display: flex;
  justify-content: flex-end;
}

.btn-export {
  background: #4caf50;
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 600;
  transition: background 0.2s;
}

.btn-export:hover:not(:disabled) {
  background: #45a049;
}

.btn-export:disabled {
  background: #cccccc;
  cursor: not-allowed;
  opacity: 0.6;
}

/* Modal de previsualización */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
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
  font-size: 1.3rem;
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
  display: flex;
  flex-direction: column;
}

.pdf-preview-container {
  flex: 1;
  min-height: 500px;
  margin-bottom: 1.5rem;
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

.pdf-preview {
  width: 100%;
  height: 70vh;
  min-height: 500px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e0e0e0;
}

.btn-cancel {
  background: #f5f5f5;
  color: #333;
  border: 1px solid #ddd;
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  transition: background 0.2s;
}

.btn-cancel:hover {
  background: #e0e0e0;
}

.btn-confirm {
  background: #4caf50;
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 600;
  transition: background 0.2s;
}

.btn-confirm:hover:not(:disabled) {
  background: #45a049;
}

.btn-confirm:disabled {
  background: #cccccc;
  cursor: not-allowed;
  opacity: 0.6;
}
</style>
