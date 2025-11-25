<template>
  <div class="seccion-a">
    <div class="section-header">
      <h3>Sección A: Resumen de Contexto</h3>
      <button 
        @click="toggleEditMode" 
        :class="['btn-edit', isEditing ? 'btn-save' : '']"
      >
        {{ isEditing ? '💾 Guardar' : '✏️ Editar' }}
      </button>
    </div>
    
    <div class="cards-grid">
      <!-- Tarjeta Cliente -->
      <div class="context-card">
        <div class="card-header">
          <span class="card-icon">👤</span>
          <h4>Cliente</h4>
        </div>
        <div class="card-body">
          <div class="info-item">
            <span class="label">Nombre:</span>
            <input 
              v-if="isEditing" 
              v-model="editedContext.client_name" 
              class="edit-input"
              placeholder="Nombre del cliente"
            />
            <span v-else class="value">{{ unifiedContext.client_name || '—' }}</span>
          </div>
          <div class="info-item">
            <span class="label">RUT:</span>
            <input 
              v-if="isEditing" 
              v-model="editedContext.rut_client" 
              class="edit-input"
              placeholder="RUT del cliente"
            />
            <span v-else class="value">{{ unifiedContext.rut_client || '—' }}</span>
          </div>
          <div class="info-item">
            <span class="label">Email:</span>
            <input 
              v-if="isEditing" 
              v-model="editedContext.email" 
              class="edit-input"
              type="email"
              placeholder="Email del cliente"
            />
            <span v-else class="value">{{ unifiedContext.email || '—' }}</span>
          </div>
          <div class="info-item">
            <span class="label">Teléfono:</span>
            <input 
              v-if="isEditing" 
              v-model="editedContext.phone" 
              class="edit-input"
              placeholder="Teléfono del cliente"
            />
            <span v-else class="value">{{ unifiedContext.phone || '—' }}</span>
          </div>
        </div>
      </div>

      <!-- Tarjeta Suministro -->
      <div class="context-card">
        <div class="card-header">
          <span class="card-icon">🏠</span>
          <h4>Suministro</h4>
        </div>
        <div class="card-body">
          <div class="info-item">
            <span class="label">Dirección:</span>
            <input 
              v-if="isEditing" 
              v-model="editedContext.address_standard" 
              class="edit-input"
              placeholder="Dirección del suministro"
            />
            <span v-else class="value">{{ unifiedContext.address_standard || '—' }}</span>
          </div>
          <div class="info-item">
            <span class="label">Comuna:</span>
            <input 
              v-if="isEditing" 
              v-model="editedContext.commune" 
              class="edit-input"
              placeholder="Comuna"
            />
            <span v-else class="value">{{ unifiedContext.commune || '—' }}</span>
          </div>
          <div class="info-item">
            <span class="label">N° Cliente/NIS:</span>
            <input 
              v-if="isEditing" 
              v-model="editedContext.service_nis" 
              class="edit-input"
              placeholder="NIS o N° Cliente"
            />
            <span v-else class="value">{{ unifiedContext.service_nis || '—' }}</span>
          </div>
        </div>
      </div>

      <!-- Tarjeta Caso -->
      <div class="context-card">
        <div class="card-header">
          <span class="card-icon">📋</span>
          <h4>Caso</h4>
        </div>
        <div class="card-body">
          <div class="info-item">
            <span class="label">ID SEC:</span>
            <span class="value">{{ compilationMetadata.case_id }}</span>
          </div>
          <div class="info-item">
            <span class="label">Materia:</span>
            <input 
              v-if="isEditing" 
              v-model="editedMateria" 
              class="edit-input"
              placeholder="Materia del caso"
            />
            <span v-else class="value">{{ materia && materia !== '—' ? materia : '—' }}</span>
          </div>
          <div class="info-item">
            <span class="label">Monto en Disputa:</span>
            <input 
              v-if="isEditing" 
              v-model.number="editedMontoDisputa" 
              class="edit-input"
              type="number"
              placeholder="0"
            />
            <span v-else class="value amount">{{ montoDisputa && montoDisputa !== '—' ? '$' + Number(montoDisputa).toLocaleString('es-CL') : '—' }}</span>
          </div>
          <div class="info-item">
            <span class="label">Empresa:</span>
            <input 
              v-if="isEditing" 
              v-model="editedEmpresa" 
              class="edit-input"
              placeholder="Nombre de la empresa"
            />
            <span v-else class="value">{{ empresa && empresa !== '—' ? empresa : '—' }}</span>
          </div>
          <div class="info-item">
            <span class="label">Fecha Ingreso:</span>
            <input 
              v-if="isEditing" 
              v-model="editedFechaIngreso" 
              class="edit-input"
              type="date"
            />
            <span v-else class="value">{{ fechaIngreso && fechaIngreso !== '—' ? fechaIngreso : '—' }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Indicadores de Alerta -->
    <div class="alertas" v-if="alertas && alertas.length > 0">
      <h4>Indicadores de Alerta</h4>
      <div class="badges-container">
        <span v-for="alerta in alertas" :key="alerta" class="alerta-badge">
          {{ alerta }}
        </span>
      </div>
    </div>
  </div>
</template>

<script>
import { casosAPI } from '../services/api'

export default {
  name: 'SeccionA',
  inject: ['caseId'],
  props: {
    unifiedContext: {
      type: Object,
      required: true
    },
    compilationMetadata: {
      type: Object,
      required: true
    },
    materia: {
      type: String,
      default: ''
    },
    montoDisputa: {
      type: Number,
      default: 0
    },
    empresa: {
      type: String,
      default: ''
    },
    fechaIngreso: {
      type: String,
      default: ''
    },
    alertas: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      isEditing: false,
      editedContext: {},
      editedMateria: '',
      editedMontoDisputa: null,
      editedEmpresa: '',
      editedFechaIngreso: '',
      saving: false
    }
  },
  methods: {
    toggleEditMode() {
      if (this.isEditing) {
        this.guardarCambios()
      } else {
        this.entrarModoEdicion()
      }
    },
    entrarModoEdicion() {
      // Copiar valores actuales a los campos de edición
      this.editedContext = {
        client_name: this.unifiedContext.client_name || '',
        rut_client: this.unifiedContext.rut_client || '',
        email: this.unifiedContext.email || '',
        phone: this.unifiedContext.phone || '',
        address_standard: this.unifiedContext.address_standard || '',
        commune: this.unifiedContext.commune || '',
        service_nis: this.unifiedContext.service_nis || ''
      }
      this.editedMateria = this.materia && this.materia !== '—' ? this.materia : ''
      this.editedMontoDisputa = this.montoDisputa && this.montoDisputa !== '—' ? this.montoDisputa : null
      this.editedEmpresa = this.empresa && this.empresa !== '—' ? this.empresa : ''
      this.editedFechaIngreso = this.fechaIngreso && this.fechaIngreso !== '—' ? this.fechaIngreso : ''
      this.isEditing = true
    },
    async guardarCambios() {
      this.saving = true
      try {
        const caseId = this.compilationMetadata.case_id
        
        // Actualizar unified_context
        await casosAPI.updateUnifiedContext(caseId, {
          unified_context: this.editedContext,
          materia: this.editedMateria || null,
          monto_disputa: this.editedMontoDisputa || null,
          empresa: this.editedEmpresa || null,
          fecha_ingreso: this.editedFechaIngreso || null
        })
        
        // Emitir evento para recargar el caso
        this.$emit('contexto-actualizado')
        
        this.isEditing = false
        alert('Cambios guardados correctamente en la base de datos')
      } catch (error) {
        console.error('Error guardando cambios:', error)
        alert('Error al guardar los cambios: ' + (error.message || 'Error desconocido'))
      } finally {
        this.saving = false
      }
    }
  }
}
</script>

