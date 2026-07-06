<script setup>
import { ref, onMounted, watch } from 'vue'
import {
  getPartsProfit, getPartsTop, getPartsConsumption,
  getServicesTop, getServicesRevenue, downloadAnalyticsExport,
} from '../api/client.js'

const emit = defineEmits(['toast'])

const period = ref('week')
const loading = ref(false)
const exporting = ref(false)

const profit = ref(null)
const topParts = ref([])
const consumption = ref(null)
const topServices = ref([])
const servicesRevenue = ref(null)

async function loadAll() {
  loading.value = true
  try {
    const [p, tp, c, ts, sr] = await Promise.all([
      getPartsProfit(),
      getPartsTop(10),
      getPartsConsumption(period.value),
      getServicesTop(10),
      getServicesRevenue(period.value),
    ])
    profit.value = p
    topParts.value = tp
    consumption.value = c
    topServices.value = ts
    servicesRevenue.value = sr
  } catch (e) {
    console.error(e)
    emit('toast', 'Не удалось загрузить аналитику.', 'error')
  } finally {
    loading.value = false
  }
}

async function handleExport() {
  exporting.value = true
  try {
    await downloadAnalyticsExport(period.value)
    emit('toast', 'Отчёт скачан.')
  } catch (e) {
    console.error(e)
    emit('toast', 'Не удалось скачать отчёт.', 'error')
  } finally {
    exporting.value = false
  }
}

function fmt(n) {
  return (n ?? 0).toLocaleString('ru-RU', { maximumFractionDigits: 2 }) + ' ₽'
}

watch(period, loadAll)
onMounted(loadAll)
</script>

<template>
  <div class="analytics-view">

    <div class="analytics-toolbar">
      <div class="period-toggle">
        <button :class="['period-btn', { active: period === 'week' }]" @click="period = 'week'">Неделя</button>
        <button :class="['period-btn', { active: period === 'month' }]" @click="period = 'month'">Месяц</button>
      </div>
      <button class="btn-primary" :disabled="exporting" @click="handleExport">
        {{ exporting ? 'Формируем...' : '⬇ Скачать Excel-отчёт' }}
      </button>
    </div>

    <div v-if="loading" class="loading-row"><span class="spinner"></span> Загрузка аналитики...</div>

    <template v-else>
      <!-- Прибыль по владельцам -->
      <div class="card">
        <h3 class="card-title">Заработок по запчастям (по владельцам)</h3>
        <div class="owner-grid">
          <div class="owner-card">
            <p class="owner-name">Кирилл</p>
            <p class="owner-metric">Закупка: {{ fmt(profit?.kirill?.cost) }}</p>
            <p class="owner-metric">Выручка: {{ fmt(profit?.kirill?.revenue) }}</p>
            <p class="owner-metric owner-profit">Прибыль: {{ fmt(profit?.kirill?.profit) }}</p>
          </div>
          <div class="owner-card">
            <p class="owner-name">Виталий</p>
            <p class="owner-metric">Закупка: {{ fmt(profit?.vitaly?.cost) }}</p>
            <p class="owner-metric">Выручка: {{ fmt(profit?.vitaly?.revenue) }}</p>
            <p class="owner-metric owner-profit">Прибыль: {{ fmt(profit?.vitaly?.profit) }}</p>
          </div>
        </div>
      </div>

      <div class="analytics-columns">
        <!-- Топ запчастей -->
        <div class="card">
          <h3 class="card-title">Топ-10 запчастей по использованию</h3>
          <table class="table">
            <thead><tr><th>Запчасть</th><th class="col-right">Списано, шт.</th></tr></thead>
            <tbody>
            <tr v-for="item in topParts" :key="item.part_id">
              <td>{{ item.name }}</td>
              <td class="col-right">{{ item.usage_count }}</td>
            </tr>
            <tr v-if="!topParts.length"><td colspan="2" class="empty-row">Нет данных</td></tr>
            </tbody>
          </table>
        </div>

        <!-- Топ услуг -->
        <div class="card">
          <h3 class="card-title">Топ-10 услуг по использованию</h3>
          <table class="table">
            <thead><tr><th>Услуга</th><th class="col-right">Использований</th></tr></thead>
            <tbody>
            <tr v-for="item in topServices" :key="item.service_id">
              <td>{{ item.name }}</td>
              <td class="col-right">{{ item.usage_count }}</td>
            </tr>
            <tr v-if="!topServices.length"><td colspan="2" class="empty-row">Нет данных</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="analytics-columns">
        <!-- Расход запчастей за период -->
        <div class="card">
          <h3 class="card-title">
            Расход запчастей за {{ period === 'week' ? 'неделю' : 'месяц' }}
            <span class="card-total">Итого: {{ consumption?.total_quantity ?? 0 }} шт.</span>
          </h3>
          <table class="table">
            <thead><tr><th>Запчасть</th><th class="col-right">Списано, шт.</th></tr></thead>
            <tbody>
            <tr v-for="item in (consumption?.items || [])" :key="item.part_id">
              <td>{{ item.name }}</td>
              <td class="col-right">{{ item.quantity }}</td>
            </tr>
            <tr v-if="!(consumption?.items || []).length"><td colspan="2" class="empty-row">Нет данных</td></tr>
            </tbody>
          </table>
        </div>

        <!-- Выручка по услугам за период -->
        <div class="card">
          <h3 class="card-title">
            Выручка по услугам за {{ period === 'week' ? 'неделю' : 'месяц' }}
            <span class="card-total">Итого: {{ fmt(servicesRevenue?.total_revenue) }}</span>
          </h3>
          <table class="table">
            <thead><tr><th>Услуга</th><th class="col-right">Кол-во</th><th class="col-right">Выручка</th></tr></thead>
            <tbody>
            <tr v-for="item in (servicesRevenue?.items || [])" :key="item.service_id">
              <td>{{ item.name }}</td>
              <td class="col-right">{{ item.usage_count }}</td>
              <td class="col-right">{{ fmt(item.revenue) }}</td>
            </tr>
            <tr v-if="!(servicesRevenue?.items || []).length"><td colspan="3" class="empty-row">Нет данных</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.analytics-view { display: flex; flex-direction: column; gap: 20px; }

