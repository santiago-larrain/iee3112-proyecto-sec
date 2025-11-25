<template>
  <div class="cases-table-container">
    <table class="cases-table">
      <thead>
        <tr>
          <th @click="sort('case_id')" class="sortable">
            <div class="th-content">
              <span>ID Caso</span>
              <span class="sort-icons">
                <span class="sort-arrow" :class="{ 'active': sortBy === 'case_id' && sortOrder === 'asc' }">▲</span>
                <span class="sort-arrow" :class="{ 'active': sortBy === 'case_id' && sortOrder === 'desc' }">▼</span>
              </span>
            </div>
          </th>
          <th @click="sort('client_name')" class="sortable">
            <div class="th-content">
              <span>Cliente</span>
              <span class="sort-icons">
                <span class="sort-arrow" :class="{ 'active': sortBy === 'client_name' && sortOrder === 'asc' }">▲</span>
                <span class="sort-arrow" :class="{ 'active': sortBy === 'client_name' && sortOrder === 'desc' }">▼</span>
              </span>
            </div>
          </th>
          <th @click="sort('rut_client')" class="sortable">
            <div class="th-content">
              <span>RUT</span>
              <span class="sort-icons">
                <span class="sort-arrow" :class="{ 'active': sortBy === 'rut_client' && sortOrder === 'asc' }">▲</span>
                <span class="sort-arrow" :class="{ 'active': sortBy === 'rut_client' && sortOrder === 'desc' }">▼</span>
              </span>
            </div>
          </th>
          <th @click="sort('materia')" class="sortable">
            <div class="th-content">
              <span>Materia</span>
              <span class="sort-icons">
                <span class="sort-arrow" :class="{ 'active': sortBy === 'materia' && sortOrder === 'asc' }">▲</span>
                <span class="sort-arrow" :class="{ 'active': sortBy === 'materia' && sortOrder === 'desc' }">▼</span>
              </span>
            </div>
          </th>
          <th @click="sort('monto_disputa')" class="sortable">
            <div class="th-content">
              <span>Monto</span>
              <span class="sort-icons">
                <span class="sort-arrow" :class="{ 'active': sortBy === 'monto_disputa' && sortOrder === 'asc' }">▲</span>
                <span class="sort-arrow" :class="{ 'active': sortBy === 'monto_disputa' && sortOrder === 'desc' }">▼</span>
              </span>
            </div>
          </th>
          <th @click="sort('empresa')" class="sortable">
            <div class="th-content">
              <span>Empresa</span>
              <span class="sort-icons">
                <span class="sort-arrow" :class="{ 'active': sortBy === 'empresa' && sortOrder === 'asc' }">▲</span>
                <span class="sort-arrow" :class="{ 'active': sortBy === 'empresa' && sortOrder === 'desc' }">▼</span>
              </span>
            </div>
          </th>
          <th @click="sort('status')" class="sortable">
            <div class="th-content">
              <span>Estado</span>
              <span class="sort-icons">
                <span class="sort-arrow" :class="{ 'active': sortBy === 'status' && sortOrder === 'asc' }">▲</span>
                <span class="sort-arrow" :class="{ 'active': sortBy === 'status' && sortOrder === 'desc' }">▼</span>
              </span>
            </div>
          </th>
          <th @click="sort('fecha_ingreso')" class="sortable">
            <div class="th-content">
              <span>Fecha Ingreso</span>
              <span class="sort-icons">
                <span class="sort-arrow" :class="{ 'active': sortBy === 'fecha_ingreso' && sortOrder === 'asc' }">▲</span>
                <span class="sort-arrow" :class="{ 'active': sortBy === 'fecha_ingreso' && sortOrder === 'desc' }">▼</span>
              </span>
            </div>
          </th>
          <th>Acciones</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="caso in casos" :key="caso.case_id" class="caso-row">
          <td>{{ caso.case_id }}</td>
          <td>{{ caso.client_name }}</td>
          <td>{{ caso.rut_client }}</td>
          <td>{{ caso.materia }}</td>
          <td>${{ (caso.monto_disputa || 0).toLocaleString('es-CL') }}</td>
          <td>{{ caso.empresa }}</td>
          <td>
            <span :class="['status-badge', getStatusClass(caso.status)]">
              {{ caso.status }}
            </span>
          </td>
          <td>{{ caso.fecha_ingreso }}</td>
          <td>
            <button @click="abrirCaso(caso.case_id)" class="btn-primary">
              Abrir
            </button>
          </td>
        </tr>
        <tr v-if="casos.length === 0" class="empty-row">
          <td colspan="9" class="empty-message">
            No se encontraron casos
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
export default {
  name: 'CasesTable',
  props: {
    casos: {
      type: Array,
      default: () => []
    },
    sortBy: {
      type: String,
      default: null
    },
    sortOrder: {
      type: String,
      default: 'asc'
    }
  },
  methods: {
    sort(column) {
      this.$emit('sort', column)
    },
    abrirCaso(caseId) {
      this.$emit('open-case', caseId)
    },
    getStatusClass(status) {
      const classes = {
        'PENDIENTE': 'status-pending',
        'EN_REVISION': 'status-review',
        'RESUELTO': 'status-resolved',
        'CERRADO': 'status-closed'
      }
      return classes[status] || ''
    }
  }
}
</script>

<style scoped>
.cases-table-container {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.cases-table {
  width: 100%;
  border-collapse: collapse;
}

.cases-table thead {
  background: #f5f5f5;
}

.cases-table th {
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  color: #333;
  border-bottom: 2px solid #ddd;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.cases-table th.sortable {
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}

.cases-table th.sortable:hover {
  background: #e8e8e8;
}

.th-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.sort-icons {
  display: flex;
  flex-direction: column;
  gap: 0;
  line-height: 0.7;
  font-size: 0.65rem;
  opacity: 0.4;
  transition: opacity 0.2s;
  margin-left: 0.5rem;
  min-width: 0.8rem;
}

.cases-table th.sortable:hover .sort-icons {
  opacity: 0.7;
}

.sort-arrow {
  display: block;
  color: #999;
  transition: color 0.2s, opacity 0.2s, transform 0.2s;
  height: 0.5rem;
  line-height: 0.5rem;
  font-weight: normal;
}

.sort-arrow.active {
  color: #667eea;
  opacity: 1;
  font-weight: bold;
  transform: scale(1.2);
}

.cases-table th.sortable:hover .sort-arrow {
  color: #667eea;
}

.cases-table th.sortable:hover .sort-arrow.active {
  opacity: 1;
  transform: scale(1.3);
}

.cases-table td {
  padding: 1rem;
  border-bottom: 1px solid #eee;
  font-size: 0.95rem;
}

.caso-row:hover {
  background: #f9f9f9;
}

.empty-row {
  text-align: center;
}

.empty-message {
  padding: 3rem;
  color: #999;
  font-style: italic;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 500;
  display: inline-block;
}

.status-pending {
  background: #fff3e0;
  color: #f57c00;
}

.status-review {
  background: #e3f2fd;
  color: #1976d2;
}

.status-resolved {
  background: #e8f5e9;
  color: #388e3c;
}

.status-closed {
  background: #f3e5f5;
  color: #7b1fa2;
}

.btn-primary {
  background: #667eea;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background 0.2s;
}

.btn-primary:hover {
  background: #5568d3;
}
</style>

