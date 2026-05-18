from __future__ import annotations

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # 应用
    app_name: str = "mimo"
    app_env: str = "development"
    app_debug: bool = True
    app_secret_key: str = ""
    app_port: int = 8000

    # 数据库
    database_url: str = "postgresql+asyncpg://mimo:mimo@localhost:5432/mimo"
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # Redis
    redis_url: str = "redis://localhost:6479/0"

    # Kafka
    kafka_bootstrap_servers: str = "localhost:9192"

    # Elasticsearch
    elasticsearch_url: str = "http://localhost:9320"

    # ClickHouse
    clickhouse_url: str = "http://localhost:8223"

    # MQTT
    mqtt_broker_url: str = "mqtt://localhost:1883"
    mqtt_username: str = ""
    mqtt_password: str = ""

    # Celery
    celery_broker_url: str = "redis://localhost:6479/1"
    celery_result_backend: str = "redis://localhost:6479/2"

    # WireMock
    wiremock_url: str = "http://localhost:8080"

    # MeterSphere
    metersphere_url: str = "http://localhost:8081"
    ms_access_key: str = ""
    ms_secret_key: str = ""
    ms_project_id: str = "mimo-project-001"
    ms_sync_enabled: bool = False

    # JWT
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # 日志
    log_level: str = "INFO"
    log_format: str = "json"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
