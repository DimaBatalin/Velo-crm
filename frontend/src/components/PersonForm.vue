<script setup>
import { computed, ref, watch } from 'vue'
import { useSyncedForm } from '../composables/useSyncedForm.js'
import { useEnums } from '../composables/useEnums.js'
import { getTags, createTag, addPersonTag, removePersonTag } from '../api/client.js'

const props = defineProps({
  visible: Boolean,
  modelValue: Object,
  title: { type: String, default: 'Новый клиент' },
  submitLabel: { type: String, default: 'Сохранить' },
  showStatus: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'save', 'close', 'tagsChanged'])

const defaults = {
  id: undefined,
  first_name: '',
  last_name: '',
  middle_name: '',
  phone: '',
  email: '',
  telegram: '',
  notes: '',
  status: 'active',
  tags: [],
  passport: {
    series: '',
    number: '',
    issued_by: '',
    issued_at: '',
    notes: '',
  },
}

function parsePhone(value) {
  if (!value) return ''
  const cleaned = value.replace(/[^\d+]/g, '')
  if (cleaned.startsWith('+')) {
    return '+' + cleaned.slice(1).replace(/\D/g, '')
  }
  return cleaned.replace(/\D/g, '')
}

function formatPhone(value) {
  if (!value) return ''
  const cleaned = value.replace(/[^\d+]/g, '')
  const hasPlus = cleaned.startsWith('+')
  const digits = hasPlus ? cleaned.slice(1) : cleaned
  if (!digits) return hasPlus ? '+' : ''

  let formatted = hasPlus ? '+' + digits[0] : digits[0]
  const rest = digits.slice(1)
  if (!rest) return formatted

  const area = rest.slice(0, 3)
  formatted += ` (${area}`
  if (rest.length <= 3) {
    return formatted
  }

  const afterArea = rest.slice(3)
  formatted += ') '
  const prefix = afterArea.slice(0, 3)
  formatted += prefix
  if (afterArea.length <= 3) {
    return formatted
  }

  const afterPrefix = afterArea.slice(3)
  formatted += '-' + afterPrefix.slice(0, 2)
  if (afterPrefix.length <= 2) {
    return formatted
  }

  formatted += '-' + afterPrefix.slice(2, 4)
  return formatted
}

const { enums } = useEnums()

const { localForm } = useSyncedForm(
  () => props.modelValue,
  (value) => emit('update:modelValue', value),
  defaults,
  (value) => ({
    id: value.id,
    first_name: value.first_name ?? '',
    last_name: value.last_name ?? '',
    middle_name: value.middle_name ?? '',
    phone: value.phone ?? '',
    email: value.email ?? '',
    telegram: value.telegram ?? '',
    notes: value.notes ?? '',
    status: value.status ?? 'active',
    tags: value.tags ?? [],
    passport: {
      series: value.passport?.series ?? '',
      number: value.passport?.number ?? '',
      issued_by: value.passport?.issued_by ?? '',
      issued_at: value.passport?.issued_at ?? '',
      notes: value.passport?.notes ?? '',
    },
  }),
)

const formattedPhone = computed({
  get() {
    return formatPhone(localForm.value.phone)
  },
  set(value) {
    localForm.value.phone = parsePhone(value)
  },
})

const FALLBACK_PERSON_STATUSES = [
  { value: 'active', label: 'Активный' },
  { value: 'blocked', label: 'Заблокирован' },
  { value: 'archived', label: 'Архивный' },
  { value: 'fired', label: 'Уволен' },
]

const statusOptions = computed(() =>
  enums.value?.person_status?.length ? enums.value.person_status : FALLBACK_PERSON_STATUSES,
)

// ── Теги клиента (редактируются прямо в форме, без отдельной страницы) ──
const isEditing = computed(() => !!localForm.value.id)
const personTags = computed(() => localForm.value.tags || [])

const tagCatalog = ref([])
const tagToAttach = ref(null)
const newTagName = ref('')
const tagsLoading = ref(false)
const tagsSaving = ref(false)

const availableTagsToAttach = computed(() =>
  tagCatalog.value.filter(tag => !personTags.value.includes(tag.name)),
)

async function loadTagCatalog() {
  tagsLoading.value = true
  try { tagCatalog.value = await getTags() }
  catch (error) { console.error('Не удалось загрузить теги', error) }
  finally { tagsLoading.value = false }
}

watch(
  () => props.visible,
  (visible) => { if (visible) loadTagCatalog() },
  { immediate: true },
)

async function handleAttachTag() {
  if (!isEditing.value || !tagToAttach.value) return
  tagsSaving.value = true
  try {
    const tag = tagCatalog.value.find(t => t.id === tagToAttach.value)
    await addPersonTag(localForm.value.id, tagToAttach.value)
    if (tag && !personTags.value.includes(tag.name)) {
      localForm.value.tags = [...personTags.value, tag.name]
    }
    tagToAttach.value = null
    emit('tagsChanged')
  } catch (error) {
    console.error('Не удалось привязать тег', error)
  } finally {
    tagsSaving.value = false
  }
}

async function handleCreateAndAttachTag() {
  if (!isEditing.value || !newTagName.value.trim()) return
  tagsSaving.value = true
  try {
    const tag = await createTag(newTagName.value.trim())
    await addPersonTag(localForm.value.id, tag.id)
    tagCatalog.value = [...tagCatalog.value, tag]
    if (!personTags.value.includes(tag.name)) {
      localForm.value.tags = [...personTags.value, tag.name]
    }
    newTagName.value = ''
    emit('tagsChanged')
  } catch (error) {
    console.error('Не удалось создать и привязать тег', error)
  } finally {
    tagsSaving.value = false
  }
}

