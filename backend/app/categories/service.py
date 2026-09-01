import uuid

from sqlalchemy.exc import IntegrityError

from app.api.errors import ApiError
from app.extensions import db
from app.models import Category, User
from app.repositories.categories import CategoryRepository


class CategoryService:
    def __init__(self) -> None:
        self.categories = CategoryRepository()

    def list(self, user: User) -> list[Category]:
        return self.categories.list_visible(user.id)

    def get(self, public_id: uuid.UUID, user: User) -> Category:
        category = self.categories.find_visible(public_id, user.id)
        if category is None:
            raise ApiError("CATEGORY_NOT_FOUND", "Категория не найдена", 404)
        return category

    def create(self, name: str, user: User) -> Category:
        self._ensure_unique_name(name, user.id)
        category = Category(name=name, normalized_name=name.casefold(), user_id=user.id)
        self.categories.add(category)
        try:
            db.session.commit()
        except IntegrityError as error:
            db.session.rollback()
            raise ApiError("CATEGORY_ALREADY_EXISTS", "Категория уже существует", 409) from error
        return category

    def update(self, public_id: uuid.UUID, name: str, user: User) -> Category:
        category = self.get(public_id, user)
        self._ensure_mutable(category, user)
        duplicate = self.categories.find_by_name(name, user.id)
        if duplicate is not None and duplicate.id != category.id:
            raise ApiError("CATEGORY_ALREADY_EXISTS", "Категория уже существует", 409)
        category.name = name
        category.normalized_name = name.casefold()
        db.session.commit()
        return category

    def delete(self, public_id: uuid.UUID, user: User) -> None:
        category = self.get(public_id, user)
        self._ensure_mutable(category, user)
        if self.categories.has_expenses(category.id):
            raise ApiError("CATEGORY_IN_USE", "Категория используется в расходах", 409)
        if self.categories.has_budgets(category.id):
            raise ApiError("CATEGORY_IN_USE", "Категория используется в бюджетах", 409)
        db.session.delete(category)
        db.session.commit()

    def _ensure_unique_name(self, name: str, user_id: int) -> None:
        if self.categories.find_by_name(name, user_id) is not None:
            raise ApiError("CATEGORY_ALREADY_EXISTS", "Категория уже существует", 409)

    @staticmethod
    def _ensure_mutable(category: Category, user: User) -> None:
        if category.is_system:
            raise ApiError(
                "SYSTEM_CATEGORY_IMMUTABLE", "Системную категорию нельзя изменить или удалить", 403
            )
        if category.user_id != user.id:
            raise ApiError("CATEGORY_NOT_FOUND", "Категория не найдена", 404)
