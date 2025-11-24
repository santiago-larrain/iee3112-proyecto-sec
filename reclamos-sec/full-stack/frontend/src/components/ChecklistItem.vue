<template>
  <div 
    class="checklist-item"
    :class="getStatusClass(item.status)"
  >
    <div class="item-header" @click="toggleExpand">
      <div class="item-left">
        <span class="status-icon">{{ getStatusIcon(item.status) }}</span>
        <span class="item-id">{{ item.id }}</span>
        <span class="item-title">{{ item.title }}</span>
      </div>
      <div class="item-right">
        <label class="checkbox-label">
          <input 
            type="checkbox" 
            :checked="item.validated"
            @change="handleValidationChange"
            @click.stop
          />
          <span>Validado</span>
        </label>
        <span class="expand-icon">{{ isExpanded ? '▼' : '▶' }}</span>
      </div>
    </div>
    <div v-if="isExpanded" class="item-details">
      <!-- Sección 1: Descripción (texto estático) -->
      <div class="description-section" v-if="item.description">
        <strong>📋 Descripción:</strong>
        <p>{{ item.description }}</p>
      </div>
      
      <!-- Sección 2: Evidencia Identificada (resultado de regla) -->
      <div class="evidence-section" v-if="item.evidence">
        <strong>🔍 Evidencia Identificada:</strong>
        <p v-html="formatEvidence(item.evidence)"></p>
      </div>
      
      <!-- Sección 3: Datos/Contexto (deep linking a archivos) -->
      <div class="data-section" v-if="item.evidence_data">
        <strong>📎 Datos/Contexto:</strong>
        <div class="data-links">
          <div v-if="item.evidence_data.file_id" class="data-link-item">
            <button 
              @click="openDocument(item.evidence_data.file_id, item.evidence_data.page_index)"
              class="btn-open-doc"
            >
              📄 Abrir Documento
              <span v-if="item.evidence_data.page_index !== null && item.evidence_data.page_index !== undefined">
                (Página {{ item.evidence_data.page_index + 1 }})
              </span>
            </button>
            <span v-if="item.evidence_data.coordinates" class="coordinates-info">
              Coordenadas: {{ formatCoordinates(item.evidence_data.coordinates) }}
            </span>
          </div>
          <div v-else-if="item.evidence_data.file_ids" class="data-link-item">
            <div v-for="(fileId, idx) in item.evidence_data.file_ids" :key="idx" class="file-link">
              <button @click="openDocument(fileId)" class="btn-open-doc">
                📄 Documento {{ idx + 1 }}
              </button>
            </div>
            <span v-if="item.evidence_data.count" class="count-info">
              Total: {{ item.evidence_data.count }} archivo(s)
            </span>
          </div>
          <div v-else class="data-placeholder">
            <p>No hay referencias de archivos disponibles</p>
          </div>
        </div>
      </div>
      
      <div class="evidence-type" v-if="item.evidence_type">
        <span class="type-badge">
          {{ item.evidence_type === 'dato' ? '📊 Dato' : '📄 Archivo' }}
        </span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ChecklistItem',
  inject: ['actualizarChecklistItem'],
  props: {
    item: {
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
      isExpanded: false
    }
  },
  methods: {
    toggleExpand() {
      this.isExpanded = !this.isExpanded
    },
    getStatusIcon(status) {
      const icons = {
        'CUMPLE': '✅',
        'NO_CUMPLE': '❌',
        'REVISION_MANUAL': '⚠️'
      }
      return icons[status] || '❓'
    },
    getStatusClass(status) {
      const classes = {
        'CUMPLE': 'status-cumple',
        'NO_CUMPLE': 'status-no-cumple',
        'REVISION_MANUAL': 'status-revision'
      }
      return classes[status] || ''
    },
    formatEvidence(evidence) {
      // Formatear evidencia con negritas para texto entre **
      return evidence.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    },
    formatCoordinates(coords) {
      if (!coords || !Array.isArray(coords)) return 'N/A'
      if (coords.length >= 4) {
        return `[${coords[0].toFixed(0)}, ${coords[1].toFixed(0)}, ${coords[2].toFixed(0)}, ${coords[3].toFixed(0)}]`
      }
      return JSON.stringify(coords)
    },
    async openDocument(fileId, pageIndex = null) {
      // Abrir documento en nueva pestaña o modal
      const url = `/api/casos/${this.caseId}/documentos/${fileId}/preview`
      if (pageIndex !== null && pageIndex !== undefined) {
        // Si hay página específica, agregar como parámetro (el backend puede usarlo en el futuro)
        window.open(`${url}?page=${pageIndex}`, '_blank')
      } else {
        window.open(url, '_blank')
      }
    },
    async handleValidationChange(event) {
      const validated = event.target.checked
      try {
        await this.actualizarChecklistItem(this.caseId, this.item.id, validated)
        this.$emit('item-validated')
      } catch (error) {
        console.error('Error al actualizar validación:', error)
        // Revertir checkbox si falla
        event.target.checked = !validated
        alert('Error al actualizar la validación: ' + (error.response?.data?.detail || error.message || 'Error desconocido'))
      }
    }
  }
}
</script>

<style scoped>
.checklist-item {
  border: 2px solid #e0e0e0;
  border-radius: 6px;
  overflow: hidden;
  transition: all 0.2s;
  background: white;
}

.checklist-item.status-cumple {
  border-color: #4caf50;
  background: #f1f8e9;
}

.checklist-item.status-no-cumple {
  border-color: #f44336;
  background: #ffebee;
}

.checklist-item.status-revision {
  border-color: #ff9800;
  background: #fff3e0;
}

.item-header {
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  transition: background 0.2s;
}

.item-header:hover {
  background: rgba(0,0,0,0.05);
}

.item-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex: 1;
}

.status-icon {
  font-size: 1.25rem;
}

.item-id {
  font-weight: 600;
  color: #667eea;
  font-size: 0.9rem;
  min-width: 50px;
}

.item-title {
  font-weight: 600;
  color: #333;
  font-size: 1rem;
}

.item-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.9rem;
  color: #666;
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.expand-icon {
  color: #666;
  font-size: 0.85rem;
  user-select: none;
}

.item-details {
  padding: 1rem;
  padding-top: 0;
  border-top: 1px solid rgba(0,0,0,0.1);
  background: white;
}

.evidence-section,
.description-section,
.data-section {
  margin-bottom: 1.5rem;
}

.evidence-section strong,
.description-section strong,
.data-section strong {
  display: block;
  margin-bottom: 0.75rem;
  color: #333;
  font-size: 0.95rem;
  font-weight: 600;
}

.evidence-section p,
.description-section p {
  margin: 0;
  color: #666;
  line-height: 1.5;
  padding: 0.75rem;
  background: #f5f5f5;
  border-radius: 4px;
}

.data-links {
  padding: 0.75rem;
  background: #f5f5f5;
  border-radius: 4px;
}

.data-link-item {
  margin-bottom: 0.5rem;
}

.file-link {
  margin-bottom: 0.5rem;
}

.btn-open-doc {
  background: #667eea;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: background 0.2s;
  margin-right: 0.5rem;
}

.btn-open-doc:hover {
  background: #5568d3;
}

.coordinates-info,
.count-info {
  display: block;
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: #666;
  font-style: italic;
}

.data-placeholder {
  padding: 0.5rem;
  color: #999;
  font-style: italic;
}

.evidence-type {
  margin-top: 0.75rem;
}

.type-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  background: #e3f2fd;
  color: #1565c0;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 500;
}
</style>

