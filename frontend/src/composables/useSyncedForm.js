import { ref, watch } from 'vue'

/**
 * useSyncedForm — безопасная синхронизация локальной копии формы
 * с объектом, приходящим через v-model (props.modelValue).
 *
 * Проблема, которую это решает:
 *   Раньше формы делали так:
 *     watch(() => props.modelValue, v => { localForm.value = {...v} }, { deep: true, immediate: true })
 *     watch(localForm, v => emit('update:modelValue', { ...v }), { deep: true })
 *
 *   Оба watch — глубокие и оба создают НОВЫЙ объект при каждом срабатывании.
 *   Новый объект — это новая ссылка, поэтому первый watch считает
 *   props.modelValue "изменившимся" даже если содержимое совпадает,
 *   что снова перезаписывает localForm, что снова триггерит второй watch,
 *   и так до бесконечности — вкладка/форма подвисает на первом же
 *   нажатии клавиши в любом текстовом поле.
 *
 * Решение: сравниваем сериализованное содержимое с тем, что мы сами
 * только что отправили/приняли, и игнорируем эхо от собственного же
 * обновления — цикл разрывается.
 *
 * @param {import('vue').Ref | (() => any)} propsModelValueGetter — геттер props.modelValue
 * @param {(emitValue: any) => void} emitUpdate — функция, вызывающая emit('update:modelValue', value)
 * @param {object} defaults — значения по умолчанию для новой (пустой) записи
 * @param {(value: object) => object} mapIncoming — необязательный маппер входящего значения -> localForm
 */
export function useSyncedForm(propsModelValueGetter, emitUpdate, defaults, mapIncoming) {
  const localForm = ref({ ...defaults })
  let lastSyncedJson = null

  watch(
    propsModelValueGetter,
    (value) => {
      if (!value) return
      const mapped = mapIncoming ? mapIncoming(value) : { ...defaults, ...value }
      const json = JSON.stringify(mapped)
      if (json === lastSyncedJson) return // эхо нашего же emit — игнорируем
      lastSyncedJson = json
      localForm.value = mapped
    },
    { immediate: true, deep: true },
  )

  watch(
    localForm,
    (value) => {
      const json = JSON.stringify(value)
      if (json === lastSyncedJson) return
      lastSyncedJson = json
      emitUpdate({ ...value })
    },
    { deep: true },
  )

  function reset() {
    lastSyncedJson = null
    localForm.value = { ...defaults }
  }

  return { localForm, reset }
}