async function handleRemoveTag(tagName) {
  if (!isEditing.value) return
  const tag = tagCatalog.value.find(t => t.name === tagName)
  if (!tag) return
  tagsSaving.value = true
  try {
    await removePersonTag(localForm.value.id, tag.id)
    localForm.value.tags = personTags.value.filter(name => name !== tagName)
    emit('tagsChanged')
  } catch (error) {
    console.error('Не удалось отвязать тег', error)
  } finally {
    tagsSaving.value = false
  }
}

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
        <label class="field">
          <span class="field-label">Имя <span class="req">*</span></span>
          <input v-model="localForm.first_name" required placeholder="Иван" />
        </label>
        <label class="field">
          <span class="field-label">Фамилия <span class="req">*</span></span>
          <input v-model="localForm.last_name" required placeholder="Иванов" />
        </label>
        <label class="field">
          <span class="field-label">Отчество</span>
          <input v-model="localForm.middle_name" placeholder="Иванович" />
        </label>
        <label class="field">
          <span class="field-label">Телефон <span class="req">*</span></span>
          <input v-model="formattedPhone" required placeholder="+7 (999) 000-00-00" />
        </label>
        <label class="field">
          <span class="field-label">Email</span>
          <input v-model="localForm.email" type="email" placeholder="ivan@example.com" />
        </label>
        <label class="field">
          <span class="field-label">Telegram</span>
          <input v-model="localForm.telegram" placeholder="@username" />
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
          <textarea v-model="localForm.notes" rows="3" placeholder="Дополнительная информация..."></textarea>
        </label>

        <div class="form-grid full-width passport-section">
          <div class="passport-section-header">Паспортные данные</div>
          <label class="field">
            <span class="field-label">Серия</span>
            <input v-model="localForm.passport.series" placeholder="1234" />
          </label>
          <label class="field">
            <span class="field-label">Номер</span>
            <input v-model="localForm.passport.number" placeholder="567890" />
          </label>
          <label class="field full-width">
            <span class="field-label">Кем выдан</span>
            <input v-model="localForm.passport.issued_by" placeholder="МВД России" />
          </label>
          <label class="field">
            <span class="field-label">Дата выдачи</span>
            <input v-model="localForm.passport.issued_at" type="date" />
          </label>
          <label class="field full-width">
            <span class="field-label">Заметки паспорта</span>
            <textarea v-model="localForm.passport.notes" rows="2" placeholder="Дополнительная информация..."></textarea>
          </label>
        </div>

        <div v-if="isEditing" class="form-grid full-width passport-section tags-section">
          <div class="passport-section-header">Теги</div>
          <div class="full-width tag-chips">
            <span v-for="tagName in personTags" :key="tagName" class="tag-chip removable">
              {{ tagName }}
              <button type="button" class="tag-remove" :disabled="tagsSaving" @click="handleRemoveTag(tagName)">✕</button>
            </span>
            <span v-if="!personTags.length" class="empty-hint">Тегов пока нет</span>
          </div>
          <label class="field">
            <span class="field-label">Привязать существующий тег</span>
            <div class="tag-attach-row">
              <select v-model="tagToAttach" :disabled="tagsSaving || !availableTagsToAttach.length">
                <option :value="null">Выберите тег</option>
                <option v-for="tag in availableTagsToAttach" :key="tag.id" :value="tag.id">{{ tag.name }}</option>
              </select>
              <button type="button" class="btn-ghost" :disabled="tagsSaving || !tagToAttach" @click="handleAttachTag">
                Добавить
              </button>
            </div>
          </label>
          <label class="field">
            <span class="field-label">Или создать новый</span>
            <div class="tag-attach-row">
              <input v-model="newTagName" placeholder="Название тега" :disabled="tagsSaving" />
              <button type="button" class="btn-ghost" :disabled="tagsSaving || !newTagName.trim()" @click="handleCreateAndAttachTag">
                Создать
              </button>
            </div>
          </label>
        </div>
      </div>
      <div class="form-actions">
        <button type="submit" class="btn-primary">{{ submitLabel }}</button>
        <button type="button" class="btn-ghost" @click="emit('close')">Отмена</button>
      </div>
    </form>
  </div>
</template>

<style scoped>
.tag-chips { display: flex; flex-wrap: wrap; gap: 8px; }

.tag-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #ede9fe;
  color: #5b21b6;
  border-radius: 999px;
  padding: 4px 12px;
  font-size: 0.82rem;
  font-weight: 600;
}

.tag-remove {
  border: none;
  background: transparent;
  cursor: pointer;
  color: #7c5cbf;
  font-size: 0.75rem;
  padding: 0;
  line-height: 1;
}
.tag-remove:hover:not(:disabled) { color: #dc2626; }
.tag-remove:disabled { opacity: .5; cursor: not-allowed; }

.empty-hint { color: #9ca3af; font-size: 0.85rem; }

.tag-attach-row { display: flex; gap: 8px; }
.tag-attach-row select,
.tag-attach-row input { flex: 1; min-width: 0; }
.tag-attach-row .btn-ghost { flex-shrink: 0; }
</style>
