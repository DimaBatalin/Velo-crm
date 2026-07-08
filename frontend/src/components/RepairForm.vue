<script setup>
import { computed, nextTick, reactive, ref, watch } from 'vue'
import { useEnums } from '../composables/useEnums.js'
import {
  addRepairPart,
  addRepairService,
  createPart,
  createService,
  getParts,
  getRepair,
  getRepairSummary,
  getServices,
  removeRepairPart,
  removeRepairService,
  updateRepair,
} from '../api/client'

const props = defineProps({
  visible: Boolean,
  modelValue: Object,
  title: { type: String, default: '' },
  submitLabel: { type: String, default: '' },
  bikes: { type: Array, default: () => [] },
  people: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:modelValue', 'save', 'saved', 'close'])

const { enums } = useEnums()

const FALLBACK_REPAIR_STATUSES = [
  { value: 'new', label: 'Новый' },
  { value: 'in_progress', label: 'В работе' },
  { value: 'waiting_parts', label: 'Ожидание запчастей' },
  { value: 'done', label: 'Выполнен' },
  { value: 'cancelled', label: 'Отменён' },
]
const FALLBACK_OWNER_TYPES = [
  { value: 'kirill', label: 'Кирилл' },
  { value: 'vitaly', label: 'Виталий' },
]

const repairStatusOptions = computed(() =>
  enums.value?.repair_status?.length ? enums.value.repair_status : FALLBACK_REPAIR_STATUSES,
)
const ownerOptions = computed(() =>
  enums.value?.owner_type?.length ? enums.value.owner_type : FALLBACK_OWNER_TYPES,
)

const createEmptyForm = () => ({
  id: null,
  bike_id: null,
  client_id: null,
  problem_description: '',
  status: 'new',
})

const form = ref(createEmptyForm())
const lastSyncedFormJson = ref(null)
const repairDetail = ref(null)
const summary = ref(null)
const servicesCatalog = ref([])
const partsCatalog = ref([])
const loading = ref(false)
const saving = ref(false)
const notice = ref('')
const activeTab = ref('overview')
const lastLoadedId = ref(null)
const syncLock = ref(false)
const serviceSearch = ref('')
const partSearch = ref('')
const showNewService = ref(false)
const showNewPart = ref(false)

const serviceDraft = reactive({
  service_id: null,
  price: '',
})

const partDraft = reactive({
  part_id: null,
  quantity: 1,
  sale_price: '',
  notes: '',
})

const newService = reactive({
  name: '',
  description: '',
  price: '',
})

const newPart = reactive({
  name: '',
  category: '',
  sku: '',
  purchase_price: '',
  sale_price: '',
  quantity: 1,
  owner: 'kirill',
  supplier: '',
  notes: '',
})

const repairId = computed(() => form.value.id ?? null)
const isEditing = computed(() => repairId.value !== null)
const dialogTitle = computed(() => props.title || (isEditing.value ? `Редактирование ремонта #${repairId.value}` : 'Новый ремонт'))
const primaryLabel = computed(() => props.submitLabel || (isEditing.value ? 'Сохранить изменения' : 'Создать ремонт'))

const selectedBike = computed(() => props.bikes.find(bike => bike.id === form.value.bike_id) || null)
const selectedPerson = computed(() => props.people.find(person => person.id === form.value.client_id) || null)

const repairServices = computed(() => repairDetail.value?.services || [])
const repairParts = computed(() => repairDetail.value?.parts || [])

const filteredServicesCatalog = computed(() => {
  const query = serviceSearch.value.trim().toLowerCase()
  if (!query) return servicesCatalog.value
  return servicesCatalog.value.filter(service =>
      [service.name, service.description, String(service.price)]
          .filter(Boolean)
          .some(value => String(value).toLowerCase().includes(query)),
  )
})

const filteredPartsCatalog = computed(() => {
  const query = partSearch.value.trim().toLowerCase()
  if (!query) return partsCatalog.value
  return partsCatalog.value.filter(part =>
      [part.name, part.category, part.sku, part.supplier, String(part.sale_price), String(part.quantity)]
          .filter(Boolean)
          .some(value => String(value).toLowerCase().includes(query)),
  )
})

const activeBikeSuggestions = computed(() => {
  if (!selectedBike.value) return []
  const rentals = Array.isArray(selectedBike.value.rentals) ? selectedBike.value.rentals : []
  return rentals
      .filter(rental => String(rental.status) === 'active' && rental.person)
      .map(rental => rental.person)
})

const activePersonSuggestions = computed(() => {
  if (!selectedPerson.value) return []
  const rentals = Array.isArray(selectedPerson.value.rentals) ? selectedPerson.value.rentals : []
  return rentals
      .filter(rental => String(rental.status) === 'active' && rental.bike)
      .map(rental => rental.bike)
})

function cloneForm(value) {
  return JSON.parse(JSON.stringify(value))
}

function cloneFormJson(value) {
  return JSON.stringify(value)
}

function currency(value) {
  const number = Number(value || 0)
  return `${number.toFixed(2).replace(/\.00$/, '')} ₽`
}

function displayBike(bike) {
  if (!bike) return '—'
  return `${bike.serial_number || `#${bike.id}`} ${bike.brand || ''} ${bike.model || ''}`.trim()
}

function displayPerson(person) {
  if (!person) return '—'
  return [person.last_name, person.first_name, person.middle_name].filter(Boolean).join(' ') || `#${person.id}`
}


function syncClientFromBike(bikeId) {
  if (!bikeId) return

  // Находим выбранный велосипед
  const selectedBike = props.bikes.find(bike => bike.id === bikeId)
  if (!selectedBike) return

  // Получаем все аренды велосипеда
  const rentals = Array.isArray(selectedBike.rentals) ? selectedBike.rentals : []

  // Сортируем аренды по дате создания (предполагаем, что есть поле created_at или start_date)
  // и берем последнюю (самую свежую)
  const sortedRentals = [...rentals].sort((a, b) => {
    // Пробуем разные возможные поля с датой
    const dateA = a.created_at || a.start_date || a.createdAt || a.startDate
    const dateB = b.created_at || b.start_date || b.createdAt || b.startDate
    if (!dateA && !dateB) return 0
    if (!dateA) return 1
    if (!dateB) return -1
    return new Date(dateB) - new Date(dateA)
  })

  // Берем последнюю аренду (первую после сортировки)
  const lastRental = sortedRentals[0]

  // Если есть аренда и у нее есть клиент (person)
  if (lastRental && lastRental.person) {
    const nextClientId = lastRental.person.id

    // Проверяем, не выбран ли уже этот клиент
    if (form.value.client_id === nextClientId) return

    // Устанавливаем блокировку, чтобы не вызвать обратную синхронизацию
    syncLock.value = true
    form.value.client_id = nextClientId

    // Показываем уведомление (опционально)
    notice.value = `Автоматически выбран клиент из последней аренды: ${displayPerson(lastRental.person)}`

    // Сбрасываем уведомление через 3 секунды
    setTimeout(() => {
      if (notice.value === `Автоматически выбран клиент из последней аренды: ${displayPerson(lastRental.person)}`) {
        notice.value = ''
      }
    }, 3000)

    nextTick(() => { syncLock.value = false })
  }
}

function syncBikeFromClient(clientId) {
  const suggestions = activePersonSuggestions.value
  if (suggestions.length !== 1) return
  const nextBikeId = suggestions[0].id
  if (form.value.bike_id === nextBikeId) return
  syncLock.value = true
  form.value.bike_id = nextBikeId
  nextTick(() => { syncLock.value = false })
}

async function loadCatalogs() {
  try {
    const [services, parts] = await Promise.all([
      getServices({ limit: 100 }),
      getParts({ limit: 100 }),
    ])
    servicesCatalog.value = services
    partsCatalog.value = parts
  } catch (error) {
    console.error('Не удалось загрузить справочники для ремонта', error)
    notice.value = 'Не удалось загрузить справочники.'
  }
}

async function loadRepairData(id) {
  if (!id) {
    repairDetail.value = null
    summary.value = null
    return
  }

  loading.value = true
  try {
    const [detail, repairSummary] = await Promise.all([
      getRepair(id),
      getRepairSummary(id),
    ])

    repairDetail.value = detail
    summary.value = repairSummary
    lastLoadedId.value = id

    syncLock.value = true
    form.value = {
      id: detail.id,
      bike_id: detail.bike_id,
      client_id: detail.client_id,
      problem_description: detail.problem_description ?? '',
      status: detail.status ?? 'new',
    }
    nextTick(() => { syncLock.value = false })
  } catch (error) {
    console.error('Не удалось загрузить ремонт', error)
    notice.value = 'Не удалось загрузить ремонт.'
  } finally {
    loading.value = false
  }
}

async function refreshAfterMutation() {
  await Promise.all([
    loadCatalogs(),
    loadRepairData(repairId.value),
  ])
}

watch(
    () => props.modelValue,
    async (value) => {
      if (!value) {
        form.value = createEmptyForm()
        lastSyncedFormJson.value = null
        repairDetail.value = null
        summary.value = null
        lastLoadedId.value = null
        return
      }

      syncLock.value = true
      const nextForm = {
        id: value.id ?? null,
        bike_id: value.bike_id ?? null,
        client_id: value.client_id ?? null,
        problem_description: value.problem_description ?? '',
        status: value.status ?? 'new',
      }
      const nextJson = JSON.stringify(nextForm)
      if (nextJson !== lastSyncedFormJson.value) {
        lastSyncedFormJson.value = nextJson
        form.value = nextForm
      }
      nextTick(() => { syncLock.value = false })

      if (value.id && value.id !== lastLoadedId.value) {
        await loadRepairData(value.id)
      }
    },
    { immediate: true, deep: true },
)

watch(
    () => props.visible,
    async (visible) => {
      if (!visible) return
      notice.value = ''
      await loadCatalogs()
      if (repairId.value) {
        await loadRepairData(repairId.value)
      }
    },
    { immediate: true },
)

watch(
    () => form.value.bike_id,
    () => {
      if (syncLock.value) return
      syncClientFromBike(form.value.bike_id)
    },
)

watch(
    () => form.value.client_id,
    () => {
      if (syncLock.value) return
      syncBikeFromClient(form.value.client_id)
    },
)

watch(
    form,
    (value) => {
      const json = cloneFormJson(value)
      if (json === lastSyncedFormJson.value) return
      lastSyncedFormJson.value = json
      emit('update:modelValue', JSON.parse(json))
    },
    { deep: true },
)

async function submitBaseRepair() {
  if (!repairId.value) {
    emit('save', {
      bike_id: form.value.bike_id,
      client_id: form.value.client_id,
      problem_description: form.value.problem_description.trim() || "",
    })
    return
  }

  saving.value = true
  try {
    await updateRepair(repairId.value, {
      problem_description: form.value.problem_description.trim(),
      status: form.value.status,
    })
    notice.value = 'Ремонт сохранён.'
    await loadRepairData(repairId.value)
    emit('saved', repairDetail.value)
  } catch (error) {
    console.error('Не удалось сохранить ремонт', error)
    notice.value = 'Не удалось сохранить ремонт.'
  } finally {
    saving.value = false
  }
}

async function addServiceToRepair() {
  if (!repairId.value) {
    notice.value = 'Сначала создайте ремонт.'
    return
  }
  if (!serviceDraft.service_id) {
    notice.value = 'Выберите услугу.'
    return
  }

  saving.value = true
  try {
    await addRepairService(repairId.value, {
      service_id: serviceDraft.service_id,
      price: serviceDraft.price !== '' ? Number(serviceDraft.price) : undefined,
    })
    serviceDraft.service_id = null
    serviceDraft.price = ''
    notice.value = 'Услуга добавлена в ремонт.'
    await refreshAfterMutation()
    emit('saved', repairDetail.value)
  } catch (error) {
    console.error('Не удалось добавить услугу', error)
    notice.value = 'Не удалось добавить услугу.'
  } finally {
    saving.value = false
  }
}

async function addNewServiceAndAttach() {
  console.log('addNewServiceAndAttach called');
  if (!repairId.value) {
    notice.value = 'Сначала создайте ремонт.'
    return
  }
  if (!newService.name.trim()) {
    notice.value = 'Введите название услуги.'
    return
  }

  saving.value = true
  try {
    const created = await createService({
      name: newService.name.trim(),
      description: newService.description.trim() || undefined,
      price: Number(newService.price || 0),
    })
    await addRepairService(repairId.value, { service_id: created.id })
    Object.assign(newService, { name: '', description: '', price: '' })
    showNewService.value = false
    notice.value = 'Новая услуга создана и добавлена в ремонт.'
    await refreshAfterMutation()
    emit('saved', repairDetail.value)
  } catch (error) {
    console.error('Не удалось создать услугу', error)
    notice.value = 'Не удалось создать услугу.'
  } finally {
    saving.value = false
  }
}

async function removeServiceEntry(entry) {
  if (!repairId.value) return
  saving.value = true
  try {
    await removeRepairService(repairId.value, entry.id)
    notice.value = 'Услуга удалена из ремонта.'
    await refreshAfterMutation()
    emit('saved', repairDetail.value)
  } catch (error) {
    console.error('Не удалось удалить услугу', error)
    notice.value = 'Не удалось удалить услугу.'
  } finally {
    saving.value = false
  }
}

async function addPartToRepair() {
  if (!repairId.value) {
    notice.value = 'Сначала создайте ремонт.'
    return
  }
  if (!partDraft.part_id) {
    notice.value = 'Выберите запчасть.'
    return
  }

  saving.value = true
  try {
    await addRepairPart(repairId.value, {
      part_id: partDraft.part_id,
      quantity: Number(partDraft.quantity || 1),
      sale_price: partDraft.sale_price !== '' ? Number(partDraft.sale_price) : undefined,
      notes: partDraft.notes.trim() || undefined,
    })
    partDraft.part_id = null
    partDraft.quantity = 1
    partDraft.sale_price = ''
    partDraft.notes = ''
    notice.value = 'Запчасть списана в ремонт.'
    await refreshAfterMutation()
    emit('saved', repairDetail.value)
  } catch (error) {
    console.error('Не удалось добавить запчасть', error)
    notice.value = 'Не удалось добавить запчасть.'
  } finally {
    saving.value = false
  }
}

async function addNewPartAndAttach() {
  if (!repairId.value) {
    notice.value = 'Сначала создайте ремонт.'
    return
  }
  if (!newPart.name.trim()) {
    notice.value = 'Введите название запчасти.'
    return
  }

  saving.value = true
  try {
    const created = await createPart({
      name: newPart.name.trim(),
      category: newPart.category.trim() || undefined,
      sku: newPart.sku.trim() || undefined,
      quantity: Number(newPart.quantity || 1),
      purchase_price: Number(newPart.purchase_price || 0),
      sale_price: Number(newPart.sale_price || 0),
      owner: newPart.owner,
      supplier: newPart.supplier.trim() || undefined,
      notes: newPart.notes.trim() || undefined,
    })

    await addRepairPart(repairId.value, {
      part_id: created.id,
      quantity: Number(newPart.quantity || 1),
      sale_price: Number(newPart.sale_price || 0),
    })

    Object.assign(newPart, {
      name: '',
      category: '',
      sku: '',
      purchase_price: '',
      sale_price: '',
      quantity: 1,
      owner: 'kirill',
      supplier: '',
      notes: '',
    })
    showNewPart.value = false
    notice.value = 'Новая запчасть создана и списана в ремонт.'
    await refreshAfterMutation()
    emit('saved', repairDetail.value)
  } catch (error) {
    console.error('Не удалось создать запчасть', error)
    notice.value = 'Не удалось создать запчасть.'
  } finally {
    saving.value = false
  }
}

async function removePartEntry(entry) {
  if (!repairId.value) return
  saving.value = true
  try {
    await removeRepairPart(repairId.value, entry.id)
    notice.value = 'Запчасть удалена из ремонта.'
    await refreshAfterMutation()
    emit('saved', repairDetail.value)
  } catch (error) {
    console.error('Не удалось удалить запчасть', error)
    notice.value = 'Не удалось удалить запчасть.'
  } finally {
    saving.value = false
  }
}

function applySuggestedBike(bikeId) {
  syncLock.value = true
  form.value.bike_id = bikeId
  nextTick(() => { syncLock.value = false })
}

function applySuggestedPerson(personId) {
  syncLock.value = true
  form.value.client_id = personId
  nextTick(() => { syncLock.value = false })
}

function formatRubles(value) {
  return currency(value ?? 0)
}
</script>

<template>
  <div v-if="visible" class="form-panel repair-panel">
    <div class="form-header repair-header">
      <div>
        <h2 class="form-title">{{ dialogTitle }}</h2>
        <p class="repair-caption">
          {{ repairId ? 'После создания ремонта можно управлять услугами, запчастями и статусом.' : 'Сначала создайте ремонт, затем откроется управление его деталями.' }}
        </p>
      </div>
      <button class="btn-ghost" type="button" @click="emit('close')">✕ Закрыть</button>
    </div>

    <div v-if="notice" class="repair-notice">{{ notice }}</div>
    <div v-if="loading" class="loading-row">
      <span class="spinner"></span> Загрузка ремонта...
    </div>

    <form v-else class="repair-form" @submit.prevent="submitBaseRepair">
      <div class="repair-top-grid">
        <label class="field">
          <span class="field-label">Велосипед <span class="req">*</span></span>
          <select v-model.number="form.bike_id" :disabled="isEditing" required>
            <option :value="null">Выберите велосипед</option>
            <option v-for="bike in bikes" :key="bike.id" :value="bike.id">
              {{ displayBike(bike) }}
            </option>
          </select>
        </label>

        <label class="field">
          <span class="field-label">Клиент <span class="req">*</span></span>
          <select v-model.number="form.client_id" :disabled="isEditing" required>
            <option :value="null">Выберите клиента</option>
            <option v-for="person in people" :key="person.id" :value="person.id">
              {{ displayPerson(person) }}
            </option>
          </select>
        </label>

        <label class="field">
          <span class="field-label">Статус</span>
          <select v-model="form.status" :disabled="!isEditing">
            <option v-for="opt in repairStatusOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
        </label>

        <div class="repair-meta">
          <div><span>Ремонт</span><strong>{{ repairId ? `#${repairId}` : '—' }}</strong></div>
          <div><span>Велосипед</span><strong>{{ displayBike(selectedBike) }}</strong></div>
          <div><span>Клиент</span><strong>{{ displayPerson(selectedPerson) }}</strong></div>
        </div>

        <label class="field full-width">
          <span class="field-label">Описание проблемы</span>
          <textarea
              v-model="form.problem_description"
              rows="4"
              placeholder="Опишите неисправность..."
              required
          ></textarea>
        </label>
      </div>

      <div v-if="!isEditing" class="repair-hints">
        <div v-if="activeBikeSuggestions.length === 1" class="repair-hint success">
          По велосипеду найдена активная аренда. Клиент подставлен автоматически.
        </div>
        <div v-else-if="activeBikeSuggestions.length > 1" class="repair-hint warning">
          У велосипеда несколько активных аренд. Выберите клиента вручную.
          <div class="hint-chips">
            <button
                v-for="person in activeBikeSuggestions"
                :key="person.id"
                type="button"
                class="hint-chip"
                @click="applySuggestedPerson(person.id)"
            >
              {{ displayPerson(person) }}
            </button>
          </div>
        </div>

        <div v-if="activePersonSuggestions.length === 1" class="repair-hint success">
          По клиенту найдена активная аренда. Велосипед подставлен автоматически.
        </div>
        <div v-else-if="activePersonSuggestions.length > 1" class="repair-hint warning">
          У клиента несколько активных аренд. Выберите велосипед вручную.
          <div class="hint-chips">
            <button
                v-for="bike in activePersonSuggestions"
                :key="bike.id"
                type="button"
                class="hint-chip"
                @click="applySuggestedBike(bike.id)"
            >
              {{ displayBike(bike) }}
            </button>
          </div>
        </div>
      </div>

      <div class="repair-actions">
        <button type="submit" class="btn-primary" :disabled="saving">
          {{ primaryLabel }}
        </button>
        <button type="button" class="btn-ghost" @click="emit('close')">Отмена</button>
      </div>
    </form>

    <div class="repair-sections">
      <section class="repair-card">
        <div class="repair-card-head">
          <div>
            <h3>Работы</h3>
            <p>Добавляйте услуги из справочника или создавайте новые прямо здесь.</p>
          </div>
          <span class="repair-total">{{ formatRubles(summary?.services_total ?? 0) }}</span>
        </div>

        <div class="catalog-toolbar">
          <input v-model="serviceSearch" type="search" placeholder="Поиск услуги..." />
          <button type="button" class="btn-ghost" @click="showNewService = !showNewService">
            {{ showNewService ? 'Скрыть' : 'Новая услуга' }}
          </button>
        </div>

        <div class="attach-row">
          <select v-model.number="serviceDraft.service_id" :disabled="!repairId">
            <option :value="null">Выберите услугу</option>
            <option v-for="service in filteredServicesCatalog" :key="service.id" :value="service.id">
              {{ service.name }} — {{ formatRubles(service.price) }}
            </option>
          </select>
          <input v-model="serviceDraft.price" :disabled="!repairId" type="number" min="0" step="0.01" placeholder="Цена (необязательно)" />
          <button type="button" class="btn-primary" :disabled="saving" @click="addServiceToRepair">
            Добавить
          </button>
        </div>

        <div v-if="showNewService" class="mini-form">
          <div class="mini-grid">
            <input v-model="newService.name" type="text" placeholder="Название услуги" />
            <input v-model="newService.price" type="number" min="0" step="0.01" placeholder="Цена" />
            <textarea v-model="newService.description" rows="2" class="full-width" placeholder="Описание"></textarea>
          </div>
          <button type="button" class="btn-primary" :disabled="saving" @click="addNewServiceAndAttach">
            Создать и добавить
          </button>
        </div>

        <div class="item-list">
          <div v-if="!repairServices.length" class="empty-inline">Услуг пока нет.</div>
          <div v-for="entry in repairServices" :key="entry.id" class="item-row">
            <div>
              <strong>{{ entry.service_name }}</strong>
              <p>{{ formatRubles(entry.price) }}</p>
            </div>
            <button type="button" class="btn-ghost danger" :disabled="saving" @click="removeServiceEntry(entry)">
              Удалить
            </button>
          </div>
        </div>
      </section>

      <section class="repair-card">
        <div class="repair-card-head">
          <div>
            <h3>Запчасти</h3>
            <p>Списывайте запчасти со склада или создавайте новую прямо из ремонта.</p>
          </div>
          <span class="repair-total">{{ formatRubles(summary?.parts_total ?? 0) }}</span>
        </div>

        <div class="catalog-toolbar">
          <input v-model="partSearch" type="search" placeholder="Поиск запчасти..." />
          <button type="button" class="btn-ghost" @click="showNewPart = !showNewPart">
            {{ showNewPart ? 'Скрыть' : 'Новая запчасть' }}
          </button>
        </div>

        <div class="attach-row attach-row-parts">
          <select v-model.number="partDraft.part_id" :disabled="!repairId">
            <option :value="null">Выберите запчасть</option>
            <option v-for="part in filteredPartsCatalog" :key="part.id" :value="part.id">
              {{ part.name }} — {{ part.quantity }} шт. — {{ formatRubles(part.sale_price) }}
            </option>
          </select>
          <input v-model.number="partDraft.quantity" :disabled="!repairId" type="number" min="1" step="1" placeholder="Кол-во" />
          <input v-model="partDraft.sale_price" :disabled="!repairId" type="number" min="0" step="0.01" placeholder="Цена продажи" />
          <button type="button" class="btn-primary" :disabled="saving" @click="addPartToRepair">
            Списать
          </button>
        </div>

        <textarea v-model="partDraft.notes" :disabled="!repairId" rows="2" class="repair-notes" placeholder="Примечание к списанию"></textarea>

        <div v-if="showNewPart" class="mini-form">
          <div class="mini-grid parts-grid">
            <input v-model="newPart.name" type="text" placeholder="Название запчасти" />
            <input v-model="newPart.category" type="text" placeholder="Категория" />
            <input v-model="newPart.sku" type="text" placeholder="SKU" />
            <input v-model="newPart.quantity" type="number" min="1" step="1" placeholder="Количество" />
            <input v-model="newPart.purchase_price" type="number" min="0" step="0.01" placeholder="Закупочная цена" />
            <input v-model="newPart.sale_price" type="number" min="0" step="0.01" placeholder="Цена продажи" />
            <select v-model="newPart.owner">
              <option v-for="opt in ownerOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>
            <input v-model="newPart.supplier" type="text" placeholder="Поставщик" />
            <textarea v-model="newPart.notes" rows="2" class="full-width" placeholder="Заметки"></textarea>
          </div>
          <button type="button" class="btn-primary" :disabled="saving" @click="addNewPartAndAttach">
            Создать и списать
          </button>
        </div>

        <div class="item-list">
          <div v-if="!repairParts.length" class="empty-inline">Запчастей пока нет.</div>
          <div v-for="entry in repairParts" :key="entry.id" class="item-row">
            <div>
              <strong>{{ entry.part_name }}</strong>
              <p>{{ entry.quantity }} шт. · {{ formatRubles(entry.sale_price) }}</p>
            </div>
            <button type="button" class="btn-ghost danger" :disabled="saving" @click="removePartEntry(entry)">
              Удалить
            </button>
          </div>
        </div>
      </section>

      <section class="repair-card summary-card">
        <div class="repair-card-head">
          <div>
            <h3>Финансовая сводка</h3>
            <p>Данные берутся из endpoint summary.</p>
          </div>
          <span class="repair-total total-main">{{ formatRubles(summary?.total_for_client ?? 0) }}</span>
        </div>

        <div class="summary-grid">
          <div class="summary-item">
            <span>Работы</span>
            <strong>{{ formatRubles(summary?.services_total ?? 0) }}</strong>
          </div>
          <div class="summary-item">
            <span>Запчасти</span>
            <strong>{{ formatRubles(summary?.parts_total ?? 0) }}</strong>
          </div>
          <div class="summary-item total-row">
            <span>Итого к оплате</span>
            <strong>{{ formatRubles(summary?.total_for_client ?? 0) }}</strong>
          </div>
        </div>

        <div class="owner-summary">
          <div class="owner-box">
            <h4>Кирилл</h4>
            <p>Закупка: {{ formatRubles(summary?.kirill?.parts_cost ?? 0) }}</p>
            <p>Выручка: {{ formatRubles(summary?.kirill?.parts_revenue ?? 0) }}</p>
            <p>Прибыль: {{ formatRubles(summary?.kirill?.parts_profit ?? 0) }}</p>
          </div>
          <div class="owner-box">
            <h4>Виталий</h4>
            <p>Закупка: {{ formatRubles(summary?.vitaly?.parts_cost ?? 0) }}</p>
            <p>Выручка: {{ formatRubles(summary?.vitaly?.parts_revenue ?? 0) }}</p>
            <p>Прибыль: {{ formatRubles(summary?.vitaly?.parts_profit ?? 0) }}</p>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.repair-panel {
  width: min(1120px, 100%);
  border-radius: 20px;
  padding: 24px;
}

.repair-header {
  gap: 18px;
  align-items: flex-start;
}

.repair-caption {
  margin-top: 6px;
  color: #6b7280;
  font-size: 0.9rem;
  max-width: 720px;
}

.repair-notice {
  margin-bottom: 14px;
  padding: 10px 14px;
  border-radius: 12px;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 0.9rem;
}

.repair-form {
  margin-bottom: 16px;
  display: grid;
  gap: 16px;
}

.repair-top-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.repair-meta {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  background: #fafafa;
}

.repair-meta span {
  display: block;
  color: #6b7280;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 4px;
}

.repair-meta strong {
  display: block;
  color: #111827;
  font-size: 0.95rem;
}

.repair-hints {
  display: grid;
  gap: 10px;
}

.repair-hint {
  padding: 12px 14px;
  border-radius: 12px;
  font-size: 0.9rem;
  line-height: 1.4;
}

.repair-hint.success {
  background: #ecfdf5;
  color: #166534;
}

.repair-hint.warning {
  background: #fffbeb;
  color: #92400e;
}

.hint-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.hint-chip {
  border: 1px solid #f59e0b;
  background: #fff;
  color: #92400e;
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 0.8rem;
  cursor: pointer;
}

.repair-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.repair-sections {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}

.summary-card {
  grid-column: auto;
}

.repair-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 18px;
  padding: 18px;
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.04);
}

