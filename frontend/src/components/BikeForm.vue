<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  visible: Boolean,
  modelValue: Object,
  title: { type: String, default: 'Новый велосипед' },
  submitLabel: { type: String, default: 'Сохранить' },
  showStatus: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'save', 'close'])

const localForm = ref({
  id: undefined,
  type: 'Электровелосипед',
  brand: '',
  model: '',
  serial_number: '',
  color: '',
  notes: '',
  owner_type: null,
  status: 'ready',
})

watch(
    () => props.modelValue,
    (value) => {
      if (value) {
        localForm.value = {
          id: value.id,
          type: value.type ?? 'Электровелосипед',
          brand: value.brand ?? '',
          model: value.model ?? '',
          serial_number: value.serial_number ?? '',
          color: value.color ?? '',
          notes: value.notes ?? '',
          owner_type: value.owner_type ?? null,
          status: value.status ?? 'ready',
        }
      }
    },
    { immediate: true, deep: true },
)

watch(
    localForm,
    (value) => emit('update:modelValue', { ...value }),
    { deep: true },
)

const bikeTypeOptions = [
  { value: 'Электровелосипед', label: '⚡ Электровелосипед' },
  { value: 'Механический велосипед', label: '🔧 Механический велосипед' },
]

const ownerTypeOptions = [
  { value: 'Великий мастер', label: 'Великий мастер' },
  { value: 'Виталий', label: 'Виталий' },
]

const statusOptions = [
  { value: 'ready', label: 'Готов' },
  { value: 'rented', label: 'В аренде' },
  { value: 'repair', label: 'Ремонт' },
  { value: 'stolen', label: 'Кража' },
]

function onSubmit() {
  emit('save')
}
</script>

<template>
  <div v-if="visible" class="form-panel">
    <div class="form-header">
      <h2 class="form-title">{{ title }}</h2>
      <button class="btn-ghost" type="button" @click="emit('close')">✕ Закрыть</button>
    </div>

    <form @submit.prevent="onSubmit">
      <div class="form-grid">
        <!-- Тип велосипеда — первым, занимает всю ширину -->
        <label class="field full-width">
          <span class="field-label">Тип велосипеда <span class="req">*</span></span>
          <div class="type-toggle">
            <button
                v-for="opt in bikeTypeOptions"
                :key="opt.value"
                type="button"
                :class="['type-btn', { active: localForm.type === opt.value }]"
                @click="localForm.type = opt.value"
            >
              {{ opt.label }}
            </button>
          </div>
        </label>

        <label class="field">
          <span class="field-label">VIN / Серийный номер <span class="req">*</span></span>
          <input v-model="localForm.serial_number" required placeholder="VIN-00000" />
        </label>
        <label class="field">
          <span class="field-label">Марка</span>
          <input v-model="localForm.brand" placeholder="Trek, Giant, Merida..." />
        </label>
        <label class="field">
          <span class="field-label">Модель</span>
          <input v-model="localForm.model" placeholder="Marlin 5, 2022" />
        </label>
        <label class="field">
          <span class="field-label">Цвет</span>
          <input v-model="localForm.color" placeholder="Чёрный" />
        </label>
        <label class="field">
          <span class="field-label">Арендодатель</span>
          <select v-model="localForm.owner_type">
            <option :value="null">Не указан</option>
            <option v-for="opt in ownerTypeOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </label>
        <label v-if="showStatus" class="field">
          <span class="field-label">Статус</span>
          <select v-model="localForm.status">
            <option v-for="opt in statusOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </label>
        <label class="field full-width">
          <span class="field-label">Заметки</span>
          <textarea v-model="localForm.notes" rows="3" placeholder="Особенности, повреждения..."></textarea>
        </label>
      </div>
      <div class="form-actions">
        <button type="submit" class="btn-primary">{{ submitLabel }}</button>
        <button type="button" class="btn-ghost" @click="emit('close')">Отмена</button>
      </div>
    </form>
  </div>
</template>

<style scoped>
.type-toggle {
  display: flex;
  gap: 10px;
}

.type-btn {
  flex: 1;
  padding: 10px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  background: #fff;
  font-size: 0.9rem;
  font-weight: 500;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.15s;
  font-family: inherit;
}

.type-btn:hover {
  border-color: #7c3aed;
  color: #7c3aed;
}

.type-btn.active {
  border-color: #7c3aed;
  background: #ede9fe;
  color: #5b21b6;
  font-weight: 700;
}
</style>