from flask import Flask
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from redis import Redis
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class RedisClient:
    def init_app(self, app: Flask) -> None:
        client = Redis.from_url(app.config["REDIS_URL"], decode_responses=True)
        app.extensions["redis"] = client

    def get(self, app: Flask) -> Redis:
        return app.extensions["redis"]


db = SQLAlchemy(model_class=Base)
migrate = Migrate(compare_type=True)
redis_client = RedisClient()
jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address)
