from dataclasses import dataclass

from email_validator import EmailNotValidError, validate_email

from app.api.errors import ApiError


@dataclass(frozen=True)
class Credentials:
    email: str
    password: str


def parse_credentials(payload: object, *, validate_password_length: bool) -> Credentials:
    if not isinstance(payload, dict):
        raise ApiError("VALIDATION_ERROR", "Некорректное тело запроса", 400)

    email = payload.get("email")
    password = payload.get("password")
    details: dict[str, list[str]] = {}

    if not isinstance(email, str):
        details["email"] = ["Укажите email"]
    else:
        try:
            email = validate_email(email.strip(), check_deliverability=False).normalized.lower()
        except EmailNotValidError:
            details["email"] = ["Некорректный email"]

    if not isinstance(password, str):
        details["password"] = ["Укажите пароль"]
    elif validate_password_length and len(password) < 8:
        details["password"] = ["Пароль должен содержать не менее 8 символов"]

    if details:
        raise ApiError("VALIDATION_ERROR", "Ошибка валидации", 400, details)

    return Credentials(email=email, password=password)
