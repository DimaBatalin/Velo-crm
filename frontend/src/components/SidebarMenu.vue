<script setup>
const props = defineProps({
  navItems:   { type: Array,  default: () => [] },
  activePage: { type: String, required: true },
  user:       { type: Object, default: null },
})
const emit = defineEmits(['selectPage', 'logout', 'openRegister'])
</script>

<template>
  <aside class="sidebar">

    <!-- Brand + user info -->
    <div class="brand">
      <div class="brand-icon">🚲</div>
      <div class="brand-text">
        <p class="brand-name">BikeCRM</p>
        <p class="brand-email" :title="user?.email">{{ user?.email ?? '—' }}</p>
      </div>
    </div>

    <!-- Navigation -->
    <nav class="menu">
      <button
        v-for="item in navItems"
        :key="item.id"
        :class="['menu-item', { active: activePage === item.id }]"
        @click="emit('selectPage', item.id)"
      >
        {{ item.label }}
      </button>
    </nav>

    <!-- Bottom actions -->
    <div class="sidebar-footer">
      <button class="footer-btn" @click="emit('openRegister')">
        Добавить пользователя
      </button>
      <button class="footer-btn footer-btn--logout" @click="emit('logout')">
        Выйти
      </button>
    </div>

  </aside>
</template>

<style scoped>
.sidebar {
  background: #fff;
  border-right: 1px solid #e5e7eb;
  padding: 20px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
}

/* ── Brand ─────────────────────────────────────────────────── */
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px 16px;
  border-bottom: 1px solid #f3f4f6;
  margin-bottom: 6px;
  min-width: 0;
}

.brand-icon { font-size: 1.4rem; flex-shrink: 0; }

.brand-text { min-width: 0; }

.brand-name {
  font-size: 1rem;
  font-weight: 700;
  color: #111827;
  line-height: 1.2;
  white-space: nowrap;
}

.brand-email {
  font-size: 0.72rem;
  color: #9ca3af;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 160px;
}

/* ── Nav ───────────────────────────────────────────────────── */
.menu {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}

.menu-item {
  width: 100%;
  text-align: left;
  border: none;
  background: transparent;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  color: #6b7280;
  font-size: 0.9rem;
  font-weight: 500;
  transition: background 0.15s, color 0.15s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.menu-item:hover  { background: #f3f4f6; color: #111827; }
.menu-item.active { background: #7c3aed; color: #fff; font-weight: 600; }
.menu-icon { font-size: 1rem; width: 20px; text-align: center; }

/* ── Footer ────────────────────────────────────────────────── */
.sidebar-footer {
  border-top: 1px solid #f3f4f6;
  padding-top: 10px;
  margin-top: auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.footer-btn {
  width: 100%;
  text-align: left;
  border: none;
  background: transparent;
  padding: 9px 12px;
  border-radius: 8px;
  cursor: pointer;
  color: #6b7280;
  font-size: 0.875rem;
  font-weight: 500;
  transition: background 0.15s, color 0.15s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.footer-btn:hover { background: #f3f4f6; color: #111827; }

.footer-btn--logout:hover {
  background: #fef2f2;
  color: #dc2626;
}

.footer-btn-icon { font-size: 1rem; width: 20px; text-align: center; }
</style>
