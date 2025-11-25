<template>
  <div class="filter-bar">
    <div class="filter-group">
      <label for="estado-filter">Estado:</label>
      <select 
        id="estado-filter"
        v-model="selectedEstado" 
        @change="onFilterChange"
        class="filter-select"
      >
        <option value="">Todos</option>
        <option value="PENDIENTE">Pendientes</option>
        <option value="RESUELTO">Resueltos</option>
      </select>
    </div>
    
    <div class="filter-group">
      <label for="tipo-filter">Tipo de Caso:</label>
      <select 
        id="tipo-filter"
        v-model="selectedTipo" 
        @change="onFilterChange"
        class="filter-select"
      >
        <option value="">Todos</option>
        <option value="CNR">CNR</option>
        <option value="OTRO">Otro</option>
      </select>
    </div>
  </div>
</template>

<script>
export default {
  name: 'FilterBar',
  data() {
    return {
      selectedEstado: '',
      selectedTipo: ''
    }
  },
  methods: {
    onFilterChange() {
      this.$emit('filter', {
        estado: this.selectedEstado,
        tipo: this.selectedTipo
      })
    }
  }
}
</script>

<style scoped>
.filter-bar {
  display: flex;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.filter-group label {
  font-weight: 500;
  color: #333;
  white-space: nowrap;
}

.filter-select {
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.95rem;
  background: white;
  cursor: pointer;
  min-width: 150px;
}

.filter-select:focus {
  outline: none;
  border-color: #667eea;
}
</style>

