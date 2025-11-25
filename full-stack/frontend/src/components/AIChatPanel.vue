<template>
  <div v-if="isOpen" class="ai-chat-panel" :class="{ 'collapsed': isCollapsed }">
    <div class="chat-header">
      <div class="chat-title">
        <span class="ai-icon">🤖</span>
        <span>Asistente IA</span>
      </div>
      <button @click="toggleCollapse" class="collapse-btn" :title="isCollapsed ? 'Expandir' : 'Colapsar'">
        {{ isCollapsed ? '◀' : '▶' }}
      </button>
    </div>
    
    <div v-if="!isCollapsed" class="chat-content">
      <div class="chat-messages" ref="messagesContainer">
        <div 
          v-for="(message, index) in messages" 
          :key="index"
          :class="['message', message.type]"
        >
          <div class="message-avatar">
            <span v-if="message.type === 'user'">👤</span>
            <span v-else>🤖</span>
          </div>
          <div class="message-content">
            <div class="message-text">{{ message.text }}</div>
            <div class="message-time">{{ formatTime(message.timestamp) }}</div>
          </div>
        </div>
      </div>
      
      <div class="chat-input-container">
        <input
          v-model="inputMessage"
          @keyup.enter="sendMessage"
          type="text"
          placeholder="Escribe tu mensaje..."
          class="chat-input"
          :disabled="isLoading"
        />
        <button 
          @click="sendMessage" 
          class="send-btn"
          :disabled="!inputMessage.trim() || isLoading"
        >
          ➤
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AIChatPanel',
  props: {
    isOpen: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      isCollapsed: false,
      messages: [
        {
          type: 'ai',
          text: '¡Hola! Soy tu asistente IA. Puedo ayudarte a analizar casos, revisar documentos y generar resoluciones. ¿En qué puedo ayudarte?',
          timestamp: new Date()
        }
      ],
      inputMessage: '',
      isLoading: false
    }
  },
  watch: {
    isOpen(newVal) {
      if (newVal && this.isCollapsed) {
        this.isCollapsed = false
      }
    },
    messages: {
      handler() {
        this.$nextTick(() => {
          this.scrollToBottom()
        })
      },
      deep: true
    }
  },
  methods: {
    toggleCollapse() {
      this.isCollapsed = !this.isCollapsed
    },
    sendMessage() {
      if (!this.inputMessage.trim() || this.isLoading) return
      
      // Agregar mensaje del usuario
      const userMessage = {
        type: 'user',
        text: this.inputMessage.trim(),
        timestamp: new Date()
      }
      this.messages.push(userMessage)
      
      // Limpiar input
      const messageText = this.inputMessage.trim()
      this.inputMessage = ''
      this.isLoading = true
      
      // Simular respuesta de IA (template constante por ahora)
      setTimeout(() => {
        const aiResponse = this.generateAIResponse(messageText)
        this.messages.push({
          type: 'ai',
          text: aiResponse,
          timestamp: new Date()
        })
        this.isLoading = false
      }, 500)
    },
    generateAIResponse(userMessage) {
      // Template constante para simular respuesta de IA
      const lowerMessage = userMessage.toLowerCase()
      
      // Respuestas contextuales básicas
      if (lowerMessage.includes('caso') || lowerMessage.includes('reclamo')) {
        return 'Puedo ayudarte a analizar el caso. Revisa el checklist en la Sección C para ver el estado de validación. Si necesitas generar una resolución, usa la Sección D.'
      }
      
      if (lowerMessage.includes('documento') || lowerMessage.includes('archivo')) {
        return 'Los documentos se gestionan en la Sección B. Puedes re-clasificar documentos si es necesario, y el checklist se actualizará automáticamente.'
      }
      
      if (lowerMessage.includes('checklist') || lowerMessage.includes('validación')) {
        return 'El checklist en la Sección C muestra el estado de cumplimiento de los requisitos. Los items en verde ✅ cumplen, en rojo ❌ no cumplen, y en amarillo ⚠️ requieren revisión manual.'
      }
      
      if (lowerMessage.includes('resolución') || lowerMessage.includes('resolver')) {
        return 'Puedes generar una resolución en la Sección D. El sistema generará automáticamente un borrador basado en el estado del checklist. Puedes editarlo antes de cerrar el caso.'
      }
      
      // Respuesta genérica
      return 'Entiendo tu consulta. Estoy aquí para ayudarte con el análisis de casos, revisión de documentos, validación de requisitos y generación de resoluciones. ¿Hay algo específico en lo que pueda ayudarte?'
    },
    formatTime(timestamp) {
      const date = new Date(timestamp)
      return date.toLocaleTimeString('es-CL', { 
        hour: '2-digit', 
        minute: '2-digit' 
      })
    },
    scrollToBottom() {
      const container = this.$refs.messagesContainer
      if (container) {
        container.scrollTop = container.scrollHeight
      }
    }
  }
}
</script>

<style scoped>
.ai-chat-panel {
  position: fixed;
  right: 0;
  top: 70px; /* Altura del header */
  bottom: 0;
  width: 380px;
  background: white;
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  z-index: 90;
  transition: transform 0.3s ease;
  border-left: 1px solid #e0e0e0;
  transform: translateX(0);
}

.ai-chat-panel.collapsed {
  transform: translateX(calc(100% - 50px));
}

.chat-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.chat-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
}

.ai-icon {
  font-size: 1.2rem;
}

.collapse-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  width: 32px;
  height: 32px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
  font-size: 0.9rem;
}

.collapse-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.chat-content {
  display: flex;
  flex-direction: column;
  flex: 1;
  height: calc(100vh - 70px - 60px); /* Altura total menos header y chat-header */
  overflow: hidden;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: #555;
}

.message {
  display: flex;
  gap: 0.75rem;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  flex-shrink: 0;
}

.message.user .message-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.message.ai .message-avatar {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.message-content {
  flex: 1;
  max-width: calc(100% - 50px);
}

.message.user .message-content {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.message.ai .message-content {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.message-text {
  padding: 0.75rem 1rem;
  border-radius: 12px;
  word-wrap: break-word;
  line-height: 1.5;
}

.message.user .message-text {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-bottom-right-radius: 4px;
}

.message.ai .message-text {
  background: #f0f0f0;
  color: #333;
  border-bottom-left-radius: 4px;
}

.message-time {
  font-size: 0.75rem;
  color: #999;
  margin-top: 0.25rem;
  padding: 0 0.5rem;
}

.chat-input-container {
  padding: 1rem;
  border-top: 1px solid #e0e0e0;
  background: white;
  display: flex;
  gap: 0.5rem;
}

.chat-input {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 1px solid #ddd;
  border-radius: 20px;
  font-size: 0.9rem;
  outline: none;
  transition: border-color 0.2s;
}

.chat-input:focus {
  border-color: #667eea;
}

.chat-input:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.send-btn {
  width: 40px;
  height: 40px;
  border: none;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  transition: transform 0.2s, opacity 0.2s;
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  transform: scale(1.1);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Responsive */
@media (max-width: 1024px) {
  .ai-chat-panel {
    width: 320px;
  }
}

@media (max-width: 768px) {
  .ai-chat-panel {
    width: 100%;
  }
  
  .ai-chat-panel.collapsed {
    transform: translateX(calc(100% - 50px));
  }
}
</style>

