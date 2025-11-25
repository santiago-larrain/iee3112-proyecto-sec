<template>
  <div class="caso-detalle">
    <div class="header-actions">
      <button @click="$router.push('/')" class="btn-back">← Volver al Dashboard</button>
    </div>

    <div v-if="loading" class="loading">
      Cargando caso...
    </div>

    <div v-if="error && !caso" class="error">
      <p>{{ error }}</p>
      <p class="error-hint">Intentando cargar información parcial...</p>
    </div>

    <div v-if="!loading && caso">
      <!-- Sección A: Resumen de Contexto -->
      <SeccionA
        :unified-context="caso.unified_context"
        :compilation-metadata="caso.compilation_metadata"
        :materia="caso.materia"
        :monto-disputa="caso.monto_disputa"
        :empresa="caso.empresa"
        :fecha-ingreso="caso.fecha_ingreso"
        :alertas="caso.alertas"
        @contexto-actualizado="recargarCaso"
      />

      <!-- Sección B: Gestor Documental -->
      <SeccionB
        :document-inventory="caso.document_inventory"
        :case-id="caseId"
        @documento-actualizado="onDocumentoActualizado"
      />

      <!-- Sección C: Checklist -->
      <SeccionC
        :checklist="caso.checklist"
        :case-id="caseId"
        @checklist-actualizado="recargarCaso"
      />

      <!-- Sección D: Resolución -->
      <SeccionD
        :case-id="caseId"
        :checklist="caso.checklist"
      />
    </div>
  </div>
</template>

<script>
import { casosAPI } from '../services/api'
import SeccionA from '../components/SeccionA.vue'
import SeccionB from '../components/SeccionB.vue'
import SeccionC from '../components/SeccionC.vue'
import SeccionD from '../components/SeccionD.vue'

export default {
  name: 'CasoDetalle',
  components: {
    SeccionA,
    SeccionB,
    SeccionC,
    SeccionD
  },
  props: {
    id: {
      type: String,
      required: true
    }
  },
  provide() {
    return {
      actualizarDocumento: this.actualizarDocumento,
      actualizarChecklistItem: this.actualizarChecklistItem,
      generarResolucion: this.generarResolucion
    }
  },
  data() {
    return {
      caso: null,
      loading: true,
      error: null,
      caseId: ''
    }
  },
  mounted() {
    this.caseId = this.id
    this.cargarCaso()
  },
  methods: {
    async cargarCaso() {
      this.loading = true
      this.error = null
      try {
        const response = await casosAPI.getCaso(this.caseId)
        this.caso = this.normalizeCaso(response.data)
      } catch (err) {
        console.error('Error cargando caso:', err)
        this.error = 'Error al cargar el caso: ' + (err.message || 'Error desconocido')
        // Intentar crear un caso mínimo para mostrar algo
        this.caso = this.createEmptyCaso()
      } finally {
        this.loading = false
      }
    },
    normalizeCaso(caso) {
      // Asegurar que todos los campos existan
      if (!caso) return this.createEmptyCaso()
      
      // Normalizar unified_context
      if (!caso.unified_context) {
        caso.unified_context = {}
      }
      const uc = caso.unified_context
      uc.rut_client = uc.rut_client || '—'
      uc.client_name = uc.client_name || '—'
      uc.service_nis = uc.service_nis || '—'
      uc.address_standard = uc.address_standard || '—'
      uc.commune = uc.commune || '—'
      uc.email = uc.email || null
      uc.phone = uc.phone || null
      
      // Normalizar document_inventory
      if (!caso.document_inventory) {
        caso.document_inventory = {
          level_1_critical: [],
          level_2_supporting: [],
          level_0_missing: []
        }
      }
      
      // Normalizar checklist
      if (!caso.checklist) {
        caso.checklist = {
          client_information: [],
          evidence_review: [],
          legal_compliance: []
        }
      }
      
      // Normalizar otros campos
      caso.materia = caso.materia || '—'
      caso.monto_disputa = caso.monto_disputa || null
      caso.empresa = caso.empresa || '—'
      caso.fecha_ingreso = caso.fecha_ingreso || '—'
      caso.alertas = caso.alertas || []
      
      return caso
    },
    createEmptyCaso() {
      return {
        compilation_metadata: {
          case_id: this.caseId,
          processing_timestamp: new Date().toISOString(),
          status: 'UNKNOWN'
        },
        unified_context: {
          rut_client: '—',
          client_name: '—',
          service_nis: '—',
          address_standard: '—',
          commune: '—',
          email: null,
          phone: null
        },
        document_inventory: {
          level_1_critical: [],
          level_2_supporting: [],
          level_0_missing: []
        },
        checklist: {
          client_information: [],
          evidence_review: [],
          legal_compliance: []
        },
        materia: '—',
        monto_disputa: null,
        empresa: '—',
        fecha_ingreso: '—',
        alertas: []
      }
    },
    async actualizarDocumento(caseId, fileId, tipo, customName = null) {
      return await casosAPI.updateDocumento(caseId, fileId, tipo, customName)
    },
    async actualizarChecklistItem(caseId, itemId, validated) {
      return await casosAPI.updateChecklistItem(caseId, itemId, validated)
    },
    async generarResolucion(caseId, templateType, content) {
      return await casosAPI.generarResolucion(caseId, templateType, content)
    },
    async onDocumentoActualizado(data) {
      // Actualizar el checklist localmente
      if (data.checklist) {
        this.caso.checklist = data.checklist
      }
      // Actualizar el documento en el inventario localmente si está disponible
      // Esto permite que el cambio se refleje inmediatamente sin recargar
      if (data.document && data.document_inventory) {
        this.caso.document_inventory = data.document_inventory
      }
      // Recargar caso completo para asegurar sincronización completa
      await this.recargarCaso()
    },
    async recargarCaso() {
      await this.cargarCaso()
    }
  }
}
</script>

<style scoped>
.caso-detalle {
  width: 100%;
}

.header-actions {
  margin-bottom: 1.5rem;
}

.btn-back {
  background: #666;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background 0.2s;
}

.btn-back:hover {
  background: #555;
}

.loading, .error {
  text-align: center;
  padding: 2rem;
  background: white;
  border-radius: 8px;
  margin-top: 2rem;
}

.error {
  color: #d32f2f;
  background: #ffebee;
  padding: 1.5rem;
}

.error-hint {
  margin-top: 0.5rem;
  font-size: 0.9rem;
  opacity: 0.8;
}
</style>