.repair-card-head {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: flex-start;
  margin-bottom: 14px;
}

.repair-card-head h3 {
  font-size: 1.02rem;
  color: #111827;
}

.repair-card-head p {
  margin-top: 4px;
  color: #6b7280;
  font-size: 0.85rem;
}

.repair-total {
  padding: 8px 12px;
  border-radius: 999px;
  background: #f3f4f6;
  color: #111827;
  font-weight: 700;
  white-space: nowrap;
}

.total-main {
  background: #ede9fe;
  color: #5b21b6;
}

.catalog-toolbar {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
  align-items: center;
}

.catalog-toolbar input {
  flex: 1;
  min-width: 0;
}

.catalog-toolbar .btn-ghost {
  white-space: nowrap;
  flex-shrink: 0;
}

.catalog-toolbar input,
.attach-row input,
.attach-row select,
.mini-form input,
.mini-form select,
.mini-form textarea,
.repair-notes,
.repair-top-grid select,
.repair-top-grid textarea {
  width: 100%;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #fff;
  padding: 10px 12px;
  font: inherit;
  color: #111827;
}

.attach-row {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) 160px auto;
  gap: 10px;
  margin-bottom: 12px;
}

.attach-row-parts {
  grid-template-columns: minmax(0, 1.2fr) 120px 160px auto;
}

