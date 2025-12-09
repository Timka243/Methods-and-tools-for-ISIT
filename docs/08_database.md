# База данных (PostgreSQL)

## СУБД
Используется PostgreSQL (контейнер `postgres:17`), развёртывание выполняется через Docker Compose.

## Структура
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

Связь: `locations (1) — (N) visits`.

## Инициализация данных
При первом запуске контейнера БД выполняются SQL-скрипты из папки `db/`, подключённой как `/docker-entrypoint-initdb.d`.
Скрипты создают таблицы и заполняют тестовые данные (локации и визиты).

## Запуск
```bash
docker compose up -d --build

Полный сброс БД (если нужно заново применить init SQL)
docker compose down -v
docker compose up -d --build
Команда down -v удаляет volume с данными.
