from flask import Blueprint

from app.api.v1.auth import blueprint as auth_blueprint
from app.api.v1.users import blueprint as users_blueprint

api_v1_blueprint = Blueprint("api_v1", __name__, url_prefix="/api/v1")
api_v1_blueprint.register_blueprint(auth_blueprint)
api_v1_blueprint.register_blueprint(users_blueprint)

__all__ = ["api_v1_blueprint"]
