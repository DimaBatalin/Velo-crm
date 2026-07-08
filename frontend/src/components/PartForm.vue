<script setup>
import { computed } from 'vue'
import { useSyncedForm } from '../composables/useSyncedForm.js'
import { useEnums } from '../composables/useEnums.js'

const props = defineProps({
  visible: Boolean,
  modelValue: Object,
  title: { type: String, default: 'Новая запчасть' },
  submitLabel: { type: String, default: 'Добавить запчасть' },
})
const emit = defineEmits(['update:modelValue', 'save', 'close'])

const { enums } = useEnums()

const FALLBACK_OWNER_TYPES = [
  { value: 'kirill', label: 'Кирилл' },
  { value: 'vitaly', label: 'Виталий' },
]

const ownerOptions = computed(() =>
  enums.value?.owner_type?.length ? enums.value.owner_type : FALLBACK_OWNER_TYPES,
)

const defaults = {
  name: '',
  category: '',
  sku: '',
  supplier: '',
  purchase_price: '',
  sale_price: '',
  quantity: 1,
  min_stock: 2,
  owner: 'kirill',
  notes: '',
}

const { localForm } = useSyncedForm(
  () => props.modelValue,
  (value) => emit('update:modelValue', value),
  defaults,
  (value) => ({
    name: value.name ?? '',
    category: value.category ?? '',
    sku: value.sku ?? '',
    supplier: value.supplier ?? '',
    purchase_price: value.purchase_price ?? '',
    sale_price: value.sale_price ?? '',
    quantity: value.quantity ?? 1,
    min_stock: value.min_stock ?? 2,
    owner: value.owner ?? 'kirill',
    notes: value.notes ?? '',
  }),
)

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
        <label class="field full-width">
          <span class="field-label">Наименование <span class="req">*</span></span>
          <input v-model="localForm.name" required placeholder="Камера 29\"" />
        </label>
        <label class="field">
          <span class="field-label">Категория</span>
          <input v-model="localForm.category" placeholder="Расходники, Трансмиссия..." />
        </label>
        <label class="field">
          <span class="field-label">Артикул (SKU)</span>
          <input v-model="localForm.sku" placeholder="ABC-123" />
        </label>
        <label class="field">
          <span class="field-label">Поставщик</span>
          <input v-model="localForm.supplier" placeholder="Название поставщика" />
        </label>
        <label class="field">
          <span class="field-label">Закупочная цена, ₽ <span class="req">*</span></span>
          <input v-model.number="localForm.purchase_price" type="number" min="0" step="0.01" required placeholder="0" />
        </label>
        <label class="field">
          <span class="field-label">Цена продажи, ₽ <span class="req">*</span></span>
          <input v-model.number="localForm.sale_price" type="number" min="0" step="0.01" required placeholder="0" />
        </label>
        <label class="field">
          <span class="field-label">Количество, шт.</span>
          <input v-model.number="localForm.quantity" type="number" min="0" placeholder="1" />
        </label>
        <label class="field">
          <span class="field-label">Мин. остаток, шт.</span>
          <input v-model.number="localForm.min_stock" type="number" min="0" placeholder="2" />
        </label>
        <label class="field">
          <span class="field-label">Принадлежность</span>
          <select v-model="localForm.owner">
            <option v-for="opt in ownerOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
        </label>
        <label class="field full-width">
          <span class="field-label">Заметки</span>
          <textarea v-model="localForm.notes" rows="2" placeholder="Дополнительно..."></textarea>
        </label>
      </div>

      <div class="form-actions">
        <button type="submit" class="btn-primary">{{ submitLabel }}</button>
        <button type="button" class="btn-ghost" @click="emit('close')">Отмена</button>
      </div>
    </form>
  </div>
</template>
