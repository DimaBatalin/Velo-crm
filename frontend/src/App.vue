<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import SidebarMenu from './components/SidebarMenu.vue'
import TopbarSearch from './components/TopbarSearch.vue'
import PageHeader from './components/PageHeader.vue'
import PersonForm from './components/PersonForm.vue'
import BikeForm from './components/BikeForm.vue'
import RepairForm from './components/RepairForm.vue'
import PartForm from './components/PartForm.vue'
import RentalForm from './components/RentalForm.vue'
import LoginForm from './components/LoginForm.vue'
import RegisterForm from './components/RegisterForm.vue'
import AnalyticsView from './components/AnalyticsView.vue'
import { getToken, removeToken } from './api/client.js'
import { getMe } from './api/auth.js'
import { useEnums } from './composables/useEnums.js'

// ── Auth state ────────────────────────────────────────────
const currentUser   = ref(null)
const authChecked   = ref(false)
const showRegister  = ref(false)

async function initAuth() {
  const token = getToken()
  if (token) {
    currentUser.value = await getMe(token)
    if (!currentUser.value) removeToken()
  }
  authChecked.value = true
}

async function loadInitialData() {
  try { await getApiMessage() } catch {}
  if (typeof window !== 'undefined') {
    isSidebarOpen.value = window.innerWidth > 1024
  }
  await Promise.all([loadPeople(), loadBikes(), loadRepairs(), loadRentals(), loadParts()])
}

async function onAuthenticated() {
  await initAuth()
  if (currentUser.value) await loadInitialData()
}

function logout() {
  removeToken()
  currentUser.value = null
}

// Handle 401 from any API call (token expired mid-session)
window.addEventListener('velo:unauthorized', () => {
  currentUser.value = null
})
// ─────────────────────────────────────────────────────────

import {
  getApiMessage,
  getPeople,    createPerson,   updatePerson,
  getBikes,     createBike,     updateBike,
  getRepairs,   createRepair,   updateRepair,
  getRentals,   createRental,   updateRental,   closeRental,   deleteRental,
  getParts,     createPart,
  createPassport, updatePassport,
} from './api/client'

const activePage     = ref('dashboard')
const searchQuery    = ref('')
const selectedStatus = ref('')
const isLoading      = ref(false)
const toast          = ref({ text: '', type: '' })
const sortState      = ref({ key: null, dir: 'asc' })

const people  = ref([])
const bikes   = ref([])
const repairs = ref([])
const rentals = ref([])
const parts   = ref([])

const showPersonForm = ref(false)
const showBikeForm   = ref(false)
const showRepairForm = ref(false)
const showPartForm   = ref(false)
const showRentalForm = ref(false)
const editingPerson  = ref(null)
const editingBike    = ref(null)
const editingRental  = ref(null)
const loadedPassport = ref(null)
const isSidebarOpen  = ref(false)

const newPerson = ref({
  first_name: '', last_name: '', middle_name: '', phone: '', email: '', telegram: '', notes: '',
  passport: { series: '', number: '', issued_by: '', issued_at: '', notes: '' },
})

const newBike = ref({
  type: 'Электровелосипед', brand: '', model: '', serial_number: '', color: '', notes: '', owner_type: null,
})

function createRepairDraft() {
  return { id: null, bike_id: null, client_id: null, problem_description: '', status: 'new' }
}

const newRepair = ref(createRepairDraft())

const newPart = ref({
  name: '', category: '', sku: '', purchase_price: '',
  sale_price: '', quantity: 1, min_stock: 2, owner: 'kirill', supplier: '', notes: '',
})

const newRental = ref({ bike_id: null, person_id: null, price_per_day: '' })

const navItems = [
  { id: 'dashboard', label: 'Аренды'      },
  { id: 'couriers',  label: 'Клиенты'     },
  { id: 'bicycles',  label: 'Велосипеды'  },
  { id: 'repairs',   label: 'Ремонты'     },
  { id: 'parts',     label: 'Запчасти'    },
  { id: 'history',   label: 'История'     },
  { id: 'analytics', label: 'Аналитика'   },
]

// ── Справочники (со значениями и label) — с backend (GET /enums) ──
// Хардкод здесь — это только fallback на случай, если /enums ещё не
// загрузился или недоступен, чтобы UI не остался без опций вовсе.
const { enums } = useEnums()

const FALLBACK_BIKE_STATUSES = [
  { value: 'ready',  label: 'Готов'    },
  { value: 'rented', label: 'В аренде' },
  { value: 'repair', label: 'Ремонт'   },
  { value: 'stolen', label: 'Кража'    },
]
const FALLBACK_REPAIR_STATUSES = [
  { value: 'new',           label: 'Новый'     },
  { value: 'in_progress',   label: 'В работе'  },
  { value: 'waiting_parts', label: 'Ожидание'  },
  { value: 'done',          label: 'Выполнен'  },
  { value: 'cancelled',     label: 'Отменён'   },
]
const FALLBACK_RENTAL_STATUSES = [
  { value: 'active',   label: 'Активна'    },
  { value: 'returned', label: 'Возвращён'  },
  { value: 'overdue',  label: 'Просрочена' },
]
const FALLBACK_PERSON_STATUSES = [
  { value: 'active',   label: 'Активный'      },
  { value: 'blocked',  label: 'Заблокирован'  },
  { value: 'archived', label: 'Архивный'      },
  { value: 'fired',    label: 'Уволен'        },
]
const FALLBACK_OWNER_TYPES = [
  { value: 'kirill', label: 'Кирилл'  },
  { value: 'vitaly', label: 'Виталий' },
]

function withAll(options) {
  return [{ value: '', label: 'Все' }, ...options]
}
function toLabelMap(options) {
  const map = {}
  for (const opt of options) map[opt.value] = opt.label
  return map
}

const FALLBACK_BIKE_TYPES = [
  { value: 'Электровелосипед',        label: 'Электровелосипед' },
  { value: 'Механический велосипед',  label: 'Механический велосипед' },
]
const FALLBACK_BIKE_OWNER_TYPES = [
  { value: 'Великий мастер', label: 'Великий мастер' },
  { value: 'Виталий',        label: 'Виталий' },
]

const bikeStatusOptions      = computed(() => enums.value?.bike_status?.length ? enums.value.bike_status : FALLBACK_BIKE_STATUSES)
const bikeTypeOptions        = computed(() => enums.value?.bike_type?.length ? enums.value.bike_type : FALLBACK_BIKE_TYPES)
const bikeOwnerTypeOptions   = computed(() => enums.value?.bike_owner_type?.length ? enums.value.bike_owner_type : FALLBACK_BIKE_OWNER_TYPES)
const repairStatusOptionsRaw = computed(() => enums.value?.repair_status?.length ? enums.value.repair_status : FALLBACK_REPAIR_STATUSES)
const rentalStatusOptionsRaw = computed(() => enums.value?.rental_status?.length ? enums.value.rental_status : FALLBACK_RENTAL_STATUSES)
const personStatusOptionsRaw = computed(() => enums.value?.person_status?.length ? enums.value.person_status : FALLBACK_PERSON_STATUSES)
const ownerTypeOptions       = computed(() => enums.value?.owner_type?.length ? enums.value.owner_type : FALLBACK_OWNER_TYPES)

const repairStatusOptions = computed(() => withAll(repairStatusOptionsRaw.value))
const rentalStatusOptions = computed(() => withAll(rentalStatusOptionsRaw.value))

const repairStatusLabels = computed(() => toLabelMap(repairStatusOptionsRaw.value))
const rentalStatusLabels = computed(() => toLabelMap(rentalStatusOptionsRaw.value))
const personStatusLabels = computed(() => toLabelMap(personStatusOptionsRaw.value))
const bikeStatusLabels   = computed(() => toLabelMap(bikeStatusOptions.value))
const ownerLabels        = computed(() => toLabelMap(ownerTypeOptions.value))

// Цвет бейджа — чисто визуальное решение, /enums его не хранит (там
// только value+label). Новый статус просто получит дефолтный цвет
// (см. `|| 'repair'` / `|| 'rented'` в местах использования) до
// ручного добавления сюда — это не ломает данные, только раскраску.
const repairStatusBadge = { new: 'rented', in_progress: 'repair', waiting_parts: 'repair', done: 'ready', cancelled: 'stolen' }
const rentalStatusBadge = { active: 'rented', returned: 'ready', overdue: 'stolen' }

const statusOptions = computed(() => ({
  dashboard: rentalStatusOptions.value,
  couriers:  withAll(personStatusOptionsRaw.value),
  bicycles:  withAll(bikeStatusOptions.value),
  repairs:   repairStatusOptions.value,
}))

const pageMeta = {
  dashboard: { title: 'Аренды',           sub: 'Управление арендами велосипедов'         },
  couriers:  { title: 'Клиенты',          sub: 'Список клиентов и их статусы'            },
  bicycles:  { title: 'Велосипеды',       sub: 'Велосипеды, состояние и последние операции' },
  repairs:   { title: 'Ремонты',          sub: 'Список заказов на ремонт и их статус'    },
  parts:     { title: 'Запчасти и склад', sub: 'Запасы и остатки на складе'              },
  history:   { title: 'История',          sub: 'Хронология аренд и ремонтов'             },
  analytics: { title: 'Аналитика',        sub: 'Заработок, топы и экспорт отчётов'       },
}

const searchPlaceholders = {
  dashboard: 'Поиск по клиенту или велосипеду...',
  couriers:  'Поиск по ФИО или телефону...',
  bicycles:  'Поиск по VIN...',
  repairs:   'Поиск по описанию...',
  parts:     'Поиск номенклатуры...',
  history:   'Поиск по событиям...',
}

const addButtonLabels = {
  dashboard: 'Создать аренду',
  couriers:  'Добавить клиента',
  bicycles:  'Добавить велосипед',
  repairs:   'Создать ремонт',
  parts:     'Добавить запчасть',
}

