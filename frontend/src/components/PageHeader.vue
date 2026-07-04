<script setup>
const props = defineProps({
  pageTitle: String,
  pageSubtitle: String,
  hasAddButton: Boolean,
  addButtonLabel: String,
})
const emit = defineEmits(["openCreateForm"])
</script>

<template>
  <div class="page-header">
    <div>
      <h1 class="page-title">{{ pageTitle }}</h1>
      <p class="page-sub">{{ pageSubtitle }}</p>
    </div>

    <button
      v-if="hasAddButton"
      class="btn-primary"
      @click="emit('openCreateForm')"
    >
      + {{ addButtonLabel }}
    </button>
  </div>
</template>
