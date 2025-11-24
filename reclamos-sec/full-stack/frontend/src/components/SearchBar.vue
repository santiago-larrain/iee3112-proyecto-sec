<template>
  <div class="search-bar">
    <input
      type="text"
      v-model="searchQuery"
      @input="onSearch"
      placeholder="Buscar en reclamos..."
      class="search-input"
    />
    <button v-if="searchQuery" @click="clearSearch" class="clear-btn">×</button>
  </div>
</template>

<script>
export default {
  name: 'SearchBar',
  data() {
    return {
      searchQuery: '',
      searchTimeout: null
    }
  },
  methods: {
    onSearch() {
      // Debounce: esperar 300ms después de que el usuario deje de escribir
      clearTimeout(this.searchTimeout)
      this.searchTimeout = setTimeout(() => {
        this.$emit('search', this.searchQuery)
      }, 300)
    },
    clearSearch() {
      this.searchQuery = ''
      this.$emit('search', '')
    }
  },
  beforeUnmount() {
    clearTimeout(this.searchTimeout)
  }
}
</script>

<style scoped>
.search-bar {
  position: relative;
  flex: 1;
  max-width: 600px;
}

.search-input {
  width: 100%;
  padding: 0.75rem 2.5rem 0.75rem 1rem;
  border: 2px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: #667eea;
}

.clear-btn {
  position: absolute;
  right: 0.5rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #999;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  line-height: 1;
}

.clear-btn:hover {
  color: #667eea;
}
</style>