// ── Дополнительные фильтры таблиц (помимо статуса) ────────
// Ключ → выбранное значение ('' = все). Сбрасываются при смене страницы.
const extraFilters = ref({})

const allTagOptions = computed(() => {
  const names = new Set()
  for (const p of people.value) for (const t of (p.tags || [])) names.add(t)
  return [...names].sort((a, b) => a.localeCompare(b, 'ru')).map(name => ({ value: name, label: name }))
})

const partCategoryOptions = computed(() => {
  const names = new Set()
  for (const p of parts.value) if (p.category) names.add(p.category)
  return [...names].sort((a, b) => a.localeCompare(b, 'ru')).map(name => ({ value: name, label: name }))
})

// Определения: какие фильтры показывать на какой странице.
const extraFilterDefs = computed(() => {
  const page = activePage.value
  if (page === 'bicycles') {
    return [
      { key: 'type',  label: 'Тип',      options: withAll(bikeTypeOptions.value) },
      { key: 'owner', label: 'Владелец', options: withAll(bikeOwnerTypeOptions.value) },
    ]
  }
  if (page === 'parts') {
    const defs = [
      { key: 'owner', label: 'Владелец', options: withAll(ownerTypeOptions.value) },
      { key: 'stock', label: 'Остаток',  options: [{ value: '', label: 'Все' }, { value: 'low', label: 'Мало на складе' }, { value: 'out', label: 'Нет в наличии' }] },
    ]
    if (partCategoryOptions.value.length) {
      defs.push({ key: 'category', label: 'Категория', options: withAll(partCategoryOptions.value) })
    }
    return defs
  }
  if (page === 'history') {
    return [
      { key: 'etype', label: 'Тип события', options: [{ value: '', label: 'Все' }, { value: 'Аренда', label: 'Аренды' }, { value: 'Ремонт', label: 'Ремонты' }] },
    ]
  }
  if (page === 'couriers' && allTagOptions.value.length) {
    return [
      { key: 'tag', label: 'Тег', options: withAll(allTagOptions.value) },
    ]
  }
  return []
})

function matchesExtraFilters(page, item) {
  const f = extraFilters.value
  if (page === 'bicycles') {
    if (f.type && item.type !== f.type) return false
    if (f.owner && item.owner_type !== f.owner) return false
  }
  if (page === 'parts') {
    if (f.owner && item.owner !== f.owner) return false
    if (f.stock === 'low' && !(item.quantity > 0 && item.quantity <= (item.min_stock ?? 0))) return false
    if (f.stock === 'out' && item.quantity !== 0) return false
    if (f.category && item.category !== f.category) return false
  }
  if (page === 'history') {
    if (f.etype && item.event_type !== f.etype) return false
  }
  if (page === 'couriers') {
    if (f.tag && !(item.tags || []).includes(f.tag)) return false
  }
  return true
}

const pageTitle       = computed(() => pageMeta[activePage.value]?.title ?? '')
const pageSubtitle    = computed(() => pageMeta[activePage.value]?.sub ?? '')
const hasSearch       = computed(() => !['analytics'].includes(activePage.value))
const hasAddButton    = computed(() => activePage.value in addButtonLabels)
const filterOptions   = computed(() => statusOptions.value[activePage.value] || [])
const searchPlaceholder = computed(() => searchPlaceholders[activePage.value] || 'Поиск...')

const personById = computed(() => {
  const map = {}
  for (const p of people.value)
    map[p.id] = `${p.first_name} ${p.last_name}`.trim()
  return map
})

const bikeById = computed(() => {
  const map = {}
  for (const b of bikes.value) map[b.id] = b
  return map
})

// ── Helpers ───────────────────────────────────────────────

function formatPersonName(person) {
  if (!person) return '—'
  return [person.last_name, person.first_name, person.middle_name].filter(Boolean).join(' ') || `#${person.id}`
}

/** Активные VIN велосипедов клиента из данных аренды */
function getActiveBikeVins(person) {
  // Пробуем данные, которые могут прийти с сервера embedded в person
  const embedded = (person.rentals || []).filter(r => r.status === 'active' && r.bike)
  if (embedded.length) return embedded.map(r => r.bike.serial_number || `#${r.bike.id}`).join(', ')

  // Иначе ищем в глобальном списке аренд
  const found = rentals.value
      .filter(r => r.person_id === person.id && r.status === 'active')
      .map(r => {
        const bike = bikeById.value[r.bike_id]
        return bike ? (bike.serial_number || `#${bike.id}`) : `#${r.bike_id}`
      })
  return found.length ? found.join(', ') : 'Нет аренды'
}

/** Имя последнего клиента велосипеда из данных аренды */
function getLastClientText(bike) {
  // Embedded в bike
  const embedded = Array.isArray(bike?.rentals) ? [...bike.rentals] : []
  if (embedded.length) {
    const sorted = embedded.sort((a, b) => new Date(b.started_at) - new Date(a.started_at))
    const last = sorted.find(r => r.person)
    if (last?.person) return formatPersonName(last.person)
  }

  // Из глобального списка
  const found = rentals.value
      .filter(r => r.bike_id === bike.id)
      .sort((a, b) => new Date(b.started_at) - new Date(a.started_at))
  if (!found.length) return '—'
  const person = people.value.find(p => p.id === found[0].person_id)
  return person ? formatPersonName(person) : `#${found[0].person_id}`
}

function bikeTypeIcon(bike) {
  if (!bike) return ''
  if (bike.type === 'Электровелосипед') return '⚡'
  if (bike.type === 'Механический велосипед') return '🔧'
  return ''
}

const repairFormTitle   = computed(() => newRepair.value?.id ? `Редактирование ремонта #${newRepair.value.id}` : 'Новый ремонт')
const repairSubmitLabel = computed(() => newRepair.value?.id ? 'Сохранить изменения' : 'Создать ремонт')

// ── Filtered rows ─────────────────────────────────────────

const historyEvents = computed(() => {
  const repairItems = repairs.value.map(r => ({
    id: `r${r.id}`, event_type: 'Ремонт',
    description: r.problem_description,
    bike_id: r.bike_id, person_id: r.client_id,
    status: r.status, status_label: repairStatusLabels.value[r.status] || r.status,
    badge: repairStatusBadge[r.status] || 'repair', created_at: r.created_at,
  }))

  const rentalItems = rentals.value.map(r => ({
    id: `n${r.id}`, event_type: 'Аренда',
    description: r.price_per_day ? `${r.price_per_day} ₽/день` : 'Цена не указана',
    bike_id: r.bike_id, person_id: r.person_id,
    status: r.status, status_label: rentalStatusLabels.value[r.status] || r.status,
    badge: rentalStatusBadge[r.status] || 'rented', created_at: r.created_at,
  }))

  return [...repairItems, ...rentalItems]
      .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
})

function buildSearchText(page, item) {
  if (page === 'dashboard') {
    const bike   = bikeById.value[item.bike_id]
    const person = people.value.find(p => p.id === item.person_id)
    return [
      bike?.serial_number, bike?.brand, bike?.model,
      person ? formatPersonName(person) : '',
      item.status,
    ].filter(Boolean).join(' ')
  }

  if (page === 'couriers') {
    return [item.first_name, item.last_name, item.middle_name, item.phone, item.email, item.telegram, item.status, getActiveBikeVins(item)].filter(Boolean).join(' ')
  }
  if (page === 'bicycles') {
    return [item.serial_number, item.brand, item.model, item.color, item.status, item.type, getLastClientText(item)].filter(Boolean).join(' ')
  }
  if (page === 'repairs') {
    return [item.id, item.problem_description, bikeById.value[item.bike_id]?.serial_number, personById.value[item.client_id], item.status].filter(Boolean).join(' ')
  }
  if (page === 'parts') {
    return [item.name, item.category, item.sku, item.supplier, item.owner, item.quantity, item.sale_price].filter(Boolean).join(' ')
  }
  if (page === 'history') {
    return [item.event_type, item.description, item.status_label, bikeById.value[item.bike_id]?.serial_number, personById.value[item.person_id]].filter(Boolean).join(' ')
  }
  return Object.values(item).map(v => String(v)).join(' ')
}

const filteredRows = computed(() => {
  const query  = searchQuery.value.trim().toLowerCase()
  const status = selectedStatus.value

  const sourceByPage = {
    dashboard: rentals.value,
    couriers:  people.value,
    bicycles:  bikes.value,
    repairs:   repairs.value,
    parts:     parts.value,
    history:   historyEvents.value,
  }

  const rows = sourceByPage[activePage.value] || []

  return rows.filter(item => {
    const matchesStatus = !status || String(item.status) === status
    const matchesQuery  = !query  || buildSearchText(activePage.value, item).toLowerCase().includes(query)
    return matchesStatus && matchesQuery && matchesExtraFilters(activePage.value, item)
  })
})

// ── Toast ─────────────────────────────────────────────────
let toastTimer = null
function showToast(text, type = 'ok') {
  toast.value = { text, type }
  clearTimeout(toastTimer)
  if (type === 'ok') toastTimer = setTimeout(() => { toast.value = { text: '', type: '' } }, 3000)
}

// ── Forms ─────────────────────────────────────────────────
function closeAllForms() {
  showPersonForm.value = false
  showBikeForm.value   = false
  showRepairForm.value = false
  showPartForm.value   = false
  showRentalForm.value = false
  editingPerson.value  = null
  editingBike.value    = null
  editingRental.value  = null
  newRepair.value      = createRepairDraft()
}

function selectPage(page) {
  activePage.value     = page
  searchQuery.value    = ''
  selectedStatus.value = ''
  extraFilters.value   = {}
  toast.value          = { text: '', type: '' }
  sortState.value      = { key: null, dir: 'asc' }
  closeAllForms()
  loadPage(page)
  if (typeof window !== 'undefined' && window.innerWidth <= 1024) {
    isSidebarOpen.value = false
  }
}

// ── Sorting ───────────────────────────────────────────────
function toggleSort(key) {
  if (sortState.value.key === key) {
    sortState.value = { key, dir: sortState.value.dir === 'asc' ? 'desc' : 'asc' }
  } else {
    sortState.value = { key, dir: 'asc' }
  }
}

