from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.analytics.service import StatisticsService
from app.auth.service import AuthService
from app.schemas.statistics import parse_currency, parse_interval, parse_period

blueprint = Blueprint("statistics", __name__, url_prefix="/statistics")


def _user():  # type: ignore[no-untyped-def]
    return AuthService().get_user(get_jwt_identity())


@blueprint.get("/summary")
@jwt_required()
def summary():  # type: ignore[no-untyped-def]
    return jsonify(StatisticsService().summary(_user(), parse_period(), parse_currency()))


@blueprint.get("/categories")
@jwt_required()
def categories():  # type: ignore[no-untyped-def]
    return jsonify(StatisticsService().categories(_user(), parse_period(), parse_currency()))


@blueprint.get("/timeline")
@jwt_required()
def timeline():  # type: ignore[no-untyped-def]
    period = parse_period()
    return jsonify(
        StatisticsService().timeline(_user(), period, parse_interval(period), parse_currency())
    )


@blueprint.get("/subscriptions")
@jwt_required()
def subscriptions():  # type: ignore[no-untyped-def]
    return jsonify(StatisticsService().subscriptions(_user(), parse_currency()))
