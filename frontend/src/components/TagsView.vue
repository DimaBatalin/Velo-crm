<script setup>
import { ref, onMounted } from 'vue'
import { getTags, createTag, getPeople, addPersonTag, removePersonTag } from '../api/client.js'

const emit = defineEmits(['toast'])

const tags = ref([])
const people = ref([])
const newTagName = ref('')
const creating = ref(false)
const selectedPersonId = ref(null)
const selectedTagId = ref(null)
const assigning = ref(false)

async function loadTags() {
  try { tags.value = await getTags() }
  catch (e) { console.error(e); emit('toast', 'Не удалось загрузить теги.', 'error') }
}

async function loadPeople() {
  try { people.value = await getPeople({ limit: 200 }) }
  catch (e) { console.error(e); emit('toast', 'Не удалось загрузить клиентов.', 'error') }
}

async function handleCreateTag() {
  if (!newTagName.value.trim()) return
  creating.value = true
  try {
    await createTag(newTagName.value.trim())
    newTagName.value = ''
    emit('toast', 'Тег создан.')
    await loadTags()
  } catch (e) {
    console.error(e)
    emit('toast', 'Не удалось создать тег (возможно, уже существует).', 'error')
  } finally {
    creating.value = false
  }
}

async function handleAssign() {
  if (!selectedPersonId.value || !selectedTagId.value) return
  assigning.value = true
  try {
    await addPersonTag(selectedPersonId.value, selectedTagId.value)
    emit('toast', 'Тег привязан к клиенту.')
    await loadPeople()
  } catch (e) {
    console.error(e)
    emit('toast', 'Не удалось привязать тег.', 'error')
  } finally {
    assigning.value = false
  }
}

async function handleRemove(person, tagName) {
  const tag = tags.value.find(t => t.name === tagName)
  if (!tag) return
  try {
    await removePersonTag(person.id, tag.id)
    emit('toast', 'Тег отвязан.')
    await loadPeople()
  } catch (e) {
    console.error(e)
    emit('toast', 'Не удалось отвязать тег.', 'error')
  }
}

function formatPersonName(person) {
  return [person.last_name, person.first_name].filter(Boolean).join(' ') || `#${person.id}`
}

const peopleWithTags = ref([])
function refreshPeopleWithTags() {
  peopleWithTags.value = people.value.filter(p => (p.tags || []).length > 0)
}

onMounted(async () => {
  await Promise.all([loadTags(), loadPeople()])
  refreshPeopleWithTags()
})
</script>

<template>
  <div class="tags-view">
    <div class="tags-columns">

      <!-- Справочник тегов -->
      <div class="card">
        <h3 class="card-title">Справочник тегов</h3>
        <div class="tag-chips">
          <span v-for="tag in tags" :key="tag.id" class="tag-chip">{{ tag.name }}</span>
          <span v-if="!tags.length" class="empty-hint">Тегов пока нет</span>
        </div>

        <form class="inline-form" @submit.prevent="handleCreateTag">
          <input v-model="newTagName" placeholder="Название нового тега" :disabled="creating" />
          <button type="submit" class="btn-primary" :disabled="creating || !newTagName.trim()">
            Создать тег
          </button>
        </form>
      </div>

      <!-- Привязка тега клиенту -->
      <div class="card">
        <h3 class="card-title">Привязать тег клиенту</h3>
        <div class="inline-form">
          <select v-model="selectedPersonId">
            <option :value="null" disabled>Выберите клиента</option>
            <option v-for="p in people" :key="p.id" :value="p.id">{{ formatPersonName(p) }}</option>
          </select>
          <select v-model="selectedTagId">
            <option :value="null" disabled>Выберите тег</option>
            <option v-for="t in tags" :key="t.id" :value="t.id">{{ t.name }}</option>
          </select>
          <button
              type="button"
              class="btn-primary"
              :disabled="assigning || !selectedPersonId || !selectedTagId"
              @click="handleAssign"
          >
            Привязать
          </button>
        </div>
      </div>

    </div>

    <!-- Клиенты с тегами -->
    <div class="card">
      <h3 class="card-title">Клиенты с тегами</h3>
      <table class="table">
        <thead>
        <tr>
          <th>Клиент</th>
          <th>Теги</th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="p in people.filter(x => (x.tags || []).length)" :key="p.id">
          <td>{{ formatPersonName(p) }}</td>
          <td>
            <span v-for="tagName in p.tags" :key="tagName" class="tag-chip removable">
              {{ tagName }}
              <button type="button" class="tag-remove" @click="handleRemove(p, tagName)">✕</button>
            </span>
          </td>
        </tr>
        <tr v-if="!people.filter(x => (x.tags || []).length).length">
          <td colspan="2" class="empty-row">Ни у одного клиента пока нет тегов</td>
        </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.tags-view { display: flex; flex-direction: column; gap: 20px; }
.tags-columns { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
@media (max-width: 900px) { .tags-columns { grid-template-columns: 1fr; } }

.card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 18px 20px;
}

.card-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: #111827;
  margin: 0 0 12px;
}

.tag-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; }

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

.tag-chip.removable { background: #f3f4f6; color: #374151; }

.tag-remove {
  border: none;
  background: transparent;
  cursor: pointer;
  color: #9ca3af;
  font-size: 0.75rem;
  padding: 0;
  line-height: 1;
}
.tag-remove:hover { color: #dc2626; }

.empty-hint { color: #9ca3af; font-size: 0.85rem; }

.inline-form { display: flex; gap: 8px; flex-wrap: wrap; }
.inline-form input, .inline-form select {
  flex: 1;
  min-width: 140px;
  padding: 8px 10px;
  border: 1.5px solid #e5e7eb;
  border-radius: 8px;
  font-size: 0.87rem;
}

.btn-primary {
  background: #7c3aed;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 8px 16px;
  font-size: 0.87rem;
  font-weight: 600;
  cursor: pointer;
}
.btn-primary:disabled { opacity: .6; cursor: not-allowed; }
.btn-primary:hover:not(:disabled) { background: #6d28d9; }

.table { width: 100%; border-collapse: collapse; }
.table th { text-align: left; font-size: 0.78rem; color: #6b7280; padding: 8px 10px; border-bottom: 1px solid #e5e7eb; }
.table td { padding: 10px; border-bottom: 1px solid #f3f4f6; font-size: 0.88rem; }
.empty-row { text-align: center; color: #9ca3af; padding: 20px; }
</style>