function sortArrow(key) {
  if (sortState.value.key !== key) return ''
  return sortState.value.dir === 'asc' ? '▲' : '▼'
}

function compareSortValues(a, b) {
  if (typeof a === 'number' && typeof b === 'number') return a - b
  return String(a).localeCompare(String(b), 'ru')
}

const sortAccessors = {
  dashboard: {
    id:         row => row.id,
    bike:       row => bikeById.value[row.bike_id]?.serial_number || '',
    client:     row => personById.value[row.person_id] || '',
    status:     row => rentalStatusLabels.value[row.status] || row.status || '',
    price:      row => row.price_per_day ?? -Infinity,
    started_at: row => row.started_at ? new Date(row.started_at).getTime() : 0,
    ended_at:   row => row.ended_at ? new Date(row.ended_at).getTime() : 0,
  },
  couriers: {
    fio:      row => [row.last_name, row.first_name, row.middle_name].filter(Boolean).join(' '),
    phone:    row => row.phone || '',
    passport: row => (row.passport?.series || row.passport?.number) ? 1 : 0,
    status:   row => personStatusLabels.value[row.status] || row.status || '',
    tags:     row => (row.tags || []).join(', '),
    bikes:    row => getActiveBikeVins(row),
  },
  bicycles: {
    vin:        row => row.serial_number || '',
    type:       row => row.type || '',
    brand:      row => [row.brand, row.model].filter(Boolean).join(' '),
    status:     row => bikeStatusLabels.value[row.status] || row.status || '',
    lastClient: row => getLastClientText(row),
  },
  repairs: {
    id:          row => row.id,
    bike:        row => bikeById.value[row.bike_id]?.serial_number || '',
    client:      row => personById.value[row.client_id] || '',
    description: row => row.problem_description || '',
    status:      row => repairStatusLabels.value[row.status] || row.status || '',
    cost:        row => row.total_cost ?? -Infinity,
    created_at:  row => row.created_at ? new Date(row.created_at).getTime() : 0,
  },
  parts: {
    name:     row => row.name || '',
    category: row => row.category || '',
    owner:    row => ownerLabels.value[row.owner] || row.owner || '',
    quantity: row => row.quantity ?? 0,
    price:    row => row.sale_price ?? -Infinity,
  },
  history: {
    type:        row => row.event_type || '',
    bike:        row => bikeById.value[row.bike_id]?.serial_number || '',
    client:      row => personById.value[row.person_id] || '',
    description: row => row.description || '',
    status:      row => row.status_label || '',
    created_at:  row => row.created_at ? new Date(row.created_at).getTime() : 0,
  },
}

const sortedRows = computed(() => {
  const rows = [...filteredRows.value]
  const { key, dir } = sortState.value
  const accessor = key && sortAccessors[activePage.value]?.[key]
  if (!accessor) return rows
  const sign = dir === 'asc' ? 1 : -1
  return rows.sort((a, b) => sign * compareSortValues(accessor(a), accessor(b)))
})

function onContentClick() {
  if (typeof window !== 'undefined' && window.innerWidth <= 1024) {
    isSidebarOpen.value = false
  }
}

function loadPage(page) {
  if (page === 'dashboard') loadRentals()
  if (page === 'couriers')  loadPeople()
  if (page === 'bicycles')  loadBikes()
  if (page === 'repairs')   loadRepairs()
  if (page === 'parts')     loadParts()
  if (page === 'history')   { loadRepairs(); loadRentals() }
}

function openCreateForm() {
  closeAllForms()
  if (activePage.value === 'dashboard') showRentalForm.value = true
  if (activePage.value === 'couriers')  showPersonForm.value = true
  if (activePage.value === 'bicycles')  showBikeForm.value   = true
  if (activePage.value === 'repairs')   showRepairForm.value = true
  if (activePage.value === 'parts')     showPartForm.value   = true
}

// ── Data loading ──────────────────────────────────────────
async function load(fn, target, errorMsg) {
  isLoading.value = true
  try { target.value = await fn() }
  catch (e) { console.error(e); showToast(errorMsg, 'error') }
  finally { isLoading.value = false }
}

async function loadPeople() {
  // Паспорт приходит вместе с клиентом (поле passport) — отдельные
  // запросы /people/{id}/passport больше не нужны.
  await load(
      () => getPeople({ search: searchQuery.value, status: selectedStatus.value || undefined, limit: 100 }),
      people, 'Не удалось загрузить клиентов.',
  )
}

function loadBikes()   { load(() => getBikes({ limit: 100 }),                                                              bikes,   'Не удалось загрузить велосипеды.') }
function loadRepairs() { load(() => getRepairs({ status: selectedStatus.value || undefined, limit: 100 }),                 repairs, 'Не удалось загрузить ремонты.') }
function loadRentals() { load(() => getRentals({ status: selectedStatus.value || undefined, limit: 100 }),                rentals, 'Не удалось загрузить аренды.') }
function loadParts()   { load(() => getParts({ search: searchQuery.value, limit: 100 }),                                  parts,   'Не удалось загрузить запчасти.') }

