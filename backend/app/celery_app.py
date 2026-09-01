from celery import Celery, Task
from flask import Flask

celery = Celery("my_expenses")


def init_celery(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = FlaskTask
    celery.config_from_object(app.config["CELERY"])
    celery.autodiscover_tasks(["app.receipts"])
    celery.set_default()
    app.extensions["celery"] = celery
    return celery
