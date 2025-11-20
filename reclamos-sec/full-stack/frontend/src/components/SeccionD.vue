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
        @click="firmarYCerrar" 
        class="btn-sign"
        :disabled="cerrando"
      >
        {{ cerrando ? '⏳ Cerrando...' : '✍️ Firmar y Cerrar Caso' }}
      </button>
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
      cerrando: false
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
    async firmarYCerrar() {
      if (!this.resolucionContent || this.resolucionContent.trim() === '') {
        alert('Por favor, genere o edite la resolución antes de cerrar el caso.')
        return
      }
      
      if (!confirm('¿Está seguro de que desea firmar y cerrar este caso?\n\nUna vez cerrado, el caso cambiará su estado a CERRADO y no podrá ser modificado.')) {
        return
      }
      
      this.cerrando = true
      try {
        await casosAPI.cerrarCaso(this.caseId, this.resolucionContent)
        alert('✅ Caso firmado y cerrado exitosamente. El estado ha sido actualizado a CERRADO.')
        // Redirigir al dashboard
        this.$router.push('/')
      } catch (error) {
        console.error('Error al firmar caso:', error)
        const errorMsg = error.response?.data?.detail || error.message || 'Error desconocido'
        alert('Error al firmar el caso: ' + errorMsg)
      } finally {
        this.cerrando = false
      }
    }
  },
  mounted() {
    // Auto-generar borrador al cargar
    this.generarBorrador()
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

.btn-sign {
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

.btn-sign:hover:not(:disabled) {
  background: #45a049;
}

.btn-sign:disabled {
  background: #cccccc;
  cursor: not-allowed;
  opacity: 0.6;
}
</style>

