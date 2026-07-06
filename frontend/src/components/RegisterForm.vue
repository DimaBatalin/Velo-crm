<script setup>
import { ref } from 'vue'

const emit = defineEmits(['close', 'created'])

const full_name = ref('')
const email     = ref('')
const password  = ref('')
const confirm   = ref('')
const role      = ref('mechanic')
const error     = ref('')
const success   = ref('')
const loading   = ref(false)

async function handleSubmit() {
  error.value   = ''
  success.value = ''

  if (password.value !== confirm.value) {
    error.value = 'Пароли не совпадают'
    return
  }
  if (password.value.length < 6) {
    error.value = 'Пароль минимум 6 символов'
    return
  }

  loading.value = true
  try {
    const token = localStorage.getItem('velo_token')
    const res = await fetch('http://localhost:8000/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        full_name: full_name.value,
        email:     email.value,
        password:  password.value,
        role:      role.value,
      }),
    })

    if (!res.ok) {
      const data = await res.json().catch(() => ({}))
      throw new Error(data.detail || `Ошибка ${res.status}`)
    }

    const user = await res.json()
    success.value = `Пользователь ${user.email} создан`
    emit('created', user)

    // Reset form
    full_name.value = ''
    email.value     = ''
    password.value  = ''
    confirm.value   = ''
    role.value      = 'mechanic'
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal-card">

      <div class="modal-header">
        <h2 class="modal-title">Новый пользователь</h2>
        <button class="modal-close" @click="emit('close')" aria-label="Закрыть">✕</button>
      </div>

      <form @submit.prevent="handleSubmit" class="modal-body">

        <div class="field">
          <label class="field-label">Полное имя</label>
          <input
            v-model="full_name"
            type="text"
            class="field-input"
            placeholder="Иван Иванов"
            :disabled="loading"
            required
          />
        </div>

        <div class="field">
          <label class="field-label">Email</label>
          <input
            v-model="email"
            type="text"
            class="field-input"
            placeholder="ivan@example.com"
            :disabled="loading"
            required
          />
        </div>

        <div class="field">
          <label class="field-label">Пароль</label>
          <input
            v-model="password"
            type="password"
            class="field-input"
            placeholder="Минимум 6 символов"
            :disabled="loading"
            autocomplete="new-password"
            required
          />
        </div>

        <div class="field">
          <label class="field-label">Повторите пароль</label>
          <input
            v-model="confirm"
            type="password"
            class="field-input"
            placeholder="Повторите пароль"
            :disabled="loading"
            autocomplete="new-password"
            required
          />
        </div>

        <div class="field">
          <label class="field-label">Роль</label>
          <select v-model="role" class="field-input" :disabled="loading" required>
            <option value="admin">Администратор</option>
            <option value="mechanic">Механик</option>
            <option value="manager">Менеджер</option>
          </select>
        </div>

        <p v-if="error"   class="msg msg--error">{{ error }}</p>
        <p v-if="success" class="msg msg--success">✓ {{ success }}</p>

        <div class="modal-actions">
          <button type="button" class="btn btn--ghost" @click="emit('close')" :disabled="loading">
            Отмена
          </button>
          <button type="submit" class="btn btn--primary" :disabled="loading">
            <span v-if="loading" class="spinner"></span>
            <span v-else>Создать</span>
          </button>
        </div>

      </form>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, .45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 16px;
}

.modal-card {
  background: #fff;
  border-radius: 16px;
  width: 100%;
  max-width: 420px;
  box-shadow: 0 8px 40px rgba(0,0,0,.15);
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 0;
}

.modal-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #111827;
  margin: 0;
}

.modal-close {
  border: none;
  background: transparent;
  cursor: pointer;
  color: #9ca3af;
  font-size: 1rem;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background .15s;
}
.modal-close:hover { background: #f3f4f6; color: #111827; }

.modal-body {
  padding: 20px 24px 24px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.field { display: flex; flex-direction: column; gap: 5px; }

.field-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: #374151;
  text-transform: uppercase;
  letter-spacing: .04em;
}

.field-input {
  padding: 9px 12px;
  border: 1.5px solid #e5e7eb;
  border-radius: 8px;
  font-size: 0.9rem;
  color: #111827;
  outline: none;
  transition: border-color .15s;
}
.field-input:focus   { border-color: #7c3aed; }
.field-input:disabled { background: #f9fafb; opacity: .7; }

.msg {
  margin: 0;
  padding: 10px 12px;
  border-radius: 8px;
  font-size: 0.85rem;
}
.msg--error   { background: #fef2f2; border: 1px solid #fecaca; color: #dc2626; }
.msg--success { background: #f0fdf4; border: 1px solid #bbf7d0; color: #16a34a; }

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 4px;
}

.btn {
  padding: 9px 20px;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: background .15s, opacity .15s;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 90px;
  min-height: 38px;
}
.btn:disabled { opacity: .6; cursor: not-allowed; }

.btn--ghost {
  background: #f3f4f6;
  color: #374151;
}
.btn--ghost:hover:not(:disabled) { background: #e5e7eb; }

.btn--primary {
  background: #7c3aed;
  color: #fff;
}
.btn--primary:hover:not(:disabled) { background: #6d28d9; }

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,.35);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin .6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Mobile */
@media (max-width: 480px) {
  .modal-card { border-radius: 12px; }
  .modal-actions { flex-direction: column-reverse; }
  .btn { width: 100%; }
}
</style>
