import { ref } from 'vue'
import { getEnums } from '../api/client.js'

// Модульный (не per-component) кэш — справочники одни и те же для всего
// приложения, незачем запрашивать их у сервера повторно на каждую форму.
const enums = ref(null)
const loading = ref(false)
let loadPromise = null

/**
 * useEnums — единая точка получения enum-справочников с backend'а
 * (GET /enums), вместо хардкода списков (типы велосипедов, статусы,
 * владельцы и т.д.) прямо в компонентах.
 *
 * Возвращает reactive-ref `enums` с формой:
 *   { bike_status, bike_type, bike_owner_type, repair_status,
 *     rental_status, owner_type, person_status }
 * каждый — массив { value, label }.
 */
export function useEnums() {
  if (!enums.value && !loadPromise) {
    loading.value = true
    loadPromise = getEnums()
      .then((data) => { enums.value = data })
      .catch((error) => {
        console.error('Не удалось загрузить справочники /enums', error)
      })
      .finally(() => { loading.value = false })
  }

  return { enums, loading }
}
