<template>
  <div class="sidebar">
    <div class="sidebar-header">
      <h2>Panel SEC</h2>
    </div>
    
    <!-- Estadísticas -->
    <div class="stats-section">
      <h3>Estadísticas</h3>
      <div class="stat-card">
        <div class="stat-number">{{ totalCasos }}</div>
        <div class="stat-label">Total Casos</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">{{ pendientes }}</div>
        <div class="stat-label">Pendientes</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">{{ resueltos }}</div>
        <div class="stat-label">Resueltos</div>
      </div>
    </div>
    
    <!-- Sección de Análisis (Futuro) -->
    <div class="analytics-section">
      <h3>Análisis</h3>
      <div class="analytics-placeholder">
        <p>Próximamente: Análisis de reclamos</p>
        <ul class="analytics-features">
          <li>Análisis por empresa</li>
          <li>Tipos de reclamos</li>
          <li>Mapa de calor por comuna</li>
          <li>Detección de patrones</li>
          <li>Casos similares</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Sidebar',
  props: {
    totalCasos: {
      type: Number,
      default: 0
    },
    pendientes: {
      type: Number,
      default: 0
    },
    resueltos: {
      type: Number,
      default: 0
    }
  }
}
</script>

<style scoped>
.sidebar {
  width: 300px;
  background: #f5f5f5;
  border-right: 1px solid #ddd;
  padding: 1.5rem;
  height: calc(100vh - 70px); /* Restar altura del header */
  overflow-y: auto;
  position: fixed;
  left: 0;
  top: 70px; /* Empezar después del header (altura aproximada del header) */
  z-index: 10;
}

.sidebar-header {
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #667eea;
}

.sidebar-header h2 {
  margin: 0;
  color: #333;
  font-size: 1.5rem;
}

.stats-section {
  margin-bottom: 2rem;
}

.stats-section h3 {
  font-size: 1rem;
  color: #666;
  margin-bottom: 1rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-card {
  background: white;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 0.75rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 6px rgba(0,0,0,0.15);
}

.stat-number {
  font-size: 2rem;
  font-weight: 600;
  color: #667eea;
  margin-bottom: 0.25rem;
}

.stat-label {
  font-size: 0.85rem;
  color: #666;
}

.analytics-section {
  margin-top: 2rem;
}

.analytics-section h3 {
  font-size: 1rem;
  color: #666;
  margin-bottom: 1rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.analytics-placeholder {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  border: 2px dashed #ddd;
}

.analytics-placeholder p {
  color: #999;
  font-style: italic;
  margin-bottom: 1rem;
}

.analytics-features {
  list-style: none;
  padding: 0;
  margin: 0;
}

.analytics-features li {
  padding: 0.5rem 0;
  color: #666;
  font-size: 0.9rem;
  border-bottom: 1px solid #eee;
}

.analytics-features li:last-child {
  border-bottom: none;
}

.analytics-features li:before {
  content: "→ ";
  color: #667eea;
  font-weight: bold;
}
</style>

