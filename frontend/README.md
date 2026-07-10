# Velo-CRM — frontend

Vue 3 + Vite, без роутера — переключение страниц реализовано вручную
(`activePage` в `App.vue`). Данные — только через REST API backend'а
(`src/api/client.js`, `src/api/auth.js`).

## Установка и запуск

```bash
npm install
npm run dev        # http://localhost:5173 (или другой свободный порт)
npm run build       # production-сборка в dist/
npm run preview      # локальный просмотр production-сборки
```

> **Важно:** адрес backend'а сейчас захардкожен как `http://localhost:8000`
> в `src/api/client.js` и `src/api/auth.js` (константа `API_URL`). Если backend
> крутится на другом хосте/порте — поправьте эту константу в обоих файлах
> (или вынесите в `.env`/`import.meta.env.VITE_API_URL`, если понадобится
> несколько окружений).

## Структура

```
src/
├── api/
│   ├── client.js    — все REST-запросы к backend (кроме auth)
│   └── auth.js       — login / getMe
├── composables/
│   ├── useEnums.js        — модульный кэш GET /enums (справочники статусов/типов)
│   └── useSyncedForm.js   — безопасная синхронизация локальной копии формы с v-model
├── components/
│   ├── PersonForm.vue, BikeForm.vue, PartForm.vue,
│   │   RepairForm.vue, RentalForm.vue   — формы создания/редактирования
│   ├── AnalyticsView.vue   — дашборд аналитики + экспорт в Excel (2.6)
│   ├── LoginForm.vue, RegisterForm.vue  — аутентификация, создание сотрудников
│   └── SidebarMenu.vue, TopbarSearch.vue, PageHeader.vue — каркас интерфейса
└── App.vue           — состояние приложения и переключение страниц
```

## Страницы

| Страница     | Раздел ТЗ | Компонент/логика                              |
|--------------|-----------|-------------------------------------------------|
| Аренды       | —         | таблица в `App.vue` + `RentalForm`             |
| Клиенты      | —         | таблица в `App.vue` + `PersonForm` (теги, паспорт, статус — редактируются прямо в форме) |
| Велосипеды   | —         | таблица в `App.vue` + `BikeForm`                |
| Ремонты      | 2.2–2.4   | таблица в `App.vue` (со стоимостью) + `RepairForm` (услуги/запчасти появляются только после создания ремонта, описание проблемы необязательно) |
| Запчасти     | 2.1       | таблица в `App.vue` + `PartForm` (min_stock)    |
| История      | —         | сводная лента ремонтов и аренд                  |
| Аналитика    | 2.6       | `AnalyticsView.vue`                              |

> Отдельной страницы «Теги» больше нет (`TagsView.vue` удалён) — привязка,
> отвязка и создание тегов клиента происходят прямо в `PersonForm.vue` при
> редактировании клиента, а сами теги видны колонкой в таблице «Клиенты».

## Справочники статусов/типов (`useEnums`)

Все опции выпадающих списков и человекочитаемые лейблы статусов (`bike_status`,
`bike_type`, `bike_owner_type`, `repair_status`, `rental_status`, `owner_type`,
`person_status`) приходят с backend'а через `GET /enums` (см. `useEnums.js`),
а не хардкодятся в компонентах. Каждый компонент, использующий `useEnums()`,
держит небольшой `FALLBACK_*`-набор на случай, если `/enums` ещё не
загрузился или недоступен — так форма не остаётся совсем без опций.
Цвета бейджей (какой статус какой класс `.badge` получает) — это чисто
визуальное решение, которое `/enums` не хранит и хранить не должно; оно
живёт локально в `App.vue` (`repairStatusBadge`/`rentalStatusBadge`).

## Роли

Роль сотрудника приходит с backend'а (`GET /auth/me` → `role`). Создание
нового пользователя (`RegisterForm.vue`) доступно только `admin`; сам backend
вернёт `403`, если запрос выполняет не-admin — UI показывает текст ошибки
как есть.

Разграничение прав на уровне интерфейса (скрытие недоступных кнопок для
конкретных ролей) пока не реализовано — все формы показываются всем
залогиненным пользователям, а фактическое разрешение проверяет backend
(при `403` показывается тост с ошибкой). Это осознанное упрощение: явную
проверку прав в UI стоит добавить, если станет важно скрывать сами кнопки,
а не просто блокировать действие.

---

Ниже — исходный boilerplate Vite/Vue, оставлен как есть:

This template should help get you started developing with Vue 3 in Vite.

## Recommended IDE Setup

[VS Code](https://code.visualstudio.com/) + [Vue (Official)](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur).

## Customize configuration

See [Vite Configuration Reference](https://vite.dev/config/).
