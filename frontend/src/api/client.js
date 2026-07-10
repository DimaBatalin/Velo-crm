import { API_URL } from './config'

// ── Token storage ─────────────────────────────────────────────
export function getToken() {
  return localStorage.getItem('velo_token')
}

export function setToken(token) {
  localStorage.setItem('velo_token', token)
}

export function removeToken() {
  localStorage.removeItem('velo_token')
}

// ── Core request ──────────────────────────────────────────────
function buildQuery(params = {}) {
  const query = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === '') continue
    query.set(key, String(value))
  }
  return query
}

async function request(path, options = {}) {
  const token = getToken()

  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  }

  const response = await fetch(`${API_URL}${path}`, {
    method: options.method ?? 'GET',
    headers,
    body: options.data !== undefined ? JSON.stringify(options.data) : undefined,
  })

  // Token expired or invalid — clear and redirect to login
  if (response.status === 401) {
    removeToken()
    window.dispatchEvent(new Event('velo:unauthorized'))
    throw new Error('Unauthorized')
  }

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`API request failed: ${response.status} ${errorText}`)
  }

  if (response.status === 204) return null

  const contentType = response.headers.get('content-type') || ''
  if (!contentType.includes('application/json')) return response.text()

  return response.json()
}

export async function getApiMessage() {
  return request('/')
}

// ── People ────────────────────────────────────────────────
export async function getPeople({ search, status, limit = 100, offset = 0 } = {}) {
  const query = buildQuery({ search, status, limit, offset })
  return request(`/people?${query.toString()}`)
}

export async function createPerson(data) {
  return request('/people', { method: 'POST', data })
}

export async function updatePerson(personId, data) {
  return request(`/people/${personId}`, { method: 'PUT', data })
}

// ── Bikes ─────────────────────────────────────────────────
export async function getBikes({ search, status, bike_type, owner_type, limit = 100, offset = 0 } = {}) {
  const query = buildQuery({ search, status, bike_type, owner_type, limit, offset })
  return request(`/bikes?${query.toString()}`)
}

export async function createBike(data) {
  return request('/bikes', { method: 'POST', data })
}

export async function updateBike(bikeId, data) {
  return request(`/bikes/${bikeId}`, { method: 'PUT', data })
}

// ── Repairs ───────────────────────────────────────────────
export async function getRepairs({ bike_id, client_id, status, limit = 100, offset = 0 } = {}) {
  const query = buildQuery({ bike_id, client_id, status, limit, offset })
  return request(`/repairs?${query.toString()}`)
}

export async function getRepair(repairId) {
  return request(`/repairs/${repairId}`)
}

export async function createRepair(data) {
  return request('/repairs', { method: 'POST', data })
}

export async function updateRepair(repairId, data) {
  return request(`/repairs/${repairId}`, { method: 'PUT', data })
}

export async function deleteRepair(repairId) {
  return request(`/repairs/${repairId}`, { method: 'DELETE' })
}

export async function addRepairService(repairId, data) {
  return request(`/repairs/${repairId}/services`, { method: 'POST', data })
}

export async function removeRepairService(repairId, repairServiceId) {
  return request(`/repairs/${repairId}/services/${repairServiceId}`, { method: 'DELETE' })
}

export async function addRepairPart(repairId, data) {
  return request(`/repairs/${repairId}/parts`, { method: 'POST', data })
}

export async function removeRepairPart(repairId, repairPartId) {
  return request(`/repairs/${repairId}/parts/${repairPartId}`, { method: 'DELETE' })
}

export async function getRepairSummary(repairId) {
  return request(`/repairs/${repairId}/summary`)
}

// ── Rentals ───────────────────────────────────────────────
export async function getRentals({ bike_id, person_id, status, limit = 100, offset = 0 } = {}) {
  const query = buildQuery({ bike_id, person_id, status, limit, offset })
  return request(`/rentals?${query.toString()}`)
}