.mini-form {
  margin-bottom: 12px;
  padding: 14px;
  border-radius: 14px;
  background: #fafafa;
  border: 1px dashed #d1d5db;
}

.mini-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}

.parts-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.full-width {
  grid-column: 1 / -1;
}

.item-list {
  display: grid;
  gap: 10px;
}

.item-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  padding: 12px 14px;
  border-radius: 12px;
  background: #fafafa;
  border: 1px solid #eef2ff;
}

.item-row strong {
  display: block;
  color: #111827;
}

.item-row p {
  margin-top: 4px;
  color: #6b7280;
  font-size: 0.85rem;
}

.empty-inline {
  color: #9ca3af;
  font-size: 0.9rem;
  padding: 8px 0;
}

.repair-notes {
  margin-bottom: 12px;
  min-height: 74px;
  resize: vertical;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 14px;
}

.summary-item {
  padding: 14px;
  border-radius: 14px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
}

.summary-item span {
  display: block;
  color: #6b7280;
  font-size: 0.8rem;
  margin-bottom: 6px;
}

.summary-item strong {
  display: block;
  color: #111827;
  font-size: 1.05rem;
}

.total-row {
  background: #ede9fe;
  border-color: #ddd6fe;
}

.owner-summary {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.owner-box {
  padding: 14px;
  border-radius: 14px;
  background: #fafafa;
  border: 1px solid #e5e7eb;
}

.owner-box h4 {
  margin-bottom: 8px;
  color: #111827;
}

.owner-box p {
  color: #4b5563;
  font-size: 0.9rem;
  line-height: 1.6;
}

.danger {
  border-color: #fecaca;
  color: #b91c1c;
}

.danger:hover {
  background: #fef2f2;
}

@media (max-width: 1024px) {
  .repair-panel {
    width: 100%;
    padding: 18px;
  }

  .repair-top-grid,
  .summary-grid,
  .owner-summary,
  .mini-grid,
  .parts-grid,
  .repair-meta {
    grid-template-columns: 1fr;
  }

  .attach-row,
  .attach-row-parts {
    grid-template-columns: 1fr;
  }
}

/* Маленькие телефоны */
@media (max-width: 640px) {
  .repair-panel {
    padding: 12px;
    border-radius: 0;
  }

  .catalog-toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .catalog-toolbar .btn-ghost {
    width: 100%;
    text-align: center;
  }

  .repair-actions {
    flex-direction: column;
  }

  .repair-actions .btn-primary,
  .repair-actions .btn-ghost {
    width: 100%;
    text-align: center;
  }

  .hint-chips {
    gap: 6px;
  }
}
</style>