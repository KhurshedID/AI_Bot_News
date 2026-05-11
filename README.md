# AIBot — AI Telegram News Publisher

Сервис собирает новости из RSS-лент и публичных Telegram-каналов, фильтрует их по ключевым словам, генерирует Telegram-посты через AI и публикует их в канал.

## Возможности

- парсинг RSS/Atom-лент;
- парсинг публичных Telegram-каналов;
- фильтрация новостей по ключевым словам;
- защита от дублей;
- генерация постов через OpenAI;
- fallback-генерация без API-ключа;
- публикация в Telegram-канал;
- фоновые задачи через Celery и Redis;
- REST API для управления источниками и ключевыми словами.

## Стек

- Python 3.13
- FastAPI
- SQLAlchemy
- Celery
- Redis
- BeautifulSoup
- OpenAI API
- Aiogram
- Docker

## Установка
```bash
git clone <ссылка-на-репозиторий>
cd aibot
uv sync


## Настройка окружения

Скопируйте пример переменных окружения:
cp .env.example .env


Заполните значения в файле .env:
DATABASE_URL=sqlite+aiosqlite:///./aibot.db
REDIS_URL=redis://localhost:6379/0
BOT_TOKEN=your_bot_token
TG_CHANNEL=@your_channel_username
CHATGPT_API_KEY=your_openai_api_key
DEBUG=True
LOG_LEVEL=INFO


## Запуск без Docker

### Запуск Redis
redis-server


### Запуск API
uv run uvicorn app.main:app --reload


API будет доступен по адресу:
text [http://127.0.0.1:8000](http://127.0.0.1:8000)


Swagger-документация:
text [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)


### Запуск Celery worker
uv run celery -A celery_worker.celery_app worker --loglevel=info


### Запуск Celery beat
uv run celery -A celery_worker.celery_app beat --loglevel=info


## Запуск через Docker
bash docker compose up --build


## Примеры API-запросов

### Добавить RSS-источник
curl -X POST [http://127.0.0.1:8000/api/sources](http://127.0.0.1:8000/api/sources) \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Example RSS",
    "type": "site",
    "url": "[https://example.com/rss](https://example.com/rss)",
    "enabled": true
  }'


### Добавить Telegram-источник
curl -X POST [http://127.0.0.1:8000/api/sources](http://127.0.0.1:8000/api/sources) \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Telegram Channel",
    "type": "tg",
    "url": "@example_channel",
    "enabled": true
  }'


### Добавить ключевое слово
curl -X POST [http://127.0.0.1:8000/api/keywords](http://127.0.0.1:8000/api/keywords) \
  -H "Content-Type: application/json" \
  -d '{
    "word": "искусственный интеллект",
    "enabled": true
  }'


### Запустить полный пайплайн
curl -X POST [http://127.0.0.1:8000/api/tasks/run-pipeline](http://127.0.0.1:8000/api/tasks/run-pipeline)


### Сгенерировать пост вручную
curl -X POST [http://127.0.0.1:8000/api/generate](http://127.0.0.1:8000/api/generate) \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Текст новости для генерации Telegram-поста"
  }'


## Основные эндпоинты

| Метод | URL | Назначение |
|---|---|---|
| GET | `/api/sources` | список источников |
| POST | `/api/sources` | создание источника |
| PATCH | `/api/sources/{source_id}` | обновление источника |
| DELETE | `/api/sources/{source_id}` | удаление источника |
| GET | `/api/keywords` | список ключевых слов |
| POST | `/api/keywords` | создание ключевого слова |
| GET | `/api/news` | список новостей |
| GET | `/api/posts` | список постов |
| POST | `/api/generate` | ручная генерация поста |
| POST | `/api/tasks/run-pipeline` | запуск фонового пайплайна |

## Структура проекта
aibot/
├── app/
│   ├── ai/
│   ├── api/
│   ├── news_parser/
│   ├── telegram/
│   ├── config.py
│   ├── main.py
│   ├── models.py
│   ├── tasks.py
│   └── utils.py
├── celery_worker.py
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── README.md