from celery import Celery
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "satsverdant",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "app.workers.tasks.classify_submission": {"queue": "classification"},
        "app.workers.tasks.pin_to_ipfs": {"queue": "storage"},
        "app.workers.tasks.mint_tokens": {"queue": "blockchain"},
        "app.workers.tasks.confirm_transaction": {"queue": "blockchain"},
        "app.workers.tasks.calculate_and_create_reward": {"queue": "rewards"},
        "app.workers.tasks.distribute_reward": {"queue": "blockchain"},
    },
    task_default_queue="default",
    task_default_exchange="satsverdant",
    task_default_routing_key="default",
)

# Import tasks to register them
from . import tasks