.analytics-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;
}

.period-toggle { display: flex; gap: 6px; background: #f3f4f6; padding: 4px; border-radius: 10px; }
.period-btn {
  border: none; background: transparent; padding: 6px 16px; border-radius: 8px;
  font-size: 0.85rem; font-weight: 600; color: #6b7280; cursor: pointer;
}
.period-btn.active { background: #fff; color: #7c3aed; box-shadow: 0 1px 3px rgba(0,0,0,.08); }

.btn-primary {
  background: #7c3aed; color: #fff; border: none; border-radius: 8px;
  padding: 9px 18px; font-size: 0.87rem; font-weight: 600; cursor: pointer;
}
.btn-primary:disabled { opacity: .6; cursor: not-allowed; }
.btn-primary:hover:not(:disabled) { background: #6d28d9; }

.card { background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 18px 20px; }
.card-title {
  font-size: 0.95rem; font-weight: 700; color: #111827; margin: 0 0 12px;
  display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 6px;
}
.card-total { font-size: 0.8rem; font-weight: 600; color: #7c3aed; }

.owner-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 640px) { .owner-grid { grid-template-columns: 1fr; } }
.owner-card { background: #f9fafb; border-radius: 10px; padding: 14px 16px; }
.owner-name { font-weight: 700; color: #111827; margin: 0 0 6px; }
.owner-metric { margin: 2px 0; font-size: 0.85rem; color: #6b7280; }
.owner-profit { color: #16a34a; font-weight: 700; }

.analytics-columns { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
@media (max-width: 900px) { .analytics-columns { grid-template-columns: 1fr; } }

.table { width: 100%; border-collapse: collapse; }
.table th { text-align: left; font-size: 0.78rem; color: #6b7280; padding: 8px 10px; border-bottom: 1px solid #e5e7eb; }
.table td { padding: 8px 10px; border-bottom: 1px solid #f3f4f6; font-size: 0.85rem; }
.col-right { text-align: right; }
.empty-row { text-align: center; color: #9ca3af; padding: 16px; }

.loading-row { display: flex; align-items: center; gap: 8px; color: #6b7280; padding: 20px; }
.spinner {
  width: 16px; height: 16px; border: 2px solid #e5e7eb; border-top-color: #7c3aed;
  border-radius: 50%; animation: spin .6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
