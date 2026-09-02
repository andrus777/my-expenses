import os
from datetime import timedelta


class BaseConfig:
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://my_expenses:change-me-for-local-development@localhost:5432/my_expenses",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "development-only-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    RATELIMIT_STORAGE_URI = REDIS_URL
    RATELIMIT_HEADERS_ENABLED = True
    CELERY = {
        "broker_url": REDIS_URL,
        "result_backend": REDIS_URL,
        "task_ignore_result": True,
        "broker_connection_retry_on_startup": True,
    }
    JSON_SORT_KEYS = False
    RECEIPT_PROVIDER = os.getenv("RECEIPT_PROVIDER", "fake")
    RECEIPT_PROVIDER_URL = os.getenv("RECEIPT_PROVIDER_URL")
    RECEIPT_PROVIDER_API_KEY = os.getenv("RECEIPT_PROVIDER_API_KEY")
    RECEIPT_PROVIDER_TIMEOUT_SECONDS = float(os.getenv("RECEIPT_PROVIDER_TIMEOUT_SECONDS", "10"))
    REDIS_CONNECT_TIMEOUT_SECONDS = float(os.getenv("REDIS_CONNECT_TIMEOUT_SECONDS", "3"))
    REDIS_SOCKET_TIMEOUT_SECONDS = float(os.getenv("REDIS_SOCKET_TIMEOUT_SECONDS", "3"))
    READINESS_DB_TIMEOUT_MS = int(os.getenv("READINESS_DB_TIMEOUT_MS", "3000"))


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite+pysqlite:///:memory:")
    JWT_SECRET_KEY = "testing-only-secret-that-is-at-least-32-bytes"
    RATELIMIT_STORAGE_URI = "memory://"
    RATELIMIT_ENABLED = False
    CELERY = {**BaseConfig.CELERY, "task_always_eager": True, "task_eager_propagates": True}


class ProductionConfig(BaseConfig):
    DEBUG = False
    TESTING = False


CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name: str | None = None) -> type[BaseConfig]:
    environment = name if name is not None else os.environ.get("APP_ENV", "development")
    try:
        return CONFIGS[environment]
    except KeyError as error:
        supported = ", ".join(sorted(CONFIGS))
        message = f"Unknown APP_ENV '{environment}'. Expected one of: {supported}"
        raise RuntimeError(message) from error
