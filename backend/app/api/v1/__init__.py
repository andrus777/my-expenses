from flask import Blueprint

from app.api.v1.auth import blueprint as auth_blueprint
from app.api.v1.budgets import blueprint as budgets_blueprint
from app.api.v1.categories import blueprint as categories_blueprint
from app.api.v1.expenses import blueprint as expenses_blueprint
from app.api.v1.receipts import blueprint as receipts_blueprint
from app.api.v1.statistics import blueprint as statistics_blueprint
from app.api.v1.subscriptions import blueprint as subscriptions_blueprint
from app.api.v1.users import blueprint as users_blueprint

api_v1_blueprint = Blueprint("api_v1", __name__, url_prefix="/api/v1")
api_v1_blueprint.register_blueprint(auth_blueprint)
api_v1_blueprint.register_blueprint(budgets_blueprint)
api_v1_blueprint.register_blueprint(categories_blueprint)
api_v1_blueprint.register_blueprint(expenses_blueprint)
api_v1_blueprint.register_blueprint(receipts_blueprint)
api_v1_blueprint.register_blueprint(statistics_blueprint)
api_v1_blueprint.register_blueprint(subscriptions_blueprint)
api_v1_blueprint.register_blueprint(users_blueprint)

__all__ = ["api_v1_blueprint"]
