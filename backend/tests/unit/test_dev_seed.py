from app.dev_seed import seed_demo_data
from app.extensions import db
from app.models import Budget, Expense, Subscription


def test_demo_seed_is_complete_and_idempotent(app):
    with app.app_context():
        user, created = seed_demo_data("portfolio@example.com", "portfolio-password")
        same_user, created_again = seed_demo_data("portfolio@example.com", "different-password")

        assert created is True
        assert created_again is False
        assert same_user.id == user.id
        assert (
            db.session.scalar(
                db.select(db.func.count(Expense.id)).where(Expense.user_id == user.id)
            )
            == 40
        )
        assert (
            db.session.scalar(
                db.select(db.func.count(Subscription.id)).where(Subscription.user_id == user.id)
            )
            == 3
        )
        assert (
            db.session.scalar(db.select(db.func.count(Budget.id)).where(Budget.user_id == user.id))
            == 3
        )
