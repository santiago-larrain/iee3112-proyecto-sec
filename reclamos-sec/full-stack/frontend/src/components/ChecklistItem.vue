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
      <div class="evidence-section" v-if="item.evidence">
        <strong>Evidencia:</strong>
        <p v-html="formatEvidence(item.evidence)"></p>
      </div>
      <div class="description-section" v-if="item.description">
        <strong>Descripción:</strong>
        <p>{{ item.description }}</p>
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
    handleValidationChange(event) {
      this.$emit('validated', this.item.id, event.target.checked)
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
.description-section {
  margin-bottom: 1rem;
}

.evidence-section strong,
.description-section strong {
  display: block;
  margin-bottom: 0.5rem;
  color: #333;
  font-size: 0.9rem;
}

.evidence-section p,
.description-section p {
  margin: 0;
  color: #666;
  line-height: 1.5;
  padding: 0.5rem;
  background: #f5f5f5;
  border-radius: 4px;
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

