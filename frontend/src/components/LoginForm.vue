<template>
  <div class="login-overlay">
    <div class="login-card">
      <div class="login-logo">
        <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
          <circle cx="10" cy="28" r="8" stroke="#2563eb" stroke-width="2.5" fill="none"/>
          <circle cx="30" cy="28" r="8" stroke="#2563eb" stroke-width="2.5" fill="none"/>
          <path d="M10 28 L20 10 L30 28" stroke="#2563eb" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
          <circle cx="20" cy="10" r="2.5" fill="#2563eb"/>
        </svg>
        <span class="login-logo-text">VELO</span>
      </div>

      <h1 class="login-title">Вход в систему</h1>

      <form class="login-form" @submit.prevent="handleSubmit">
        <div class="field">
          <label class="field-label">Email</label>
          <input
            v-model="email"
            type="email"
            class="field-input"
            placeholder="admin@velo.local"
            autocomplete="username"
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
            placeholder="••••••••"
            autocomplete="current-password"
            :disabled="loading"
            required
          />
        </div>

        <p v-if="error" class="login-error">{{ error }}</p>

        <button type="submit" class="login-btn" :disabled="loading">
          <span v-if="loading" class="spinner"></span>
          <span v-else>Войти</span>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { login } from '../api/auth.js'
import { setToken } from '../api/client.js'

const emit = defineEmits(['authenticated'])

const email    = ref('')
const password = ref('')
const error    = ref('')
const loading  = ref(false)

async function handleSubmit() {
  error.value   = ''
  loading.value = true
  try {
    const { access_token } = await login(email.value, password.value)
    setToken(access_token)
    emit('authenticated', access_token)
  } catch (e) {
    error.value = e.message || 'Ошибка входа'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-overlay {
  position: fixed;
  inset: 0;
  background: #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.login-card {
  background: #fff;
  border-radius: 16px;
  padding: 40px 36px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 4px 24px rgba(0,0,0,.08);
}

.login-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 24px;
}

.login-logo-text {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: .06em;
  color: #1e293b;
}

.login-title {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 24px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  font-size: 13px;
  font-weight: 500;
  color: #64748b;
}

.field-input {
  padding: 10px 12px;
  border: 1.5px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  color: #1e293b;
  transition: border-color .15s;
  outline: none;
}

.field-input:focus {
  border-color: #2563eb;
}

.field-input:disabled {
  background: #f8fafc;
  opacity: .7;
}

.login-error {
  margin: 0;
  padding: 10px 12px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  font-size: 13px;
  color: #dc2626;
}

.login-btn {
  margin-top: 4px;
  padding: 11px;
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background .15s;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 42px;
}

.login-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.login-btn:disabled {
  opacity: .7;
  cursor: not-allowed;
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2.5px solid rgba(255,255,255,.35);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin .6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
