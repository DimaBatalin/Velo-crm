<script setup>
import { computed } from 'vue'
import { useSyncedForm } from '../composables/useSyncedForm.js'
import { useEnums } from '../composables/useEnums.js'

const props = defineProps({
  visible: Boolean,
  modelValue: Object,
  bikes: {
    type: Array,
    default: () => [],
  },
  people: {
    type: Array,
    default: () => [],
  },
  title: {
    type: String,
    default: 'Новая аренда',
  },
  submitLabel: {
    type: String,
    default: 'Создать аренду',
  },
})

const emit = defineEmits([
  'update:modelValue',
  'save',
  'close',
])

const defaults = {
  id: undefined,
  bike_id: null,
  person_id: null,
  price_per_day: '',

  started_at: '',
  ended_at: '',

  status: 'active',
}

const { enums } = useEnums()

const FALLBACK_RENTAL_STATUSES = [
  { value: 'active', label: 'Активна' },
  { value: 'returned', label: 'Возвращена' },
  { value: 'overdue', label: 'Просрочена' },
]

const statusOptions = computed(() =>
  enums.value?.rental_status?.length ? enums.value.rental_status : FALLBACK_RENTAL_STATUSES,
)

const { localForm } = useSyncedForm(
    () => props.modelValue,
    (value) => emit('update:modelValue', value),
    defaults,
    (value) => ({
      id: value.id,
      bike_id: value.bike_id ?? null,
      person_id: value.person_id ?? null,

      price_per_day: value.price_per_day ?? '',

      started_at: value.started_at
          ? value.started_at.slice(0, 16)
          : '',

      ended_at: value.ended_at
          ? value.ended_at.slice(0, 16)
          : '',

      status: value.status ?? 'active',
    }),
)

const availableBikes = computed(() =>
    props.bikes.filter(
        bike =>
            bike.status === 'ready' ||
            bike.id === localForm.value.bike_id,
    ),
)

// Аренду можно оформить только активному клиенту (не заблокированному,
// не архивному, не уволенному). Текущего выбранного оставляем в списке,
// чтобы при редактировании старой аренды форма не «теряла» клиента.
const availablePeople = computed(() =>
    props.people.filter(
        person =>
            person.status === 'active' ||
            person.id === localForm.value.person_id,
    ),
)

function displayBike(bike) {
  if (!bike) return ''

  const typeIcon =
      bike.type === 'Электровелосипед'
          ? '⚡'
          : '🔧'

  return `${typeIcon} ${bike.serial_number} — ${bike.brand || ''} ${bike.model || ''}`.trim()
}

function displayPerson(person) {
  if (!person) return ''

  return (
      [person.last_name, person.first_name, person.middle_name]
          .filter(Boolean)
          .join(' ') ||
      `#${person.id}`
  )
}

function onSubmit() {
  emit('update:modelValue', {
    ...localForm.value,

    started_at: localForm.value.started_at
        ? new Date(localForm.value.started_at).toISOString()
        : null,

    ended_at: localForm.value.ended_at
        ? new Date(localForm.value.ended_at).toISOString()
        : null,
  })

  emit('save')
}
</script>

<template>
  <div
      v-if="visible"
      class="form-panel"
  >
    <div class="form-header">
      <h2 class="form-title">
        {{ title }}
      </h2>

      <button
          class="btn-ghost"
          type="button"
          @click="emit('close')"
      >
        ✕ Закрыть
      </button>
    </div>

    <form @submit.prevent="onSubmit">
      <div class="form-grid">

        <label class="field">
          <span class="field-label">
            Велосипед
            <span class="req">*</span>
          </span>

          <select
              v-model.number="localForm.bike_id"
              required
          >
            <option :value="null">
              Выберите велосипед
            </option>

            <option
                v-for="bike in availableBikes"
                :key="bike.id"
                :value="bike.id"
            >
              {{ displayBike(bike) }}
            </option>
          </select>
        </label>

        <label class="field">
          <span class="field-label">
            Клиент
            <span class="req">*</span>
          </span>

          <select
              v-model.number="localForm.person_id"
              required
          >
            <option :value="null">
              Выберите клиента
            </option>

            <option
                v-for="person in availablePeople"
                :key="person.id"
                :value="person.id"
            >
              {{ displayPerson(person) }}
            </option>
          </select>
        </label>

        <label class="field">
          <span class="field-label">
            Цена в день (₽)
          </span>

          <input
              v-model="localForm.price_per_day"
              type="number"
              min="0"
              step="0.01"
              placeholder="Например: 500"
          />
        </label>

        <label class="field">
          <span class="field-label">
            Статус
          </span>

          <select v-model="localForm.status">
            <option v-for="opt in statusOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
        </label>

        <label class="field">
          <span class="field-label">
            Дата начала
          </span>

          <input
              v-model="localForm.started_at"
              type="datetime-local"
          />
        </label>

        <label class="field">
          <span class="field-label">
            Дата окончания
          </span>

          <input
              v-model="localForm.ended_at"
              type="datetime-local"
          />
        </label>

      </div>

      <div class="form-actions">
        <button
            type="submit"
            class="btn-primary"
        >
          {{ submitLabel }}
        </button>

        <button
            type="button"
            class="btn-ghost"
            @click="emit('close')"
        >
          Отмена
        </button>
      </div>
    </form>
  </div>
</template>
