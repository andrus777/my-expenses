from app.api.errors import ApiError


def parse_category_payload(payload: object) -> str:
    if not isinstance(payload, dict):
        raise ApiError("VALIDATION_ERROR", "Некорректное тело запроса", 400)
    name = payload.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ApiError("VALIDATION_ERROR", "Ошибка валидации", 400, {"name": ["Укажите название"]})
    name = name.strip()
    if len(name) > 100:
        raise ApiError(
            "VALIDATION_ERROR",
            "Ошибка валидации",
            400,
            {"name": ["Максимальная длина: 100"]},
        )
    return name
