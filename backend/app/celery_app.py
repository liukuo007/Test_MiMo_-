from __future__ import annotations

from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "mimo",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,
    task_reject_on_worker_lost=True,
    task_soft_time_limit=300,
    task_time_limit=600,
    worker_max_tasks_per_child=1000,
    broker_connection_retry_on_startup=True,
    task_routes={
        "app.tasks.test_execution.execute_test_task": {"queue": "test"},
        "app.tasks.ai_evaluation.run_ai_evaluation": {"queue": "ai"},
        "app.tasks.report_generation.generate_report_task": {"queue": "report"},
        "app.tasks.health_snapshot.compute_health_snapshot": {"queue": "report"},
        "app.tasks.env_health_check.env_health_check_all": {"queue": "report"},
        "app.tasks.stability_analysis.run_stability_analysis": {"queue": "report"},
        "app.tasks.quality_loop_check.evaluate_quality_loop_rules": {"queue": "report"},
    },
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.tasks"])

# Ensure task modules are imported
import app.tasks.test_execution  # noqa
import app.tasks.ai_evaluation  # noqa
import app.tasks.report_generation  # noqa
import app.tasks.health_snapshot  # noqa
import app.tasks.env_health_check  # noqa
import app.tasks.stability_analysis  # noqa
import app.tasks.quality_loop_check  # noqa
