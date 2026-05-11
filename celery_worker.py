"""Настройка Celery-приложения и расписания фоновых задач."""

from celery import Celery

from app.config import settings


celery_app = Celery(
    "aibot",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks"],
)

celery_app.conf.timezone = "UTC"

celery_app.conf.beat_schedule = {
    "run-pipeline-every-30-minutes": {
        "task": "app.tasks.run_pipeline_task",
        "schedule": 30 * 60,
    },
}