export async function getRental(rentalId) {
  return request(`/rentals/${rentalId}`)
}

export async function createRental(data) {
  return request('/rentals', { method: 'POST', data })
}

export async function updateRental(rentalId, data) {
  return request(`/rentals/${rentalId}`, { method: 'PUT', data })
}

export async function closeRental(rentalId, data = {}) {
  return request(`/rentals/${rentalId}/close`, { method: 'POST', data })
}

export async function deleteRental(rentalId) {
  return request(`/rentals/${rentalId}`, { method: 'DELETE' })
}

// ── Parts ─────────────────────────────────────────────────
export async function getParts({ search, category, owner, lowStock, limit = 100, offset = 0 } = {}) {
  const query = buildQuery({
    search, category, owner,
    low_stock: lowStock,
    limit, offset,
  })
  return request(`/parts?${query.toString()}`)
}

export async function createPart(data) {
  return request('/parts', { method: 'POST', data })
}

export async function updatePart(partId, data) {
  return request(`/parts/${partId}`, { method: 'PUT', data })
}

export async function deletePart(partId) {
  return request(`/parts/${partId}`, { method: 'DELETE' })
}

// ── Services ──────────────────────────────────────────────
export async function getServices({ search, limit = 100, offset = 0 } = {}) {
  const query = buildQuery({ search, limit, offset })
  return request(`/services?${query.toString()}`)
}

export async function getService(serviceId) {
  return request(`/services/${serviceId}`)
}

export async function createService(data) {
  return request('/services', { method: 'POST', data })
}

export async function updateService(serviceId, data) {
  return request(`/services/${serviceId}`, { method: 'PUT', data })
}

export async function deleteService(serviceId) {
  return request(`/services/${serviceId}`, { method: 'DELETE' })
}

// ── Passport ──────────────────────────────────────────────
export async function getPassport(personId) {
  return request(`/people/${personId}/passport`)
}

export async function createPassport(personId, data) {
  return request(`/people/${personId}/passport`, { method: 'POST', data })
}

export async function updatePassport(personId, data) {
  return request(`/people/${personId}/passport`, { method: 'PUT', data })
}

export async function deletePassport(personId) {
  return request(`/people/${personId}/passport`, { method: 'DELETE' })
}

// ── Tags (2.5) ────────────────────────────────────────────
export async function getTags() {
  return request('/tags')
}

export async function createTag(name) {
  return request('/tags', { method: 'POST', data: { name } })
}

export async function addPersonTag(personId, tagId) {
  return request(`/people/${personId}/tags`, { method: 'POST', data: { tag_id: tagId } })
}

export async function removePersonTag(personId, tagId) {
  return request(`/people/${personId}/tags/${tagId}`, { method: 'DELETE' })
}

// ── Analytics (2.6) ───────────────────────────────────────
export async function getPartsProfit() {
  return request('/analytics/parts/profit')
}

export async function getPartsTop(limit = 10) {
  return request(`/analytics/parts/top?limit=${limit}`)
}

export async function getPartsConsumption(period = 'week') {
  return request(`/analytics/parts/consumption?period=${period}`)
}

export async function getPartsPurchases(period = 'week') {
  return request(`/analytics/parts/purchases?period=${period}`)
}

export async function getServicesTop(limit = 10) {
  return request(`/analytics/services/top?limit=${limit}`)
}

export async function getServicesRevenue(period = 'week') {
  return request(`/analytics/services/revenue?period=${period}`)
}

/** Скачивает xlsx-отчёт и инициирует сохранение файла в браузере. */
export async function downloadAnalyticsExport(period = 'week') {
  const token = getToken()
  const response = await fetch(`${API_URL}/analytics/export?period=${period}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!response.ok) throw new Error(`Export failed: ${response.status}`)
  const blob = await response.blob()
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'report.xlsx'
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(url)
}

// ── Enums (справочники со значениями и человекочитаемыми label) ──
export async function getEnums() {
  return request('/enums')
}
