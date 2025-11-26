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
      
      <!-- Calculadora CNR (solo para items de validación de montos) -->
      <div class="calculator-section" v-if="isMontoItem">
        <button @click="openCalculator" class="btn-calculator">
          🧮 Abrir Simulador CNR
        </button>
      </div>
    </div>
    
    <!-- Modal Calculadora CNR -->
    <div v-if="showCalculator" class="modal-overlay" @click="closeCalculator">
      <div class="modal-content calculator-modal" @click.stop>
        <div class="modal-header">
          <h3>🧮 Simulador CNR</h3>
          <button @click="closeCalculator" class="modal-close">×</button>
        </div>
        <div class="modal-body">
          <div class="calculator-form">
            <div class="form-group">
              <label>CIM (Consumo Índice Mensual) en kWh:</label>
              <input 
                v-model.number="calculatorData.cim" 
                type="number" 
                step="0.01"
                class="form-input"
                placeholder="Ej: 623"
              />
            </div>
            <div class="form-group">
              <label>Meses a Recuperar:</label>
              <input 
                v-model.number="calculatorData.meses" 
                type="number" 
                class="form-input"
                placeholder="Ej: 6"
              />
            </div>
            <div class="form-group">
              <label>Tarifa Vigente ($/kWh):</label>
              <input 
                v-model.number="calculatorData.tarifa" 
                type="number" 
                step="0.01"
                class="form-input"
                placeholder="Ej: 150.5"
              />
            </div>
            <div class="form-group">
              <label>Historial de Consumo (kWh) - Últimos 12 meses:</label>
              <textarea 
                v-model="historialInput" 
                class="form-textarea"
                placeholder="Separar por comas: 600, 620, 610, 630, ..."
                rows="3"
              ></textarea>
            </div>
            <button @click="calculateCNR" class="btn-calculate" :disabled="calculating">
              {{ calculating ? 'Calculando...' : 'Calcular' }}
            </button>
          </div>
          
          <div v-if="calculationResult" class="calculation-result">
            <h4>Resultado del Cálculo</h4>
            <div class="result-item">
              <span class="result-label">Monto Calculado:</span>
              <span class="result-value highlight">${{ formatNumber(calculationResult.monto_calculado) }}</span>
            </div>
            <div class="result-item" v-if="calculationResult.diferencia_vs_cobrado !== null">
              <span class="result-label">Diferencia vs. Cobrado:</span>
              <span class="result-value" :class="{ 'positive': calculationResult.diferencia_vs_cobrado < 0, 'negative': calculationResult.diferencia_vs_cobrado > 0 }">
                ${{ formatNumber(Math.abs(calculationResult.diferencia_vs_cobrado)) }}
                <span v-if="calculationResult.diferencia_vs_cobrado > 0">(Empresa cobró de más)</span>
                <span v-else>(Empresa cobró de menos)</span>
              </span>
            </div>
            <div class="result-item">
              <span class="result-label">CIM Aplicado:</span>
              <span class="result-value">{{ calculationResult.cim_aplicado }} kWh</span>
            </div>
            <div class="breakdown" v-if="calculationResult.breakdown_por_mes">
              <h5>Desglose por Mes:</h5>
              <table class="breakdown-table">
                <thead>
                  <tr>
                    <th>Mes</th>
                    <th>Consumo (kWh)</th>
                    <th>Tarifa</th>
                    <th>Monto</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="mes in calculationResult.breakdown_por_mes" :key="mes.mes">
                    <td>{{ mes.mes }}</td>
                    <td>{{ mes.consumo_kwh.toFixed(2) }}</td>
                    <td>${{ formatNumber(mes.tarifa) }}</td>
                    <td>${{ formatNumber(mes.monto) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { casosAPI } from '../services/api'

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
      isExpanded: false,
      showCalculator: false,
      calculatorData: {
        cim: null,
        meses: 6,
        tarifa: 150.0,
        historial: []
      },
      historialInput: '',
      calculationResult: null,
      calculating: false
    }
  },
  computed: {
    isMontoItem() {
      // Detectar si el item es de validación de montos/CNR
      const title = (this.item.title || '').toLowerCase()
      const id = (this.item.id || '').toLowerCase()
      return title.includes('monto') || title.includes('cnr') || title.includes('cálculo') || 
             id.includes('c.2') || id.includes('monto')
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
    },
    openCalculator() {
      this.showCalculator = true
      // Inicializar valores por defecto si están disponibles en el item
      if (this.item.evidence) {
        // Intentar extraer valores del evidence si es posible
      }
    },
    closeCalculator() {
      this.showCalculator = false
      this.calculationResult = null
    },
    parseHistorial() {
      if (!this.historialInput) return []
      return this.historialInput
        .split(',')
        .map(v => parseFloat(v.trim()))
        .filter(v => !isNaN(v))
    },
    async calculateCNR() {
      this.calculating = true
      try {
        const historial = this.parseHistorial()
        
        if (historial.length === 0 && !this.calculatorData.cim) {
          alert('Debe proporcionar historial de consumo o CIM')
          return
        }
        
        if (!this.calculatorData.meses || this.calculatorData.meses <= 0) {
          alert('Debe especificar meses a recuperar')
          return
        }
        
        if (!this.calculatorData.tarifa || this.calculatorData.tarifa <= 0) {
          alert('Debe especificar tarifa vigente')
          return
        }
        
        const response = await casosAPI.calculateCNR(this.caseId, {
          historial_kwh: historial.length > 0 ? historial : [this.calculatorData.cim || 0],
          tarifa_vigente: this.calculatorData.tarifa,
          meses_a_recuperar: this.calculatorData.meses,
          cim_override: this.calculatorData.cim || null
        })
        
        this.calculationResult = response
      } catch (error) {
        console.error('Error calculando CNR:', error)
        alert('Error al calcular CNR: ' + (error.response?.data?.detail || error.message || 'Error desconocido'))
      } finally {
        this.calculating = false
      }
    },
    formatNumber(num) {
      return Number(num).toLocaleString('es-CL', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
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

.calculator-section {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e0e0e0;
}

.btn-calculator {
  background: #9c27b0;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: background 0.2s;
}

.btn-calculator:hover {
  background: #7b1fa2;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 700px;
  max-height: 90vh;
  overflow: auto;
}

.calculator-modal {
  max-width: 800px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #e0e0e0;
}

.modal-header h3 {
  margin: 0;
  color: #333;
}

.modal-close {
  background: none;
  border: none;
  font-size: 2rem;
  color: #666;
  cursor: pointer;
  padding: 0;
  width: 2rem;
  height: 2rem;
  line-height: 1;
}

.modal-close:hover {
  color: #333;
}

.modal-body {
  padding: 1.5rem;
}

.calculator-form {
  margin-bottom: 2rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #333;
}

.form-input,
.form-textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
  font-family: inherit;
}

.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
}

.btn-calculate {
  background: #667eea;
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 600;
  transition: background 0.2s;
  width: 100%;
}

.btn-calculate:hover:not(:disabled) {
  background: #5568d3;
}

.btn-calculate:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.calculation-result {
  margin-top: 2rem;
  padding: 1.5rem;
  background: #f5f5f5;
  border-radius: 8px;
  border-left: 4px solid #667eea;
}

.calculation-result h4 {
  margin-top: 0;
  margin-bottom: 1rem;
  color: #333;
}

.result-item {
  display: flex;
  justify-content: space-between;
  padding: 0.75rem 0;
  border-bottom: 1px solid #e0e0e0;
}

.result-item:last-child {
  border-bottom: none;
}

.result-label {
  font-weight: 600;
  color: #666;
}

.result-value {
  color: #333;
  font-weight: 600;
}

.result-value.highlight {
  color: #667eea;
  font-size: 1.2rem;
}

.result-value.positive {
  color: #4caf50;
}

.result-value.negative {
  color: #f44336;
}

.breakdown {
  margin-top: 1.5rem;
}

.breakdown h5 {
  margin-bottom: 1rem;
  color: #333;
}

.breakdown-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 4px;
  overflow: hidden;
}

.breakdown-table thead {
  background: #667eea;
  color: white;
}

.breakdown-table th,
.breakdown-table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

.breakdown-table th {
  font-weight: 600;
}

.breakdown-table tbody tr:hover {
  background: #f5f5f5;
}
</style>

