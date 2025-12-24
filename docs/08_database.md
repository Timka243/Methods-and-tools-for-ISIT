# База данных (PostgreSQL)

## СУБД
Используется PostgreSQL (контейнер `postgres:17`), развёртывание выполняется через Docker Compose.

## Структура

### Таблица `roles`
- `id` — PK, идентификатор роли
- `name` — название роли (уникально), например `admin`, `user`

### Таблица `users`
- `id` — PK, идентификатор пользователя
- `username` — логин (уникально)
- `password_hash` — хэш пароля
- `role_id` — FK → `roles(id)` (роль пользователя)
- `full_name` — ФИО (может быть NULL)
- `created_at` — дата/время создания (по умолчанию NOW)

### Таблица `locations`
- `id` — PK, идентификатор локации
- `name` — название локации

### Таблица `visits`
- `id` — PK, идентификатор визита
- `location_id` — FK → `locations(id)`
- `date` — дата визита (NOT NULL)
- `material` — материал/услуга (NOT NULL)
- `spent` — сумма, ₽ (по умолчанию 0)
- `discount` — скидка, ₽ (по умолчанию 0)
- `created_by` — FK → `users(id)` (кто создал запись)

### Таблица `tags`
- `id` — PK, идентификатор тега
- `name` — название тега (уникально)

### Таблица `visit_tags`
Таблица связи многие-ко-многим между `visits` и `tags`.
- `visit_id` — PK, FK → `visits(id)`
- `tag_id` — PK, FK → `tags(id)`

## Связи
- `roles (1) — (N) users`
- `locations (1) — (N) visits`
- `users (1) — (N) visits` по полю `created_by`
- `visits (N) — (N) tags` через `visit_tags`

## Инициализация данных
При первом запуске контейнера БД выполняются SQL-скрипты из папки `db/`, подключённой как `/docker-entrypoint-initdb.d`. Скрипты создают таблицы и заполняют тестовые данные (локации, визиты, пользователи/роли и теги при наличии).

## Запуск

```bash
docker compose up -d --build
