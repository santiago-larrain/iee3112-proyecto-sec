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
    
    <!-- Modal Visor de Documento -->
    <div v-if="documentoSeleccionado" class="modal-overlay" @click="cerrarVisorDocumento">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h4>Vista Previa del Documento</h4>
          <button @click="cerrarVisorDocumento" class="modal-close">×</button>
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
              @error="handleIframeError"
            ></iframe>
            
            <!-- Image Viewer -->
            <img
              v-if="documentUrl && !loadingDocument && !documentError && isImage"
              :src="documentUrl"
              class="image-viewer"
              alt="Vista previa"
              @error="handleImageError"
            />
            
            <!-- DOCX Viewer (converted to PDF) -->
            <iframe
              v-if="documentUrl && !loadingDocument && !documentError && isDocx"
              :src="documentUrl"
              class="pdf-viewer"
              frameborder="0"
              @error="handleIframeError"
            ></iframe>
            
            <!-- Fallback para otros tipos -->
            <div v-if="documentUrl && !loadingDocument && !documentError && !isPdf && !isImage && !isDocx" class="other-document">
              <p>📄 Documento no se puede previsualizar</p>
              <a :href="documentUrl" target="_blank" class="btn-download">
                Descargar Documento
              </a>
            </div>
          </div>
        </div>
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
    },
    documentInventory: {
      type: Object,
      default: null
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
      calculating: false,
      documentoSeleccionado: null,
      documentUrl: null,
      loadingDocument: false,
      documentError: null,
      selectedFileId: null,
      selectedPageIndex: null
    }
  },
  computed: {
    isMontoItem() {
      // Detectar si el item es de validación de montos/CNR
      const title = (this.item.title || '').toLowerCase()
      const id = (this.item.id || '').toLowerCase()
      return title.includes('monto') || title.includes('cnr') || title.includes('cálculo') || 
             id.includes('c.2') || id.includes('monto')
    },
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
    },
    isDocx() {
      if (!this.documentoSeleccionado) return false
      const name = this.documentoSeleccionado.original_name || ''
      return name.toLowerCase().endsWith('.docx')
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
      // Abrir documento en modal
      this.selectedFileId = fileId
      this.selectedPageIndex = pageIndex
      
      // Buscar el documento en el document_inventory si está disponible
      let documentoInfo = null
      if (this.documentInventory) {
        // Buscar en todas las categorías
        const categories = ['reclamo_respuesta', 'informe_evidencias', 'historial_calculos', 'otros', 
                           'level_1_critical', 'level_2_supporting', 'level_0_missing']
        for (const category of categories) {
          const docs = this.documentInventory[category] || []
          documentoInfo = docs.find(doc => doc.file_id === fileId)
          if (documentoInfo) break
        }
      }
      
      // Si no se encuentra en document_inventory, intentar obtenerlo del backend
      if (!documentoInfo) {
        try {
          // Obtener información del caso para buscar el documento
          const casoResponse = await casosAPI.getCaso(this.caseId)
          const caso = casoResponse.data
          const docInventory = caso.document_inventory || {}
          const categories = ['reclamo_respuesta', 'informe_evidencias', 'historial_calculos', 'otros',
                             'level_1_critical', 'level_2_supporting', 'level_0_missing']
          for (const category of categories) {
            const docs = docInventory[category] || []
            documentoInfo = docs.find(doc => doc.file_id === fileId)
            if (documentoInfo) break
          }
        } catch (error) {
          console.warn('No se pudo obtener información del documento:', error)
        }
      }
      
      // Crear objeto documento para el modal
      this.documentoSeleccionado = {
        file_id: fileId,
        original_name: documentoInfo?.original_name || `Documento ${fileId}`,
        standardized_name: documentoInfo?.standardized_name,
        page_index: pageIndex,
        extracted_data: documentoInfo?.extracted_data,
        metadata: documentoInfo?.metadata
      }
      await this.cargarDocumento()
    },
    async cargarDocumento() {
      if (!this.documentoSeleccionado || !this.selectedFileId) return
      
      this.loadingDocument = true
      this.documentError = null
      
      try {
        const apiUrl = `http://localhost:8000/api/casos/${this.caseId}/documentos/${this.selectedFileId}/preview`
        if (this.selectedPageIndex !== null && this.selectedPageIndex !== undefined) {
          // Agregar parámetro de página si está disponible
          // Nota: El backend puede usar esto en el futuro para navegar a una página específica
        }
        
        // Verificar que el archivo existe antes de intentar cargarlo
        const response = await fetch(apiUrl, { method: 'HEAD' })
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: response.statusText }))
          throw new Error(errorData.detail || `Error ${response.status}: ${response.statusText}`)
        }
        
        // Si la verificación es exitosa, usar la URL
        this.documentUrl = apiUrl
        this.loadingDocument = false
      } catch (error) {
        console.error('Error cargando documento:', error)
        this.documentError = error.message || 'Error desconocido'
        this.loadingDocument = false
        this.documentUrl = null
      }
    },
    cerrarVisorDocumento() {
      this.documentoSeleccionado = null
      this.documentUrl = null
      this.documentError = null
      this.selectedFileId = null
      this.selectedPageIndex = null
    },
    handleIframeError() {
      this.documentError = 'Error al cargar el documento. El archivo puede no existir o estar corrupto.'
      this.documentUrl = null
    },
    handleImageError() {
      this.documentError = 'Error al cargar la imagen. El archivo puede no existir o estar corrupto.'
      this.documentUrl = null
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
      this.calculationResult = null
      
      try {
        const historial = this.parseHistorial()
        
        // Validar que haya historial o CIM
        if (historial.length === 0 && (!this.calculatorData.cim || this.calculatorData.cim <= 0)) {
          alert('Debe proporcionar historial de consumo o CIM válido')
          this.calculating = false
          return
        }
        
        // Validar meses
        const meses = parseInt(this.calculatorData.meses)
        if (!meses || meses <= 0 || isNaN(meses)) {
          alert('Debe especificar meses a recuperar (mayor a 0)')
          this.calculating = false
          return
        }
        
        // Validar tarifa
        const tarifa = parseFloat(this.calculatorData.tarifa)
        if (!tarifa || tarifa <= 0 || isNaN(tarifa)) {
          alert('Debe especificar tarifa vigente (mayor a 0)')
          this.calculating = false
          return
        }
        
        // Preparar historial: si hay historial, usarlo; si no, usar CIM como único valor
        let historial_kwh = historial
        if (historial.length === 0 && this.calculatorData.cim) {
          // Si solo hay CIM, crear un historial con ese valor para el cálculo
          historial_kwh = [parseFloat(this.calculatorData.cim)]
        }
        
        // Validar que el historial tenga valores válidos
        if (historial_kwh.length === 0 || historial_kwh.some(v => isNaN(v) || v <= 0)) {
          alert('El historial de consumo debe contener valores numéricos válidos mayores a 0')
          this.calculating = false
          return
        }
        
        const cimOverride = this.calculatorData.cim ? parseFloat(this.calculatorData.cim) : null
        
        const response = await casosAPI.calculateCNR(this.caseId, {
          historial_kwh: historial_kwh,
          tarifa_vigente: tarifa,
          meses_a_recuperar: meses,
          cim_override: cimOverride
        })
        
        // Acceder a response.data ya que axios devuelve { data: {...}, status: ... }
        const result = response.data || response
        
        // Validar que el resultado tenga los campos esperados
        if (!result || typeof result.monto_calculado === 'undefined' || isNaN(result.monto_calculado)) {
          console.error('Respuesta inválida del servidor:', result)
          alert('Error: El servidor devolvió una respuesta inválida. Verifique los valores ingresados.')
          return
        }
        
        this.calculationResult = result
      } catch (error) {
        console.error('Error calculando CNR:', error)
        const errorMsg = error.response?.data?.detail || error.message || 'Error desconocido'
        alert('Error al calcular CNR: ' + errorMsg)
        this.calculationResult = null
      } finally {
        this.calculating = false
      }
    },
    formatNumber(num) {
      if (num === null || num === undefined || isNaN(num)) {
        return '0.00'
      }
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

/* Estilos para modal de documento */
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
</style>

