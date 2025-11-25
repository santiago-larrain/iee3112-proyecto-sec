<template>
  <div id="app">
    <header class="app-header">
      <h1>Sistema de Análisis de Reclamos SEC</h1>
      <nav>
        <button 
          @click="toggleMode" 
          :class="['mode-toggle', mode === 'test' ? 'mode-test' : 'mode-validate']"
          :title="mode === 'test' ? 'Modo Test (Mock Data)' : 'Modo Validate (Casos Reales)'"
        >
          {{ mode === 'test' ? '🧪 Test' : '✅ Validate' }}
        </button>
        <router-link to="/">Dashboard</router-link>
        <button 
          @click="toggleAIChat" 
          class="ai-toggle-btn"
          :class="{ 'active': aiChatOpen }"
          title="Asistente IA"
        >
          🤖
        </button>
      </nav>
    </header>
    <main class="app-main" :class="{ 'with-chat': aiChatOpen }">
      <router-view />
    </main>
    <AIChatPanel :is-open="aiChatOpen" />
  </div>
</template>

<script>
import AIChatPanel from './components/AIChatPanel.vue'

export default {
  name: 'App',
  components: {
    AIChatPanel
  },
  data() {
    return {
      mode: 'validate', // Por defecto: validate (casos reales)
      aiChatOpen: false
    }
  },
  mounted() {
    // Cargar modo desde localStorage al iniciar
    const savedMode = localStorage.getItem('app_mode')
    if (savedMode) {
      this.mode = savedMode
    } else {
      localStorage.setItem('app_mode', this.mode)
    }
    
    // Cargar estado del chat desde localStorage
    const savedChatState = localStorage.getItem('ai_chat_open')
    if (savedChatState !== null) {
      this.aiChatOpen = savedChatState === 'true'
    }
  },
  methods: {
    toggleMode() {
      this.mode = this.mode === 'test' ? 'validate' : 'test'
      // Guardar en localStorage
      localStorage.setItem('app_mode', this.mode)
      // Recargar la página para aplicar el cambio
      window.location.reload()
    },
    toggleAIChat() {
      this.aiChatOpen = !this.aiChatOpen
      localStorage.setItem('ai_chat_open', this.aiChatOpen)
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background-color: #f5f5f5;
  color: #333;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.5rem 2rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
}

.app-header h1 {
  font-size: 1.5rem;
  font-weight: 600;
}

.app-header nav {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.app-header nav a {
  color: white;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.app-header nav a:hover {
  background-color: rgba(255,255,255,0.2);
}

.mode-toggle {
  background: rgba(255,255,255,0.2);
  color: white;
  border: 1px solid rgba(255,255,255,0.3);
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.2s;
}

.mode-toggle:hover {
  background: rgba(255,255,255,0.3);
  transform: translateY(-1px);
}

.mode-toggle.mode-test {
  background: rgba(255, 193, 7, 0.3);
  border-color: rgba(255, 193, 7, 0.5);
}

.mode-toggle.mode-validate {
  background: rgba(76, 175, 80, 0.3);
  border-color: rgba(76, 175, 80, 0.5);
}

.app-main {
  flex: 1;
  padding: 2rem;
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
  margin-top: 70px; /* Espacio para header fijo */
  transition: margin-right 0.3s ease;
}

.app-main.with-chat {
  padding-right: 400px; /* Espacio para el panel de chat */
}

.ai-toggle-btn {
  background: rgba(255,255,255,0.2);
  color: white;
  border: 1px solid rgba(255,255,255,0.3);
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1.2rem;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 44px;
  height: 44px;
}

.ai-toggle-btn:hover {
  background: rgba(255,255,255,0.3);
  transform: translateY(-1px);
}

.ai-toggle-btn.active {
  background: rgba(255,255,255,0.4);
  border-color: rgba(255,255,255,0.6);
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

@media (max-width: 768px) {
  .app-main.with-chat {
    margin-right: 0;
  }
}
</style>

