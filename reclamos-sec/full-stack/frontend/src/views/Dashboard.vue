<template>
  <div class="dashboard">
    <h2>Panel de Reclamos</h2>
    
    <!-- Tarjetas de Resumen -->
    <div class="summary-cards">
      <div class="summary-card">
        <div class="card-icon total">📊</div>
        <div class="card-content">
          <h3>{{ totalCasos }}</h3>
          <p>Total Casos</p>
        </div>
      </div>
      <div class="summary-card">
        <div class="card-icon pending">⏳</div>
        <div class="card-content">
          <h3>{{ pendientes }}</h3>
          <p>Pendientes</p>
        </div>
      </div>
      <div class="summary-card">
        <div class="card-icon resolved">✅</div>
        <div class="card-content">
          <h3>{{ resueltos }}</h3>
          <p>Resueltos</p>
        </div>
      </div>
      <div class="summary-card">
        <div class="card-icon closed">🔒</div>
        <div class="card-content">
          <h3>{{ cerrados }}</h3>
          <p>Cerrados</p>
        </div>
      </div>
    </div>

    <!-- Filtros -->
    <div class="filters">
      <select v-model="filtroEstado" @change="aplicarFiltros">
        <option value="">Todos los estados</option>
        <option value="PENDIENTE">Pendientes</option>
        <option value="EN_REVISION">En Revisión</option>
        <option value="RESUELTO">Resueltos</option>
        <option value="CERRADO">Cerrados</option>
      </select>
    </div>

    <!-- Tabla de Casos -->
    <div class="casos-table-container" v-if="!loading">
      <table class="casos-table">
        <thead>
          <tr>
            <th>ID Caso</th>
            <th>Cliente</th>
            <th>RUT</th>
            <th>Materia</th>
            <th>Monto</th>
            <th>Empresa</th>
            <th>Estado</th>
            <th>Fecha Ingreso</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="caso in casosFiltrados" :key="caso.case_id" class="caso-row">
            <td>{{ caso.case_id }}</td>
            <td>{{ caso.client_name }}</td>
            <td>{{ caso.rut_client }}</td>
            <td>{{ caso.materia }}</td>
            <td>${{ caso.monto_disputa.toLocaleString('es-CL') }}</td>
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
        </tbody>
      </table>
    </div>

    <div v-if="loading" class="loading">
      Cargando casos...
    </div>

    <div v-if="error" class="error">
      {{ error }}
    </div>
  </div>
</template>

<script>
import { casosAPI } from '../services/api'

export default {
  name: 'Dashboard',
  data() {
    return {
      casos: [],
      loading: true,
      error: null,
      filtroEstado: ''
    }
  },
  computed: {
    totalCasos() {
      return this.casos.length
    },
    pendientes() {
      return this.casos.filter(c => c.status === 'PENDIENTE').length
    },
    resueltos() {
      return this.casos.filter(c => c.status === 'RESUELTO').length
    },
    cerrados() {
      return this.casos.filter(c => c.status === 'CERRADO').length
    },
    casosFiltrados() {
      if (!this.filtroEstado) {
        return this.casos
      }
      return this.casos.filter(c => c.status === this.filtroEstado)
    }
  },
  mounted() {
    this.cargarCasos()
  },
  methods: {
    async cargarCasos() {
      this.loading = true
      this.error = null
      try {
        const response = await casosAPI.getCasos()
        this.casos = response.data
      } catch (err) {
        this.error = 'Error al cargar casos: ' + (err.message || 'Error desconocido')
        console.error(err)
      } finally {
        this.loading = false
      }
    },
    abrirCaso(caseId) {
      this.$router.push(`/caso/${caseId}`)
    },
    getStatusClass(status) {
      const classes = {
        'PENDIENTE': 'status-pending',
        'EN_REVISION': 'status-review',
        'RESUELTO': 'status-resolved',
        'CERRADO': 'status-closed'
      }
      return classes[status] || ''
    },
    aplicarFiltros() {
      // Los filtros se aplican automáticamente por computed
    }
  }
}
</script>

<style scoped>
.dashboard {
  width: 100%;
}

.dashboard h2 {
  margin-bottom: 2rem;
  color: #333;
  font-size: 2rem;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.summary-card {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  gap: 1rem;
}

.card-icon {
  font-size: 2.5rem;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
}

.card-icon.total {
  background: #e3f2fd;
}

.card-icon.pending {
  background: #fff3e0;
}

.card-icon.resolved {
  background: #e8f5e9;
}

.card-icon.closed {
  background: #f3e5f5;
}

.card-content h3 {
  font-size: 2rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 0.25rem;
}

.card-content p {
  color: #666;
  font-size: 0.9rem;
}

.filters {
  margin-bottom: 1.5rem;
}

.filters select {
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  background: white;
}

.casos-table-container {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.casos-table {
  width: 100%;
  border-collapse: collapse;
}

.casos-table thead {
  background: #f5f5f5;
}

.casos-table th {
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  color: #333;
  border-bottom: 2px solid #ddd;
}

.casos-table td {
  padding: 1rem;
  border-bottom: 1px solid #eee;
}

.caso-row:hover {
  background: #f9f9f9;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 500;
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
}
</style>

