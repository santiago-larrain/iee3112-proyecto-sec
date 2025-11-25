<template>
  <div class="filter-button-container">
    <button 
      @click="toggleDropdown" 
      :class="['filter-button', { 'active': isOpen || selected }]"
    >
      <span>{{ label }}</span>
      <span class="filter-value" v-if="selected">{{ selectedLabel }}</span>
      <span class="arrow" :class="{ 'open': isOpen }">▼</span>
    </button>
    <div v-if="isOpen" class="dropdown-menu">
      <div 
        v-for="option in options" 
        :key="option.value"
        @click="selectOption(option.value)"
        :class="['dropdown-item', { 'selected': option.value === selected }]"
      >
        {{ option.label }}
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'FilterButton',
  props: {
    label: {
      type: String,
      required: true
    },
    options: {
      type: Array,
      required: true
    },
    selected: {
      type: String,
      default: ''
    }
  },
  data() {
    return {
      isOpen: false
    }
  },
  computed: {
    selectedLabel() {
      const option = this.options.find(opt => opt.value === this.selected)
      return option ? option.label : ''
    }
  },
  mounted() {
    document.addEventListener('click', this.handleClickOutside)
  },
  beforeUnmount() {
    document.removeEventListener('click', this.handleClickOutside)
  },
  methods: {
    toggleDropdown() {
      this.isOpen = !this.isOpen
    },
    selectOption(value) {
      this.$emit('select', value)
      this.isOpen = false
    },
    handleClickOutside(event) {
      if (!this.$el.contains(event.target)) {
        this.isOpen = false
      }
    }
  }
}
</script>

<style scoped>
.filter-button-container {
  position: relative;
}

.filter-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: white;
  border: 2px solid #ddd;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.95rem;
  font-weight: 500;
  color: #333;
  transition: all 0.2s;
  white-space: nowrap;
}

.filter-button:hover {
  border-color: #667eea;
  background: #f5f5ff;
}

.filter-button.active {
  border-color: #667eea;
  background: #f0f0ff;
}

.filter-value {
  color: #667eea;
  font-weight: 600;
}

.arrow {
  font-size: 0.7rem;
  transition: transform 0.2s;
  color: #666;
}

.arrow.open {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + 0.5rem);
  left: 0;
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  min-width: 180px;
  z-index: 1000;
  max-height: 300px;
  overflow-y: auto;
}

.dropdown-item {
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: background 0.2s;
  font-size: 0.9rem;
}

.dropdown-item:hover {
  background: #f5f5f5;
}

.dropdown-item.selected {
  background: #e3f2fd;
  color: #1976d2;
  font-weight: 600;
}
</style>