// ── Bike status ───────────────────────────────────────────
async function changeBikeStatus(bike, newStatus) {
  if (bike.status === newStatus) return
  const prev = bike.status
  bike.status = newStatus
  try {
    await updateBike(bike.id, { status: newStatus })
    showToast(`Статус ${bike.serial_number || `#${bike.id}`} обновлён.`)
  } catch (e) {
    console.error(e); bike.status = prev
    showToast(e?.message || 'Не удалось обновить статус.', 'error')
  }
}

// ── Edit / Create ─────────────────────────────────────────
function startEditPerson(person) {
  closeAllForms()
  // Паспорт уже пришёл вместе с клиентом — отдельный запрос не нужен.
  const passport = person.passport || null
  editingPerson.value = {
    ...person,
    passport: passport
        ? { ...passport }
        : { series: '', number: '', issued_by: '', issued_at: '', notes: '' },
  }
  loadedPassport.value = passport
}

function startEditBike(bike) {
  closeAllForms()
  editingBike.value = { ...bike }
}

function startEditRental(rental) {
  closeAllForms()
  editingRental.value = { ...rental }
}

function startEditRepair(repair) {
  closeAllForms()
  newRepair.value = { ...repair, id: repair.id, bike_id: repair.bike_id, client_id: repair.client_id,
    problem_description: repair.problem_description ?? '', status: repair.status ?? 'new' }
  showRepairForm.value = true
}

// ── Cross-entity navigation ───────────────────────────────

/** Открыть карточку клиента по ID (подгрузить если нужно) */
async function openPersonById(personId) {
  if (!personId) return
  let person = people.value.find(p => p.id === personId)
  if (!person) {
    await loadPeople()
    person = people.value.find(p => p.id === personId)
  }
  if (person) startEditPerson(person)
  else showToast('Клиент не найден', 'error')
}

/** Открыть карточку велосипеда по ID (подгрузить если нужно) */
async function openBikeById(bikeId) {
  if (!bikeId) return
  let bike = bikes.value.find(b => b.id === bikeId)
  if (!bike) {
    await loadBikes()
    bike = bikes.value.find(b => b.id === bikeId)
  }
  if (bike) startEditBike(bike)
  else showToast('Велосипед не найден', 'error')
}

/** Открыть карточку последнего клиента велосипеда */
async function openLastClientForBike(bike) {
  // Сначала из embedded данных аренды
  const embedded = Array.isArray(bike?.rentals) ? [...bike.rentals] : []
  if (embedded.length) {
    const last = embedded
        .sort((a, b) => new Date(b.started_at) - new Date(a.started_at))
        .find(r => r.person)
    if (last?.person?.id) return openPersonById(last.person.id)
  }
  // Из глобального списка аренд
  if (!rentals.value.length) await loadRentals()
  const found = rentals.value
      .filter(r => r.bike_id === bike.id)
      .sort((a, b) => new Date(b.started_at) - new Date(a.started_at))
  if (found.length) return openPersonById(found[0].person_id)
  showToast('Нет данных о клиенте', 'error')
}

/** Открыть карточку первого активного велосипеда клиента */
async function openFirstActiveBikeForPerson(person) {
  // Из embedded данных
  const embedded = (person.rentals || []).filter(r => r.status === 'active' && r.bike)
  if (embedded.length) return openBikeById(embedded[0].bike.id)
  // Из глобального списка аренд
  if (!rentals.value.length) await loadRentals()
  const found = rentals.value.filter(r => r.person_id === person.id && r.status === 'active')
  if (found.length) return openBikeById(found[0].bike_id)
  showToast('Нет активной аренды', 'error')
}

/** Открыть запись из истории (аренда или ремонт) */
function openHistoryRow(row) {
  const id = row.id?.toString() ?? ''
  if (id.startsWith('r')) {
    const repair = repairs.value.find(r => r.id === parseInt(id.slice(1)))
    if (repair) startEditRepair(repair)
  } else if (id.startsWith('n')) {
    const rental = rentals.value.find(r => r.id === parseInt(id.slice(1)))
    if (rental) startEditRental(rental)
  }
}

// ── Submit: Person ────────────────────────────────────────
async function submitEditPerson() {
  if (!editingPerson.value) return
  try {
    await updatePerson(editingPerson.value.id, {
      first_name: editingPerson.value.first_name, last_name: editingPerson.value.last_name,
      middle_name: editingPerson.value.middle_name || undefined, phone: editingPerson.value.phone,
      email: editingPerson.value.email || undefined, telegram: editingPerson.value.telegram || undefined,
      notes: editingPerson.value.notes || undefined, status: editingPerson.value.status,
    })
    const passport = editingPerson.value.passport || {}
    const hasPassportData = passport.series || passport.number || passport.issued_by || passport.issued_at || passport.notes
    if (hasPassportData) {
      const payload = { series: passport.series || undefined, number: passport.number || undefined,
        issued_by: passport.issued_by || undefined, issued_at: passport.issued_at || undefined, notes: passport.notes || undefined }
      if (loadedPassport.value) await updatePassport(editingPerson.value.id, payload)
      else await createPassport(editingPerson.value.id, payload)
    }
    showToast('Клиент обновлён.')
    editingPerson.value = null; loadedPassport.value = null
    loadPeople()
  } catch (e) { console.error(e); showToast(e?.message || 'Не удалось сохранить изменения.', 'error') }
}

async function submitPerson() {
  try {
    const person = await createPerson({
      first_name: newPerson.value.first_name, last_name: newPerson.value.last_name,
      middle_name: newPerson.value.middle_name || undefined, phone: newPerson.value.phone,
      email: newPerson.value.email || undefined, telegram: newPerson.value.telegram || undefined,
      notes: newPerson.value.notes || undefined,
    })
    const passport = newPerson.value.passport || {}
    const hasPassportData = passport.series || passport.number || passport.issued_by || passport.issued_at || passport.notes
    if (hasPassportData) {
      await createPassport(person.id, { series: passport.series || undefined, number: passport.number || undefined,
        issued_by: passport.issued_by || undefined, issued_at: passport.issued_at || undefined, notes: passport.notes || undefined })
    }
    showToast('Клиент добавлен.')
    showPersonForm.value = false
    newPerson.value = { first_name: '', last_name: '', middle_name: '', phone: '', email: '', telegram: '', notes: '',
      passport: { series: '', number: '', issued_by: '', issued_at: '', notes: '' } }
    loadPeople()
  } catch (e) { console.error(e); showToast(e?.message || 'Ошибка при добавлении клиента.', 'error') }
}

// ── Submit: Bike ──────────────────────────────────────────
async function submitEditBike() {
  if (!editingBike.value) return
  try {
    await updateBike(editingBike.value.id, {
      type: editingBike.value.type, brand: editingBike.value.brand, model: editingBike.value.model,
      serial_number: editingBike.value.serial_number || undefined, color: editingBike.value.color || undefined,
      notes: editingBike.value.notes || undefined, owner_type: editingBike.value.owner_type || undefined,
      status: editingBike.value.status,
    })
    showToast('Велосипед обновлён.'); editingBike.value = null; loadBikes()
  } catch (e) { console.error(e); showToast(e?.message || 'Не удалось сохранить изменения.', 'error') }
}

async function submitBike() {
  try {
    await createBike({
      type: newBike.value.type, brand: newBike.value.brand, model: newBike.value.model,
      serial_number: newBike.value.serial_number || undefined, color: newBike.value.color || undefined,
      notes: newBike.value.notes || undefined, owner_type: newBike.value.owner_type || undefined,
    })
    showToast('Велосипед добавлен.'); showBikeForm.value = false
    newBike.value = { type: 'Электровелосипед', brand: '', model: '', serial_number: '', color: '', notes: '', owner_type: null }
    loadBikes()
  } catch (e) { console.error(e); showToast(e?.message || 'Ошибка при добавлении велосипеда.', 'error') }
}

// ── Submit: Repair ────────────────────────────────────────
async function submitRepair() {
  try {
    const repair = await createRepair({
      bike_id: newRepair.value.bike_id,
      client_id: newRepair.value.client_id,
      problem_description: newRepair.value.problem_description,
    })
    // Бэкенд сам переводит велосипед в статус «Ремонт» атомарно с созданием
    // заказа — отдельный запрос updateBike больше не нужен.
    const bike = bikes.value.find(b => b.id === newRepair.value.bike_id)
    if (bike) bike.status = 'repair'
    newRepair.value = { ...repair, status: repair.status ?? 'new' }
    showToast('Ремонт создан. Теперь можно добавлять работы и запчасти.')
    loadRepairs(); loadBikes()
  } catch (e) { console.error(e); showToast(e?.message || 'Ошибка при создании ремонта.', 'error') }
}

async function onRepairSaved() { loadRepairs(); loadBikes(); loadParts() }

// ── Submit: Part ──────────────────────────────────────────
async function submitPart() {
  try {
    await createPart({
      name: newPart.value.name, category: newPart.value.category || undefined,
      sku: newPart.value.sku || undefined, purchase_price: Number(newPart.value.purchase_price),
      sale_price: Number(newPart.value.sale_price), quantity: Number(newPart.value.quantity),
      min_stock: Number(newPart.value.min_stock) || 2,
      owner: newPart.value.owner, supplier: newPart.value.supplier || undefined, notes: newPart.value.notes || undefined,
    })
    showToast('Запчасть добавлена.'); showPartForm.value = false
    newPart.value = { name: '', category: '', sku: '', purchase_price: '', sale_price: '', quantity: 1, min_stock: 2, owner: 'kirill', supplier: '', notes: '' }
    loadParts()
  } catch (e) { console.error(e); showToast(e?.message || 'Ошибка при добавлении запчасти.', 'error') }
}

// ── Submit: Rental ────────────────────────────────────────
async function submitRental() {
  try {
    await createRental({
      bike_id: newRental.value.bike_id,
      person_id: newRental.value.person_id,
      price_per_day: newRental.value.price_per_day !== '' ? Number(newRental.value.price_per_day) : undefined,
    })
    showToast('Аренда создана.')
    showRentalForm.value = false
    newRental.value = { bike_id: null, person_id: null, price_per_day: '' }
    loadRentals(); loadBikes()
  } catch (e) { console.error(e); showToast(e?.message || 'Ошибка при создании аренды.', 'error') }
}


async function submitEditRental() {
  if (!editingRental.value) return

  try {
    await updateRental(editingRental.value.id, {
      bike_id: editingRental.value.bike_id,
      person_id: editingRental.value.person_id,
      price_per_day: editingRental.value.price_per_day !== '' ? Number(editingRental.value.price_per_day) : null,
      started_at: editingRental.value.started_at,
      ended_at: editingRental.value.ended_at,
      status: editingRental.value.status,
    })

    showToast('Аренда обновлена.')

    editingRental.value = null

    await loadRentals()
    await loadBikes()
  } catch (e) {
    console.error(e)
    showToast(e?.message || 'Не удалось обновить аренду.', 'error')
  }
}

async function handleCloseRental(rental) {
  if (!confirm(`Закрыть аренду #${rental.id}?`)) return
  try {
    await closeRental(rental.id)
    showToast('Аренда закрыта.'); loadRentals(); loadBikes()
  } catch (e) { console.error(e); showToast(e?.message || 'Не удалось закрыть аренду.', 'error') }
}

async function handleDeleteRental(rental) {
  if (!confirm(`Удалить аренду #${rental.id}?`)) return
  try {
    await deleteRental(rental.id)
    showToast('Аренда удалена.'); loadRentals(); loadBikes()
  } catch (e) { console.error(e); showToast(e?.message || 'Не удалось удалить аренду.', 'error') }
}

// ── Lifecycle ─────────────────────────────────────────────
onMounted(async () => {
  await initAuth()
  if (!currentUser.value) return
  await loadInitialData()
})

const lastTap = ref(0)
function handleRowTouch(row, type) {
  const now = Date.now()
  if (now - lastTap.value < 350) {
    if (type === 'person') startEditPerson(row)
    if (type === 'bike') startEditBike(row)
    lastTap.value = 0
    return
  }
  lastTap.value = now
}

// Debounce: без него каждый введённый символ поиска дёргал сервер.
let reloadTimer = null
watch([searchQuery, selectedStatus], () => {
  clearTimeout(reloadTimer)
  reloadTimer = setTimeout(() => {
    const page = activePage.value
    if (page === 'dashboard') loadRentals()
    if (page === 'couriers')  loadPeople()
    if (page === 'repairs')   loadRepairs()
    if (page === 'parts')     loadParts()
  }, 300)
})
</script>

<template>
  <!-- Not yet checked localStorage → nothing -->
  <div v-if="!authChecked" class="auth-checking"></div>

  <!-- Not logged in → show login screen -->
  <LoginForm v-else-if="!currentUser" @authenticated="onAuthenticated" />

  <!-- Logged in → full app -->
  <div v-else class="app-shell">
    <div
        v-if="isSidebarOpen"
        class="sidebar-backdrop"
        @click="isSidebarOpen = false"
    ></div>

    <SidebarMenu
        :class="{ 'sidebar-open': isSidebarOpen }"
        :navItems="navItems"
        :activePage="activePage"
        :user="currentUser"
        @selectPage="selectPage"
        @logout="logout"
        @openRegister="showRegister = true"
    />

    <section class="content" @click="onContentClick">
      <TopbarSearch
          :hasSearch="hasSearch"
          :searchQuery="searchQuery"
          :searchPlaceholder="searchPlaceholder"
          :toast="toast"
          @update:searchQuery="value => searchQuery = value"
          @toggleMenu="isSidebarOpen = !isSidebarOpen"
      />

      <PageHeader
          :pageTitle="pageTitle"
          :pageSubtitle="pageSubtitle"
          :hasAddButton="hasAddButton"
          :addButtonLabel="addButtonLabels[activePage]"
          @openCreateForm="openCreateForm"
      />

      <!-- Modals -->
      <transition name="fade">
        <div
            v-if="showPersonForm || showBikeForm || showRepairForm || showPartForm || showRentalForm || editingPerson || editingBike || editingRental"
            class="modal-backdrop"
            @click.self="closeAllForms"
        >
          <transition name="slide-down">
            <div class="modal-body">
              <PersonForm
                  v-if="showPersonForm"
                  :visible="showPersonForm"
                  v-model:modelValue="newPerson"
                  title="Новый клиент"
                  submitLabel="Сохранить"
                  @save="submitPerson"
                  @close="closeAllForms"
              />

              <BikeForm
                  v-else-if="showBikeForm"
                  :visible="showBikeForm"
                  v-model:modelValue="newBike"
                  :people="people"
                  title="Новый велосипед"
                  submitLabel="Сохранить"
                  @save="submitBike"
                  @close="closeAllForms"
              />

              <RepairForm
                  v-else-if="showRepairForm"
                  :visible="showRepairForm"
                  v-model:modelValue="newRepair"
                  :bikes="bikes"
                  :people="people"
                  :current-user="currentUser"
                  :title="repairFormTitle"
                  :submitLabel="repairSubmitLabel"
                  @save="submitRepair"
                  @saved="onRepairSaved"
                  @close="closeAllForms"
              />

              <PartForm
                  v-else-if="showPartForm"
                  :visible="showPartForm"
                  v-model:modelValue="newPart"
                  @save="submitPart"
                  @close="closeAllForms"
              />

              <RentalForm
                  v-else-if="showRentalForm"
                  :visible="showRentalForm"
                  v-model:modelValue="newRental"
                  :bikes="bikes"
                  :people="people"
                  title="Новая аренда"
                  submitLabel="Создать аренду"
                  @save="submitRental"
                  @close="closeAllForms"
              />

              <PersonForm
                  v-else-if="editingPerson"
                  :visible="!!editingPerson"
                  v-model:modelValue="editingPerson"
                  :showStatus="true"
                  title="Редактировать клиента"
                  submitLabel="Сохранить изменения"
                  @save="submitEditPerson"
                  @tagsChanged="loadPeople"
                  @close="closeAllForms"
              />

              <BikeForm
                  v-else-if="editingBike"
                  :visible="!!editingBike"
                  v-model:modelValue="editingBike"
                  :showStatus="true"
                  title="Редактировать велосипед"
                  submitLabel="Сохранить изменения"
                  @save="submitEditBike"
                  @close="closeAllForms"
              />

              <RentalForm
                  v-else-if="editingRental"
                  :visible="!!editingRental"
                  v-model:modelValue="editingRental"
                  :bikes="bikes"
                  :people="people"
                  title="Редактирование аренды"
                  submitLabel="Сохранить изменения"
                  @save="submitEditRental"
                  @close="closeAllForms"
              />
            </div>
          </transition>
        </div>
      </transition>

      <!-- Page content -->
      <div v-if="filterOptions.length || extraFilterDefs.length" class="toolbar toolbar-filters">
        <div v-if="filterOptions.length" class="filter-group">
          <span class="filter-label">Статус:</span>
          <div class="filter-chips">
            <button
                v-for="opt in filterOptions"
                :key="opt.value"
                :class="['chip', { active: selectedStatus === opt.value }]"
                @click="selectedStatus = opt.value"
            >{{ opt.label }}</button>
          </div>
        </div>

        <div v-for="def in extraFilterDefs" :key="def.key" class="filter-group">
          <span class="filter-label">{{ def.label }}:</span>
          <div class="filter-chips">
            <button
                v-for="opt in def.options"
                :key="opt.value"
                :class="['chip', { active: (extraFilters[def.key] || '') === opt.value }]"
                @click="extraFilters = { ...extraFilters, [def.key]: opt.value }"
            >{{ opt.label }}</button>
          </div>
        </div>
      </div>

      <div class="panel">
        <div v-if="isLoading" class="loading-row">
          <span class="spinner"></span> Загрузка...
        </div>

        <AnalyticsView v-if="activePage === 'analytics'" @toast="showToast" />

        <!-- ═══════════════ АРЕНДЫ (dashboard) ═══════════════ -->
        <div v-else class="table-wrap">
          <table v-if="activePage === 'dashboard'" class="table">
            <thead>
            <tr>
              <th class="th-sortable" @click="toggleSort('id')">№ <span class="sort-arrow">{{ sortArrow('id') }}</span></th>
              <th class="th-sortable" @click="toggleSort('bike')">Велосипед <span class="sort-arrow">{{ sortArrow('bike') }}</span></th>
              <th>Тип</th>
              <th class="th-sortable" @click="toggleSort('client')">Клиент <span class="sort-arrow">{{ sortArrow('client') }}</span></th>
              <th class="th-sortable" @click="toggleSort('status')">Статус <span class="sort-arrow">{{ sortArrow('status') }}</span></th>
              <th class="col-right th-sortable" @click="toggleSort('price')">₽/день <span class="sort-arrow">{{ sortArrow('price') }}</span></th>
              <th class="th-sortable" @click="toggleSort('started_at')">Начало <span class="sort-arrow">{{ sortArrow('started_at') }}</span></th>
              <th class="th-sortable" @click="toggleSort('ended_at')">Конец <span class="sort-arrow">{{ sortArrow('ended_at') }}</span></th>
              <th></th>
            </tr>
            </thead>
            <tbody>
            <tr v-for="row in sortedRows" :key="row.id" class="row-clickable" @click="startEditRental(row)" title="Открыть аренду">
              <td class="td-mono" data-label="№">{{ row.id }}</td>
              <td class="td-vin td-link" data-label="Велосипед" title="Открыть велосипед" @click.stop="openBikeById(row.bike_id)">
                {{ bikeById[row.bike_id]?.serial_number || `#${row.bike_id}` }}
              </td>
              <td data-label="Тип">
                <span class="type-pill">{{ bikeById[row.bike_id] ? (bikeById[row.bike_id].type === 'Электровелосипед' ? '⚡' : '🔧') : '' }}</span>
              </td>
              <td class="td-link" data-label="Клиент" title="Открыть клиента" @click.stop="openPersonById(row.person_id)">
                {{ personById[row.person_id] || `#${row.person_id}` }}
              </td>
              <td data-label="Статус">
                  <span :class="['badge', rentalStatusBadge[row.status] || 'rented']">
                    {{ rentalStatusLabels[row.status] || row.status }}
                  </span>
              </td>
              <td class="col-right" data-label="₽/день">{{ row.price_per_day != null ? `${row.price_per_day} ₽` : '—' }}</td>
              <td class="td-date" data-label="Начало">{{ row.started_at ? new Date(row.started_at).toLocaleDateString('ru') : '—' }}</td>
              <td class="td-date" data-label="Конец">{{ row.ended_at ? new Date(row.ended_at).toLocaleDateString('ru') : '—' }}</td>
              <td class="td-actions" data-label="" @click.stop>
                <button
                    v-if="row.status === 'active'"
                    class="action-btn close-btn"
                    title="Закрыть аренду"
                    @click="handleCloseRental(row)"
                >Закрыть</button>
                <button
                    class="action-btn del-btn"
                    title="Удалить"
                    @click="handleDeleteRental(row)"
                >✕</button>
              </td>
            </tr>
            <tr v-if="!isLoading && sortedRows.length === 0">
              <td colspan="9" class="empty-row">Аренды не найдены</td>
            </tr>
            </tbody>
          </table>

          <!-- ═══════════════ КЛИЕНТЫ ═══════════════ -->
          <table v-else-if="activePage === 'couriers'" class="table">
            <thead>
            <tr>
              <th class="th-sortable" @click="toggleSort('fio')">ФИО <span class="sort-arrow">{{ sortArrow('fio') }}</span></th>
              <th class="th-sortable" @click="toggleSort('phone')">Телефон <span class="sort-arrow">{{ sortArrow('phone') }}</span></th>
              <th class="th-sortable" @click="toggleSort('passport')">Паспорт <span class="sort-arrow">{{ sortArrow('passport') }}</span></th>
              <th class="th-sortable" @click="toggleSort('status')">Статус <span class="sort-arrow">{{ sortArrow('status') }}</span></th>
              <th class="th-sortable" @click="toggleSort('tags')">Теги <span class="sort-arrow">{{ sortArrow('tags') }}</span></th>
              <th class="th-sortable" @click="toggleSort('bikes')">Велосипеды в аренде <span class="sort-arrow">{{ sortArrow('bikes') }}</span></th>
            </tr>
            </thead>
            <tbody>
            <tr v-for="row in sortedRows" :key="row.id"
                class="row-clickable" @click="startEditPerson(row)"
                title="Открыть клиента">
              <td class="td-name" data-label="ФИО">{{ `${row.first_name} ${row.last_name}` }}</td>
              <td data-label="Телефон">{{ row.phone || '—' }}</td>
              <td data-label="Паспорт">
                  <span :class="['passport-tag', row.passport?.series || row.passport?.number ? 'loaded' : 'missing']">
                    {{ row.passport?.series || row.passport?.number ? 'Загружен' : 'Нет данных' }}
                  </span>
              </td>
              <td data-label="Статус">
                  <span :class="['badge', row.status === 'active' ? 'ready' : row.status === 'blocked' ? 'repair' : 'stolen']">
                    {{ personStatusLabels[row.status] || row.status }}
                  </span>
              </td>
              <td class="td-tags" data-label="Теги">
                <span v-for="tagName in row.tags" :key="tagName" class="person-tag-chip">{{ tagName }}</span>
                <span v-if="!row.tags?.length" class="td-muted">—</span>
              </td>
              <td class="td-bikes td-link" data-label="В аренде"
                  title="Открыть велосипед"
                  @click.stop="openFirstActiveBikeForPerson(row)">
                {{ getActiveBikeVins(row) }}
              </td>
            </tr>
            <tr v-if="!isLoading && sortedRows.length === 0">
              <td colspan="6" class="empty-row">Клиенты не найдены</td>
            </tr>
            </tbody>
          </table>

          <!-- ═══════════════ ВЕЛОСИПЕДЫ ═══════════════ -->
          <table v-else-if="activePage === 'bicycles'" class="table">
            <thead>
            <tr>
              <th class="th-sortable" @click="toggleSort('vin')">VIN <span class="sort-arrow">{{ sortArrow('vin') }}</span></th>
              <th class="th-sortable" @click="toggleSort('type')">Тип <span class="sort-arrow">{{ sortArrow('type') }}</span></th>
              <th class="th-sortable" @click="toggleSort('brand')">Марка / Модель <span class="sort-arrow">{{ sortArrow('brand') }}</span></th>
              <th class="th-sortable" @click="toggleSort('status')">Статус <span class="sort-arrow">{{ sortArrow('status') }}</span></th>
              <th class="th-sortable" @click="toggleSort('lastClient')">Последний клиент <span class="sort-arrow">{{ sortArrow('lastClient') }}</span></th>
            </tr>
            </thead>
            <tbody>
            <tr v-for="row in sortedRows" :key="row.id"
                class="row-clickable" @click="startEditBike(row)"
                title="Открыть велосипед">
              <td class="td-vin" data-label="VIN">{{ row.serial_number || '—' }}</td>
              <td data-label="Тип">
                  <span :class="['bike-type-tag', row.type === 'Электровелосипед' ? 'type-e' : 'type-m']">
                    {{ row.type === 'Электровелосипед' ? '⚡ Электро' : '🔧 Механика' }}
                  </span>
              </td>
              <td data-label="Марка / Модель">{{ row.brand }} {{ row.model }}</td>
              <td data-label="Статус" @click.stop>
                <select
                    :class="['status-select', row.status]"
                    :value="row.status"
                    @change="changeBikeStatus(row, $event.target.value)"
                >
                  <option v-for="opt in bikeStatusOptions" :key="opt.value" :value="opt.value">
                    {{ opt.label }}
                  </option>
                </select>
              </td>
              <td class="td-link" data-label="Последний клиент"
                  title="Открыть клиента"
                  @click.stop="openLastClientForBike(row)">
                {{ getLastClientText(row) }}
              </td>
            </tr>
            <tr v-if="!isLoading && sortedRows.length === 0">
              <td colspan="5" class="empty-row">Велосипеды не найдены</td>
            </tr>
            </tbody>
          </table>

          <!-- ═══════════════ РЕМОНТЫ ═══════════════ -->
          <table v-else-if="activePage === 'repairs'" class="table">
            <thead>
            <tr>
              <th class="th-sortable" @click="toggleSort('id')">№ <span class="sort-arrow">{{ sortArrow('id') }}</span></th>
              <th class="th-sortable" @click="toggleSort('bike')">Велосипед <span class="sort-arrow">{{ sortArrow('bike') }}</span></th>
              <th class="th-sortable" @click="toggleSort('client')">Клиент <span class="sort-arrow">{{ sortArrow('client') }}</span></th>
              <th class="th-sortable" @click="toggleSort('description')">Описание <span class="sort-arrow">{{ sortArrow('description') }}</span></th>
              <th class="th-sortable" @click="toggleSort('status')">Статус <span class="sort-arrow">{{ sortArrow('status') }}</span></th>
              <th class="col-right th-sortable" @click="toggleSort('cost')">Стоимость <span class="sort-arrow">{{ sortArrow('cost') }}</span></th>
              <th class="th-sortable" @click="toggleSort('created_at')">Дата <span class="sort-arrow">{{ sortArrow('created_at') }}</span></th>
            </tr>
            </thead>
            <tbody>
            <tr v-for="row in sortedRows" :key="row.id" class="row-clickable" @click="startEditRepair(row)" title="Открыть ремонт">
              <td class="td-mono" data-label="№">{{ row.id }}</td>
              <td class="td-vin td-link" data-label="Велосипед" title="Открыть велосипед" @click.stop="openBikeById(row.bike_id)">
                {{ bikeById[row.bike_id]?.serial_number || `#${row.bike_id}` }}
              </td>
              <td class="td-link" data-label="Клиент" title="Открыть клиента" @click.stop="openPersonById(row.client_id)">
                {{ personById[row.client_id] || `#${row.client_id}` }}
              </td>
              <td class="td-desc" data-label="Описание">{{ row.problem_description || '—' }}</td>
              <td data-label="Статус">
                  <span :class="['badge', repairStatusBadge[row.status] || 'repair']">
                    {{ repairStatusLabels[row.status] || row.status }}
                  </span>
              </td>
              <td class="col-right td-price" data-label="Стоимость">{{ row.total_cost != null ? `${row.total_cost} ₽` : '—' }}</td>
              <td class="td-date" data-label="Дата">{{ row.created_at ? new Date(row.created_at).toLocaleDateString('ru') : '—' }}</td>
            </tr>
            <tr v-if="!isLoading && sortedRows.length === 0">
              <td colspan="7" class="empty-row">Ремонты не найдены</td>
            </tr>
            </tbody>
          </table>

          <!-- ═══════════════ ЗАПЧАСТИ ═══════════════ -->
          <table v-else-if="activePage === 'parts'" class="table">
            <thead>
            <tr>
              <th class="th-sortable" @click="toggleSort('name')">Наименование <span class="sort-arrow">{{ sortArrow('name') }}</span></th>
              <th class="th-sortable" @click="toggleSort('category')">Категория <span class="sort-arrow">{{ sortArrow('category') }}</span></th>
              <th class="th-sortable" @click="toggleSort('owner')">Принадлежность <span class="sort-arrow">{{ sortArrow('owner') }}</span></th>
              <th class="col-right th-sortable" @click="toggleSort('quantity')">Кол-во <span class="sort-arrow">{{ sortArrow('quantity') }}</span></th>
              <th class="col-right th-sortable" @click="toggleSort('price')">Цена продажи <span class="sort-arrow">{{ sortArrow('price') }}</span></th>
            </tr>
            </thead>
            <tbody>
            <tr v-for="row in sortedRows" :key="row.id">
              <td class="td-name" data-label="Наименование">{{ row.name }}</td>
              <td data-label="Категория"><span class="category-tag">{{ row.category || '—' }}</span></td>
              <td data-label="Принадлежность">
                  <span :class="['owner-tag', row.owner === 'vitaly' ? 'owner-v' : 'owner-k']">
                    {{ ownerLabels[row.owner] || row.owner }}
                  </span>
              </td>
              <td class="col-right" data-label="Кол-во">
                  <span :class="['quantity-val', row.quantity <= row.min_stock ? 'quantity-low' : '']" :title="`Мин. остаток: ${row.min_stock}`">
                    {{ row.quantity }} шт.
                  </span>
              </td>
              <td class="col-right td-price" data-label="Цена">
                {{ row.sale_price != null ? `${row.sale_price} ₽` : '—' }}
              </td>
            </tr>
            <tr v-if="!isLoading && sortedRows.length === 0">
              <td colspan="5" class="empty-row">Запчасти не найдены</td>
            </tr>
            </tbody>
          </table>

          <!-- ═══════════════ ИСТОРИЯ ═══════════════ -->
          <table v-else-if="activePage === 'history'" class="table">
            <thead>
            <tr>
              <th class="th-sortable" @click="toggleSort('type')">Тип <span class="sort-arrow">{{ sortArrow('type') }}</span></th>
              <th class="th-sortable" @click="toggleSort('bike')">Велосипед <span class="sort-arrow">{{ sortArrow('bike') }}</span></th>
              <th class="th-sortable" @click="toggleSort('client')">Клиент <span class="sort-arrow">{{ sortArrow('client') }}</span></th>
              <th class="th-sortable" @click="toggleSort('description')">Описание <span class="sort-arrow">{{ sortArrow('description') }}</span></th>
              <th class="th-sortable" @click="toggleSort('status')">Статус <span class="sort-arrow">{{ sortArrow('status') }}</span></th>
              <th class="th-sortable" @click="toggleSort('created_at')">Дата <span class="sort-arrow">{{ sortArrow('created_at') }}</span></th>
            </tr>
            </thead>
            <tbody>
            <tr v-for="row in sortedRows" :key="row.id" class="row-clickable" @click="openHistoryRow(row)" title="Открыть запись">
              <td data-label="Тип">
                  <span :class="['event-badge', row.event_type === 'Аренда' ? 'ev-rental' : 'ev-repair']">
                    {{ row.event_type }}
                  </span>
              </td>
              <td class="td-vin td-link" data-label="Велосипед" title="Открыть велосипед" @click.stop="openBikeById(row.bike_id)">
                {{ bikeById[row.bike_id]?.serial_number || `#${row.bike_id}` }}
              </td>
              <td class="td-link" data-label="Клиент" title="Открыть клиента" @click.stop="openPersonById(row.person_id)">
                {{ personById[row.person_id] || `#${row.person_id}` }}
              </td>
              <td class="td-desc" data-label="Описание">{{ row.description }}</td>
              <td data-label="Статус"><span :class="['badge', row.badge]">{{ row.status_label }}</span></td>
              <td class="td-date" data-label="Дата">{{ row.created_at ? new Date(row.created_at).toLocaleDateString('ru') : '—' }}</td>
            </tr>
            <tr v-if="!isLoading && sortedRows.length === 0">
              <td colspan="6" class="empty-row">История пуста</td>
            </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- Register modal -->
    <RegisterForm
      v-if="showRegister"
      @close="showRegister = false"
      @created="showRegister = false"
    />

  </div>
  <!-- /v-else (logged in) -->
</template>

<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: 'Segoe UI', system-ui, sans-serif;
  background: #f1f3f7;
  color: #111827;
  font-size: 15px;
}

