<template>
  <div class="seccion-c">
    <h3>Sección C: Checklist de Validación Expandible</h3>
    
    <div v-if="!checklist || (!hasChecklistItems)" class="no-checklist">
      <p>No hay items de checklist disponibles para este caso.</p>
    </div>
    
    <!-- Grupo A: Admisibilidad y Forma -->
    <div class="checklist-group" v-if="checklist?.group_a_admisibilidad?.length > 0">
      <h4 class="group-title">
        <span class="group-icon">📋</span>
        Grupo A: Etapa de Admisibilidad y Forma
      </h4>
      <p class="group-description">Verificar requisitos administrativos y plazos legales</p>
      <div class="checklist-items">
        <ChecklistItem
          v-for="item in checklist.group_a_admisibilidad"
          :key="item.id"
          :item="item"
          :case-id="caseId"
          @validated="onItemValidated"
        />
      </div>
    </div>

    <!-- Grupo B: Instrucción (Integridad Probatoria) -->
    <div class="checklist-group" v-if="checklist?.group_b_instruccion?.length > 0">
      <h4 class="group-title">
        <span class="group-icon">🔍</span>
        Grupo B: Etapa de Instrucción (Integridad Probatoria)
      </h4>
      <p class="group-description">Verificar que la empresa haya aportado todas las piezas del expediente</p>
      <div class="checklist-items">
        <ChecklistItem
          v-for="item in checklist.group_b_instruccion"
          :key="item.id"
          :item="item"
          :case-id="caseId"
          @validated="onItemValidated"
        />
      </div>
    </div>

    <!-- Grupo C: Análisis Técnico-Jurídico -->
    <div class="checklist-group" v-if="checklist?.group_c_analisis?.length > 0">
      <h4 class="group-title">
        <span class="group-icon">⚖️</span>
        Grupo C: Etapa de Análisis Técnico-Jurídico (Fondo del Asunto)
      </h4>
      <p class="group-description">Cruzamiento de datos para validar la legalidad del cobro</p>
      <div class="checklist-items">
        <ChecklistItem
          v-for="item in checklist.group_c_analisis"
          :key="item.id"
          :item="item"
          :case-id="caseId"
          @validated="onItemValidated"
        />
      </div>
    </div>
  </div>
</template>

<script>
import ChecklistItem from './ChecklistItem.vue'

export default {
  name: 'SeccionC',
  components: {
    ChecklistItem
  },
  inject: ['actualizarChecklistItem'],
  props: {
    checklist: {
      type: Object,
      default: () => ({
        group_a_admisibilidad: [],
        group_b_instruccion: [],
        group_c_analisis: {
          c1_acreditacion_hecho: [],
          c2_legalidad_cobro: []
        }
      })
    },
    caseId: {
      type: String,
      required: true
    }
  },
  computed: {
    hasChecklistItems() {
      if (!this.checklist) return false
      const hasA = this.checklist.group_a_admisibilidad?.length > 0
      const hasB = this.checklist.group_b_instruccion?.length > 0
      // Nueva estructura: group_c_analisis es una lista directa
      const hasC = Array.isArray(this.checklist.group_c_analisis) && this.checklist.group_c_analisis.length > 0
      // Compatibilidad con estructura antigua
      const hasC1 = this.checklist.group_c_analisis?.c1_acreditacion_hecho?.length > 0
      const hasC2 = this.checklist.group_c_analisis?.c2_legalidad_cobro?.length > 0
      return hasA || hasB || hasC || hasC1 || hasC2
    }
  },
  methods: {
    async onItemValidated(itemId, validated) {
      try {
        await this.actualizarChecklistItem(this.caseId, itemId, validated)
        this.$emit('checklist-actualizado')
      } catch (error) {
        console.error('Error al actualizar validación:', error)
        alert('Error al actualizar la validación')
      }
    }
  }
}
</script>

<style scoped>
.seccion-c {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.seccion-c h3 {
  margin-bottom: 1.5rem;
  color: #333;
  font-size: 1.5rem;
  border-bottom: 2px solid #667eea;
  padding-bottom: 0.5rem;
}

.checklist-group {
  margin-bottom: 2.5rem;
  padding: 1.5rem;
  background: #f9f9f9;
  border-radius: 6px;
  border-left: 4px solid #667eea;
}

.group-title {
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #333;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.group-icon {
  font-size: 1.3rem;
}

.group-description {
  color: #666;
  font-size: 0.9rem;
  margin-bottom: 1rem;
  font-style: italic;
}

.sub-checklist {
  margin-top: 1.5rem;
  margin-left: 1rem;
  padding: 1rem;
  background: white;
  border-radius: 4px;
  border-left: 3px solid #4caf50;
}

.sub-checklist-title {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
  color: #555;
}

.checklist-items {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.no-checklist {
  text-align: center;
  padding: 2rem;
  color: #666;
  font-style: italic;
}
</style>