<style scoped>
.seccion-a {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  border-bottom: 2px solid #667eea;
  padding-bottom: 0.5rem;
}

.seccion-a h3 {
  margin: 0;
  color: #333;
  font-size: 1.5rem;
}

.btn-edit {
  background: #667eea;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: background 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-edit:hover {
  background: #5568d3;
}

.btn-edit.btn-save {
  background: #4caf50;
}

.btn-edit.btn-save:hover {
  background: #45a049;
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.context-card {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
  transition: box-shadow 0.2s;
}

.context-card:hover {
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.card-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.card-icon {
  font-size: 1.5rem;
}

.card-header h4 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
}

.card-body {
  padding: 1.5rem;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 0.75rem 0;
  border-bottom: 1px solid #f0f0f0;
}

.info-item:last-child {
  border-bottom: none;
}

.label {
  font-weight: 600;
  color: #666;
  min-width: 140px;
}

.value {
  color: #333;
  text-align: right;
  flex: 1;
}

.value.amount {
  font-weight: 600;
  color: #667eea;
  font-size: 1.1rem;
}

.edit-input {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
  font-family: inherit;
}

.edit-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
}

.alertas {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e0e0e0;
}

.alertas h4 {
  margin-bottom: 1rem;
  color: #333;
  font-size: 1.1rem;
}

.badges-container {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.alerta-badge {
  background: #ff9800;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 500;
}
</style>

