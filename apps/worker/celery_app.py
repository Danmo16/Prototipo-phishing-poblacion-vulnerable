# apps/worker/celery_app.py
from celery import Celery
from core.config.settings import settings

celery_app = Celery(
    "worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

celery_app.conf.worker_pool = "solo"
celery_app.conf.worker_concurrency = 1
celery_app.conf.broker_connection_retry_on_startup = True

import apps.worker.tasks  # noqa: F401