<script setup>
defineProps({
  hasSearch: Boolean,
  searchQuery: String,
  searchPlaceholder: String,
  toast: Object,
})
const emit = defineEmits(['update:searchQuery', 'toggleMenu'])
</script>

<template>
  <div class="topbar">
    <button class="hamburger" type="button" @click.stop="emit('toggleMenu')" aria-label="Меню">
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
        <rect y="2"  width="18" height="2" rx="1" fill="currentColor"/>
        <rect y="8"  width="18" height="2" rx="1" fill="currentColor"/>
        <rect y="14" width="18" height="2" rx="1" fill="currentColor"/>
      </svg>
    </button>

    <div class="search-wrap">
      <span class="search-icon">
        <svg width="14" height="14" viewBox="0 0 20 20" fill="none">
          <circle cx="9" cy="9" r="6" stroke="#9ca3af" stroke-width="2"/>
          <path d="M13.5 13.5L17 17" stroke="#9ca3af" stroke-width="2" stroke-linecap="round"/>
        </svg>
      </span>
      <input
        v-if="hasSearch"
        type="search"
        :value="searchQuery"
        @input="emit('update:searchQuery', $event.target.value)"
        class="search-input"
        :placeholder="searchPlaceholder"
      />
      <input
        v-else
        type="search"
        class="search-input"
        placeholder="Быстрый поиск (ФИО, VIN, телефон)..."
        disabled
      />
    </div>

    <transition name="fade">
      <div v-if="toast?.text" :class="['toast', `toast-${toast.type}`]">{{ toast.text }}</div>
    </transition>
  </div>
</template>