.app-shell {
  display: flex;
  align-items: stretch;
  min-height: 100vh;
}

/* ── Sidebar ────────────────────────────────────────────── */
.app-shell .sidebar {
  flex: 0 0 240px;
  width: 240px;
  max-width: 240px;
  background: #fff;
  border-right: 1px solid #e5e7eb;
  padding: 20px 12px;
  display: flex; flex-direction: column; gap: 6px;
  position: sticky; top: 0; height: 100vh; overflow-y: auto;
}

.brand {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 10px 16px; border-bottom: 1px solid #f3f4f6;
  margin-bottom: 6px;
}
.brand-icon { font-size: 1.4rem; }
.brand-name { font-size: 1rem; font-weight: 700; color: #111827; line-height: 1.2; }
.brand-sub  { font-size: 0.75rem; color: #9ca3af; }

.menu { display: flex; flex-direction: column; gap: 2px; }
.menu-item {
  width: 100%; text-align: left; border: none; background: transparent;
  padding: 10px 12px; border-radius: 8px; cursor: pointer;
  color: #6b7280; font-size: 0.9rem; font-weight: 500;
  transition: background 0.15s, color 0.15s;
}
.menu-item:hover  { background: #f3f4f6; color: #111827; }
.menu-item.active { background: #7c3aed; color: #fff; font-weight: 600; }

/* ── Content ────────────────────────────────────────────── */
.content {
  display: flex; flex-direction: column; gap: 20px;
  padding: 24px 32px; flex: 1; min-width: 0;
}

/* ── Topbar ─────────────────────────────────────────────── */
.topbar { display: flex; align-items: center; gap: 16px; }
.hamburger {
  display: none; align-items: center; justify-content: center;
  background: transparent; border: 1px solid transparent;
  font-size: 1.05rem; padding: 6px 8px; border-radius: 8px;
  cursor: pointer;
}
.search-wrap { position: relative; flex: 1; max-width: 480px; }
.search-icon {
  position: absolute; left: 12px; top: 50%; transform: translateY(-50%);
  font-size: 0.85rem; pointer-events: none;
}
.search-input {
  width: 100%; padding: 9px 14px 9px 36px;
  border: 1px solid #e5e7eb; border-radius: 10px;
  font-size: 0.9rem; background: #fff; color: #111827;
  outline: none; transition: border-color 0.15s;
}
.search-input:focus    { border-color: #7c3aed; }
.search-input:disabled { background: #f9fafb; cursor: default; }

.toast { padding: 8px 16px; border-radius: 8px; font-size: 0.875rem; font-weight: 500; flex-shrink: 0; }
.toast-ok    { background: #dcfce7; color: #166534; }
.toast-error { background: #fee2e2; color: #991b1b; }

.fade-enter-active, .fade-leave-active { transition: opacity 0.25s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

/* ── Page header ────────────────────────────────────────── */
.page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
.page-title { font-size: 1.55rem; font-weight: 700; color: #111827; }
.page-sub   { color: #6b7280; font-size: 0.875rem; margin-top: 3px; }

/* ── Buttons ────────────────────────────────────────────── */
.btn-primary {
  background: #7c3aed; color: #fff; border: none;
  padding: 10px 18px; border-radius: 8px;
  font-size: 0.875rem; font-weight: 600; cursor: pointer;
  white-space: nowrap; transition: background 0.15s;
}
.btn-primary:hover { background: #6d28d9; }

.btn-ghost {
  background: transparent; border: 1px solid #e5e7eb; color: #6b7280;
  padding: 8px 14px; border-radius: 8px; font-size: 0.875rem;
  cursor: pointer; transition: background 0.15s;
}
.btn-ghost:hover { background: #f3f4f6; }

/* ── Form panel ─────────────────────────────────────────── */
.form-panel {
  background: #fff; border: 1px solid #e5e7eb;
  border-radius: 12px; padding: 28px 32px;
}
.form-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.form-title { font-size: 1.05rem; font-weight: 700; }

.form-grid {
  display: grid; grid-template-columns: repeat(2, 1fr);
  gap: 20px; margin-bottom: 24px;
}
.full-width { grid-column: span 2; }

.passport-section {
  padding: 18px 16px 14px;
  border: 1px solid #e5e7eb; border-radius: 12px; gap: 14px;
}
.passport-section-header {
  grid-column: span 2; font-size: 0.9rem; font-weight: 700;
  color: #1f2937; margin-bottom: 8px;
}

.field { display: flex; flex-direction: column; gap: 6px; }
.field-label {
  font-size: 0.78rem; font-weight: 600; color: #374151;
  text-transform: uppercase; letter-spacing: 0.05em;
}
.req { color: #ef4444; }

.field input, .field select, .field textarea {
  padding: 10px 14px; border: 1px solid #e5e7eb;
  border-radius: 8px; font-size: 0.9rem; color: #111827;
  background: #fff; outline: none; transition: border-color 0.15s;
  font-family: inherit; width: 100%;
}
.field input:focus, .field select:focus, .field textarea:focus {
  border-color: #7c3aed; box-shadow: 0 0 0 3px rgba(124,58,237,.08);
}
.field textarea { resize: vertical; min-height: 80px; }

.form-actions { display: flex; gap: 10px; }

/* ── Modal ──────────────────────────────────────────────── */
.slide-down-enter-active { transition: all 0.22s ease; }
.slide-down-leave-active { transition: all 0.18s ease; }
.slide-down-enter-from   { opacity: 0; transform: translateY(-10px); }
.slide-down-leave-to     { opacity: 0; transform: translateY(-6px); }

.modal-backdrop {
  position: fixed; inset: 0;
  background: rgba(15, 23, 42, 0.45);
  display: flex; align-items: center; justify-content: center;
  padding: 24px; z-index: 50; overflow: auto;
}
.modal-body {
  width: min(100%, 720px);
  max-height: calc(100vh - 48px);
  overflow: hidden;
}
.modal-body .form-panel {
  max-width: 100%;
  max-height: calc(100vh - 96px);
  overflow-y: auto;
}

/* ── Stats cards ────────────────────────────────────────── */
.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.stat-card {
  background: #fff; border: 1px solid #e5e7eb;
  border-radius: 12px; padding: 20px 24px;
  border-left: 4px solid transparent;
}
.stat-blue   { border-left-color: #3b82f6; }
.stat-orange { border-left-color: #f59e0b; }
.stat-red    { border-left-color: #ef4444; }
.stat-label {
  font-size: 0.75rem; color: #6b7280; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.04em;
  margin-bottom: 10px;
}
.stat-value {
  font-size: 2.2rem; font-weight: 700;
  color: #111827; line-height: 1;
}

/* ── Activity ───────────────────────────────────────────── */
.activity-list { padding: 0 20px; }
.activity-row  {
  display: flex; align-items: center; gap: 14px;
  padding: 14px 0; border-bottom: 1px solid #f9fafb;
}
.activity-row:last-child { border-bottom: none; }
.activity-dot  { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.activity-dot.ready  { background: #22c55e; }
.activity-dot.rented { background: #3b82f6; }
.activity-dot.repair { background: #f59e0b; }
.activity-dot.stolen { background: #ef4444; }
.activity-body { flex: 1; display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.activity-type { font-size: 0.78rem; font-weight: 600; color: #6b7280; text-transform: uppercase; }
.activity-desc {
  font-size: 0.9rem; font-weight: 500; color: #111827;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.activity-time { font-size: 0.8rem; color: #9ca3af; white-space: nowrap; }
.empty-panel { padding: 36px; text-align: center; color: #9ca3af; font-size: 0.9rem; }

/* ── Toolbar / chips ────────────────────────────────────── */
.toolbar { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.toolbar-filters { align-items: flex-start; flex-direction: column; gap: 8px; }
.filter-group { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.filter-label { font-size: 0.8rem; font-weight: 600; color: #6b7280; min-width: 64px; }
.filter-chips { display: flex; gap: 6px; flex-wrap: wrap; }
.chip {
  padding: 5px 12px; border: 1px solid #e5e7eb;
  border-radius: 20px; background: #fff;
  font-size: 0.8rem; font-weight: 500; color: #6b7280;
  cursor: pointer; transition: all 0.15s;
}
.chip:hover  { border-color: #7c3aed; color: #7c3aed; }
.chip.active { background: #7c3aed; border-color: #7c3aed; color: #fff; }

/* ── Panel / Table ──────────────────────────────────────── */
.panel { background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden; }
.panel-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px; border-bottom: 1px solid #f3f4f6;
}
.panel-title { font-size: 0.95rem; font-weight: 700; color: #111827; }

.table-wrap {
  width: 100%;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.table { width: 100%; border-collapse: collapse; }
.table thead { background: #f9fafb; border-bottom: 1px solid #e5e7eb; }
.table th {
  text-align: left; padding: 11px 16px;
  font-size: 0.72rem; font-weight: 600; color: #6b7280;
  text-transform: uppercase; letter-spacing: 0.05em; white-space: nowrap;
}
.th-sortable { cursor: pointer; user-select: none; transition: color 0.12s; }
.th-sortable:hover { color: #7c3aed; }
.sort-arrow { font-size: 0.85em; color: #7c3aed; display: inline-block; width: 0.8em; }
.table td {
  padding: 13px 16px; border-bottom: 1px solid #f3f4f6;
  font-size: 0.9rem; color: #374151; vertical-align: middle;
}
.table tbody tr:last-child td { border-bottom: none; }
.table tbody tr:hover td { background: #fafafa; }

.td-name  { font-weight: 500; color: #111827; }
.td-vin   { font-family: 'Courier New', monospace; font-size: 0.85rem; color: #4b5563; }
.td-mono  { font-family: 'Courier New', monospace; font-size: 0.85rem; }
.td-date  { color: #9ca3af; font-size: 0.85rem; white-space: nowrap; }
.td-price { font-weight: 600; color: #111827; }
.td-desc  { max-width: 220px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.td-bikes { font-size: 0.85rem; color: #4b5563;}
.td-actions { white-space: nowrap; text-align: right; }
.col-right { text-align: right; }
.empty-row { text-align: center; color: #9ca3af; padding: 36px !important; font-size: 0.875rem; }

/* Кликабельные ячейки — навигация к связанной сущности */
.td-link {
  color: #5b21b6;
  text-decoration: underline;
  text-underline-offset: 2px;
  text-decoration-color: #c4b5fd;
  cursor: pointer;
  transition: color 0.12s, text-decoration-color 0.12s;
}
.td-link:hover {
  color: #4c1d95;
  text-decoration-color: #7c3aed;
  background: #f5f3ff !important;
}

/* ── Badges ─────────────────────────────────────────────── */
.badge {
  display: inline-flex; align-items: center;
  padding: 4px 10px; border-radius: 20px;
  font-size: 0.75rem; font-weight: 600; white-space: nowrap;
}
.badge.ready  { background: #dcfce7; color: #15803d; }
.badge.rented { background: #dbeafe; color: #1d4ed8; }
.badge.repair { background: #fef3c7; color: #b45309; }
.badge.stolen { background: #fee2e2; color: #b91c1c; }

.status-select {
  padding: 4px 10px; border-radius: 20px;
  font-size: 0.75rem; font-weight: 600;
  border: none; cursor: pointer;
  appearance: none; -webkit-appearance: none; outline: none;
}
.status-select.ready  { background: #dcfce7; color: #15803d; }
.status-select.rented { background: #dbeafe; color: #1d4ed8; }
.status-select.repair { background: #fef3c7; color: #b45309; }
.status-select.stolen { background: #fee2e2; color: #b91c1c; }

.event-badge {
  display: inline-flex; align-items: center;
  padding: 3px 8px; border-radius: 4px;
  font-size: 0.75rem; font-weight: 600; white-space: nowrap;
}
.ev-repair { background: #fef3c7; color: #b45309; }
.ev-rental { background: #dbeafe; color: #1d4ed8; }

.passport-tag {
  font-size: 0.75rem; font-weight: 600;
  padding: 3px 8px; border-radius: 4px;
}
.passport-tag.loaded  { background: #f0fdf4; color: #15803d; }
.passport-tag.missing { background: #f9fafb; color: #9ca3af; }

.td-tags { flex-wrap: wrap; gap: 4px; align-items: center; }
.person-tag-chip {
  font-size: 0.72rem; font-weight: 600;
  padding: 3px 9px; border-radius: 999px;
  background: #ede9fe; color: #5b21b6; white-space: nowrap;
}
.td-muted { color: #9ca3af; }

.category-tag {
  font-size: 0.75rem; background: #f3f4f6; color: #6b7280;
  padding: 3px 8px; border-radius: 4px; font-weight: 500;
}

.owner-tag {
  font-size: 0.75rem; font-weight: 600;
  padding: 3px 8px; border-radius: 4px;
}
.owner-k { background: #ede9fe; color: #6d28d9; }
.owner-v { background: #e0f2fe; color: #0369a1; }

.quantity-val { font-weight: 500; }
.quantity-low { color: #ef4444; font-weight: 700; }

/* ── Bike type tags ─────────────────────────────────────── */
.bike-type-tag {
  font-size: 0.75rem; font-weight: 600;
  padding: 3px 8px; border-radius: 4px; white-space: nowrap;
}
.type-e { background: #fef9c3; color: #854d0e; }
.type-m { background: #f1f5f9; color: #475569; }
.type-pill { font-size: 1rem; }

/* ── Rental action buttons ──────────────────────────────── */
.action-btn {
  border: none; border-radius: 6px; padding: 4px 10px;
  font-size: 0.78rem; font-weight: 600; cursor: pointer;
  transition: all 0.15s; margin-left: 4px;
}
.close-btn  { background: #dcfce7; color: #15803d; }
.close-btn:hover { background: #bbf7d0; }
.del-btn    { background: #fee2e2; color: #b91c1c; }
.del-btn:hover { background: #fecaca; }

/* ── Misc ───────────────────────────────────────────────── */
.row-clickable { cursor: pointer; }
.row-clickable:hover td { background: #f0edfb !important; }
.edit-panel {
  border-top: 2px solid #7c3aed; padding: 24px 28px;
  background: #faf8ff;
}
.loading-row {
  display: flex; align-items: center; gap: 10px;
  padding: 20px; color: #9ca3af; font-size: 0.875rem;
}
.spinner {
  width: 16px; height: 16px;
  border: 2px solid #e5e7eb; border-top-color: #7c3aed;
  border-radius: 50%; animation: spin 0.7s linear infinite;
  display: inline-block;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Sidebar backdrop (mobile/tablet overlay) ─────────────── */
.app-shell .sidebar-backdrop {
  display: none;
}

/* ── ≤ 1024px: планшеты и телефоны ──────────────────────── */
@media (max-width: 1024px) {
  .app-shell { flex-direction: column; }

  /* Сайдбар скрыт по умолчанию, открывается как оверлей */
  .app-shell .sidebar {
    display: none;
    position: fixed;
    left: 0; top: 0; bottom: 0;
    width: 260px;
    height: 100%;
    z-index: 60;
    background: #fff;
    flex-direction: column;
    padding: 16px;
    overflow-y: auto;
    border-right: 1px solid #e5e7eb;
    box-shadow: 4px 0 24px rgba(15, 23, 42, 0.14);
  }
  .app-shell .sidebar.sidebar-open {
    display: flex;
  }

  .app-shell .sidebar-backdrop {
    display: block;
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    width: 80%;
    max-width: 280px;
    background: rgba(15, 23, 42, 0.4);
    z-index: 59;
  }

  /* Бургер-кнопка видна */
  .hamburger { display: inline-flex; }

  .content { padding: 16px 20px; }

  /* Таблицы скроллятся горизонтально */
  .table {
    width: 100%;
    min-width: 100%;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  /* Формы в 2 колонки (на планшете нормально) */
  .form-grid { grid-template-columns: repeat(2, 1fr); }

  .modal-body { width: min(100%, 94%); }
  .topbar .search-wrap { flex: 1; }
}

/* ── ≤ 640px: маленькие телефоны ────────────────────────── */
@media (max-width: 640px) {
  body { font-size: 14px; }

  .content { padding: 12px; gap: 14px; }

  /* Формы в 1 колонку */
  .form-grid  { grid-template-columns: 1fr; }
  .full-width { grid-column: span 1; }

  /* Заголовок страницы */
  .page-header { flex-direction: column; align-items: flex-start; gap: 10px; }
  .page-title  { font-size: 1.25rem; }
  .btn-primary, .form-actions .btn-primary, .form-actions .btn-ghost { width: 100%; justify-content: center; text-align: center; }

  /* Топбар */
  .topbar { gap: 8px; }
  .search-wrap { max-width: none; }

  /* Toast не выходит за экран */
  .toast { font-size: 0.8rem; padding: 6px 10px; max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

  /* Кнопки формы — в столбик */
  .form-actions { flex-direction: column; gap: 8px; }

  /* Модалка — нижний шит */
  .modal-backdrop { padding: 0; align-items: flex-end; }
  .modal-body { width: 100%; max-height: 100vh; }
  .modal-body .form-panel {
    border-radius: 16px 16px 0 0;
    max-height: 92vh;
    border-left: none; border-right: none; border-bottom: none;
    padding: 20px 16px;
  }
  .form-panel { padding: 20px 16px; }
  .form-header { margin-bottom: 16px; }

  /* Фильтры */
  .toolbar { gap: 8px; }
  .filter-chips { gap: 4px; }
  .chip { padding: 4px 10px; font-size: 0.75rem; }

  /* Паспортная секция */
  .passport-section { padding: 14px 12px 10px; }
  .passport-section-header { margin-bottom: 4px; }
}

/* ── Responsive: ≤768px (mobile off‑canvas) ────────────── */
@media (max-width: 768px) {
  .app-shell {
    flex-direction: column;
  }

  .app-shell .sidebar {
    display: none;
    position: fixed;
    z-index: 60;
    width: 80%;
    max-width: 280px;
    left: 0; top: 0; bottom: 0;
    height: 100%;
    transform: translateX(-110%);
    transition: transform .25s ease;
    box-shadow: 4px 0 20px rgba(15,23,42,0.1);

    /* Бургер-меню — строго вертикально */
    flex-direction: column;
    overflow-y: auto;
  }
  .app-shell .sidebar.sidebar-open {
    display: flex;
    transform: translateX(0);
  }

  .menu {
    flex-direction: column;
  }

  .hamburger {
    display: inline-flex;
  }

  .content {
    padding: 12px 14px;
  }

  .page-header {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }
  .page-header .btn-primary {
    width: 100%;
    justify-content: center;
    text-align: center;
  }

  .stats-grid {
    grid-template-columns: 1fr;
    gap: 14px;
  }

  .form-grid {
    grid-template-columns: 1fr;
    gap: 14px;
  }
  .full-width,
  .passport-section-header {
    grid-column: span 1;
  }

  .panel {
    padding: 10px;
    border-radius: 10px;
  }

  .table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
  }
  .table thead {
    display: none;
  }
  .table tbody tr {
    display: block;
    background: #fff;
    margin-bottom: 10px;
    padding: 10px 12px;
    border-radius: 10px;
    border: 1px solid #f3f4f6;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  }
  .table tbody td {
    display: grid;
    grid-template-columns: 42% 1fr;
    align-items: center;
    padding: 7px 0;
    border-bottom: 1px solid #f3f4f6;
    font-size: 0.875rem;
    text-align: right;
  }
  .table tbody td:last-child {
    border-bottom: none;
  }
  .table tbody td::before {
    content: attr(data-label);
    color: #6b7280;
    font-size: 0.75rem;
    font-weight: 600;
    text-align: left;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-right: 8px;
  }
  .table tbody td.td-desc {
    display: block;
    text-align: left;
    white-space: normal;
    max-width: unset;
    padding: 4px 0 6px;
    color: #4b5563;
    font-size: 0.85rem;
  }
  .table tbody td.td-desc::before {
    display: block;
    margin-bottom: 3px;
  }
  .table tbody td > * {
    justify-self: end;
  }
  .td-name, .td-vin {
    font-weight: 600;
  }
  .col-right {
    text-align: right;
  }

  .modal-backdrop {
    padding: 0;
    align-items: flex-end;
  }
  .modal-body {
    width: 100%;
    max-height: 92vh;
    border-radius: 0;
  }
  .modal-body .form-panel {
    max-height: 92vh;
    border-radius: 18px 18px 0 0;
    padding: 20px 16px 28px;
  }

  .toolbar {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  .filter-chips {
    gap: 6px;
  }

  .activity-row {
    flex-wrap: wrap;
    gap: 6px;
  }
  .activity-time {
    width: 100%;
    text-align: right;
  }

  .search-wrap {
    max-width: 100%;
    flex: 1;
  }

  .form-actions {
    flex-direction: column;
  }
  .form-actions .btn-primary,
  .form-actions .btn-ghost {
    width: 100%;
    text-align: center;
    justify-content: center;
  }
}
</style>