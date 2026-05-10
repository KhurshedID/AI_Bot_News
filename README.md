\# AIBot — AI Telegram News Publisher



AIBot — сервис для автоматического сбора новостей, генерации коротких AI-постов и публикации их в Telegram-канал.



Проект реализован на FastAPI, SQLAlchemy, Celery, Redis и Telegram Bot API.



\## Возможности



\- Сбор новостей из RSS-источников

\- Сбор сообщений из публичных Telegram-каналов

\- Фильтрация новостей по ключевым словам

\- Проверка дублей по URL или заголовку

\- Генерация постов через AI

\- Fallback-генерация без AI API

\- Публикация постов в Telegram-канал

\- Управление источниками через REST API

\- Управление ключевыми словами через REST API

\- Просмотр новостей и постов через API

\- Запуск фонового pipeline через Celery

\- Автоматический запуск pipeline каждые 30 минут через Celery Beat

\- Swagger-документация



\## Стек технологий



\- Python 3.13

\- FastAPI

\- SQLAlchemy

\- SQLite

\- Pydantic Settings

\- Celery

\- Redis

\- aiogram

\- OpenAI API

\- feedparser

\- httpx

\- BeautifulSoup4

\- loguru



\## Настройка окружения



Создайте файл `.env` в корне проекта.



Пример:



env DATABASE\_URL=sqlite+aiosqlite:///./aibot.db REDIS\_URL=redis://localhost:6379/0

BOT\_TOKEN=your\_telegram\_bot\_token TG\_CHANNEL=@your\_channel\_username

CHATGPT\_API\_KEY=your\_openai\_api\_key

DEBUG=false LOG\_LEVEL=INFO





\### Описание переменных окружения



| Переменная | Описание |

|---|---|

| `DATABASE\_URL` | URL базы данных |

| `REDIS\_URL` | URL Redis для Celery |

| `BOT\_TOKEN` | Токен Telegram-бота от BotFather |

| `TG\_CHANNEL` | Username Telegram-канала |

| `CHATGPT\_API\_KEY` | API-ключ OpenAI |

| `DEBUG` | Режим отладки |

| `LOG\_LEVEL` | Уровень логирования |



Важно: файл `.env` нельзя добавлять в GitHub.



\## Установка зависимостей



Если используется `uv`:

bash uv sync





Если нужно установить отдельную зависимость:

bash uv add package\_name





\## Запуск Redis



Через Docker:

bash docker run -d --name aibot-redis -p 6379:6379 redis:7





Если контейнер уже создан:

bash docker start aibot-redis





Проверить запущенные контейнеры:

bash docker ps





\## Запуск FastAPI

bash uv run uvicorn app.main:app --reload





После запуска API будет доступно по адресу:

http://127.0.0.1:8000





Swagger-документация:

http://127.0.0.1:8000/docs





Health check:

http://127.0.0.1:8000/health





\## Запуск Celery worker



На Windows нужно использовать `--pool=solo`:

bash uv run celery -A celery\_worker.celery\_app worker --loglevel=info --pool=solo





Celery Beat запускает pipeline каждые 30 минут.



\## Основные API endpoints



\### Health check

http GET / GET /health





\### Источники новостей

http GET /api/sources GET /api/sources/{source\_id} POST /api/sources PATCH /api/sources/{source\_id} DELETE /api/sources/{source\_id}





Пример создания RSS-источника:

json { "name": "Real Python", "type": "site", "url": "\[https://realpython.com/atom.xml](https://realpython.com/atom.xml)", "enabled": true }





Пример создания Telegram-источника:

json { "name": "Durov Telegram", "type": "tg", "url": "durov", "enabled": true }





\### Ключевые слова

http GET /api/keywords GET /api/keywords/{keyword\_id} POST /api/keywords PATCH /api/keywords/{keyword\_id} DELETE /api/keywords/{keyword\_id}











