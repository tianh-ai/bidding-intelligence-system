"""
Celery worker configuration for async task processing.
"""

from celery import Celery
from core.config import settings
from core.logger import logger

# Initialize Celery app
celery_app = Celery(
    "bidding_worker",
    broker=settings.celery_broker,
    backend=settings.celery_backend,
)

# Configure Celery
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Timezone
    timezone="Asia/Shanghai",
    enable_utc=True,
    
    # Task settings
    task_track_started=True,
    task_time_limit=settings.PARSING_TIMEOUT,
    task_soft_time_limit=settings.PARSING_TIMEOUT - 30,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_extended=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Concurrency
    worker_concurrency=settings.MAX_CONCURRENT_TASKS,
)

logger.info(f"Celery worker initialized with broker: {settings.celery_broker}")

# Import tasks to register them
try:
    import tasks  # noqa
    logger.info("Tasks module imported successfully")
except Exception as e:
    logger.warning(f"Failed to import tasks module: {e}")
