<template>
  <div class="dashboard-container">
    <!-- Sidebar -->
    <Sidebar
      :total-casos="totalCasos"
      :pendientes="pendientes"
      :resueltos="resueltos"
      :cerrados="cerrados"
    />
    
    <!-- Main Content -->
    <div class="main-content">
      <h2>Panel de Reclamos</h2>
      
      <!-- Fixed Search and Filter Bar -->
      <div class="fixed-controls-bar">
        <div class="controls-container">
          <SearchBar @search="onSearch" />
          <div class="filter-buttons">
            <FilterButton 
              label="Estado" 
              :options="estadoOptions" 
              :selected="filtroEstado"
              @select="onEstadoFilter"
            />
            <FilterButton 
              label="Caso" 
              :options="tipoCasoOptions" 
              :selected="filtroTipoCaso"
              @select="onTipoCasoFilter"
            />
          </div>
        </div>
      </div>
      
      <!-- Cases Table -->
      <div class="table-container" v-if="!loading">
        <CasesTable
          :casos="casos"
          :sort-by="sortBy"
          :sort-order="sortOrder"
          @sort="onSort"
          @open-case="abrirCaso"
        />
        <div class="pagination-info">
          Mostrando {{ casos.length }} de {{ totalCasos }} casos
        </div>
      </div>
      
      <div v-if="loading" class="loading">
        Cargando casos...
      </div>
      
      <div v-if="error" class="error">
        {{ error }}
      </div>
    </div>
  </div>
</template>

<script>
import { casosAPI } from '../services/api'
import Sidebar from '../components/Sidebar.vue'
import SearchBar from '../components/SearchBar.vue'
import FilterButton from '../components/FilterButton.vue'
import CasesTable from '../components/CasesTable.vue'

export default {
  name: 'Dashboard',
  components: {
    Sidebar,
    SearchBar,
    FilterButton,
    CasesTable
  },
  data() {
    return {
      casos: [],
      allCasos: [], // Todos los casos sin paginación (para estadísticas)
      loading: true,
      error: null,
      searchQuery: '',
      filtroEstado: '',
      filtroTipoCaso: '',
      sortBy: null,
      sortOrder: 'asc',
      page: 1,
      pageSize: 100, // Parametrizable
      estadoOptions: [
        { value: '', label: 'Todos' },
        { value: 'PENDIENTE', label: 'Pendientes' },
        { value: 'CERRADO', label: 'Cerrados' }
      ],
      tipoCasoOptions: [
        { value: '', label: 'Todos' },
        { value: 'CNR', label: 'CNR' },
        { value: 'CORTE_SUMINISTRO', label: 'Corte Suministro' },
        { value: 'DAÑO_EQUIPOS', label: 'Daño Equipos' },
        { value: 'ATENCION_COMERCIAL', label: 'Atención Comercial' },
        { value: 'OTROS', label: 'Otros' }
      ]
    }
  },
  computed: {
    totalCasos() {
      return this.allCasos.length
    },
    pendientes() {
      return this.allCasos.filter(c => c.status === 'PENDIENTE').length
    },
    resueltos() {
      return this.allCasos.filter(c => c.status === 'RESUELTO').length
    },
    cerrados() {
      return this.allCasos.filter(c => c.status === 'CERRADO').length
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
        // Cargar todos los casos sin filtros para estadísticas (una sola vez al inicio)
        // Usar page_size máximo permitido (1000) en lugar de 10000
        if (this.allCasos.length === 0) {
          try {
            const allResponse = await casosAPI.getCasos('', '', '', null, 'asc', 1, 1000)
            this.allCasos = allResponse.data || []
          } catch (err) {
            console.warn('Error cargando todos los casos para estadísticas:', err)
            this.allCasos = []
          }
        }
        
        // Cargar casos paginados con filtros para la tabla
        const response = await casosAPI.getCasos(
          this.searchQuery || '',
          this.filtroTipoCaso || '',
          this.filtroEstado || '',
          this.sortBy || null,
          this.sortOrder || 'asc',
          this.page || 1,
          this.pageSize || 100
        )
        this.casos = response.data || []
      } catch (err) {
        this.error = 'Error al cargar casos: ' + (err.message || 'Error desconocido')
        console.error('Error completo:', err)
        console.error('Response:', err.response)
        this.casos = []
      } finally {
        this.loading = false
      }
    },
    async onSearch(query) {
      this.searchQuery = query
      this.page = 1 // Resetear a primera página
      await this.cargarCasos()
    },
    async onEstadoFilter(value) {
      this.filtroEstado = value
      this.page = 1
      await this.cargarCasos()
    },
    async onTipoCasoFilter(value) {
      this.filtroTipoCaso = value
      this.page = 1
      await this.cargarCasos()
    },
    async onSort(column) {
      if (this.sortBy === column) {
        // Si ya está ordenado por esta columna, cambiar el orden
        this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc'
      } else {
        this.sortBy = column
        this.sortOrder = 'asc'
      }
      await this.cargarCasos()
    },
    abrirCaso(caseId) {
      this.$router.push(`/caso/${caseId}`)
    }
  }
}
</script>

<style scoped>
.dashboard-container {
  display: flex;
  min-height: 100vh;
}

.main-content {
  flex: 1;
  margin-left: 300px;
  padding: 2rem;
  background: #fafafa;
  padding-top: 140px; /* Espacio para controles fijos */
}

.main-content h2 {
  margin-bottom: 2rem;
  color: #333;
  font-size: 2rem;
  position: sticky;
  top: 70px; /* Debajo del header */
  background: #fafafa;
  padding: 1rem 0;
  z-index: 5;
}

.fixed-controls-bar {
  position: fixed;
  top: 70px; /* Debajo del header */
  left: 300px; /* Después del sidebar */
  right: 0;
  transition: right 0.3s ease;
  background: white;
  padding: 1rem 2rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  z-index: 10;
}

.controls-container {
  display: flex;
  align-items: center;
  gap: 1rem;
  max-width: 1400px;
  margin: 0 auto;
}

.filter-buttons {
  display: flex;
  gap: 0.5rem;
}

.table-container {
  margin-top: 1rem;
}

.pagination-info {
  margin-top: 1rem;
  padding: 0.75rem;
  background: white;
  border-radius: 8px;
  text-align: center;
  color: #666;
  font-size: 0.9rem;
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
