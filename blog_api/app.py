from blog_api.models import db
from blog_api.views import blueprints
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException, default_exceptions


def create_json_app(settings=None):
    if settings is None:
        settings = {
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///blog.db'
        }
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings['SQLALCHEMY_DATABASE_URI']

    # При всех возможных исключениях выдавать json-ответ
    def default_json_error(exc):
        resp = jsonify({'message': str(exc)})
        resp.status_code = (exc.code
                            if isinstance(exc, HTTPException) else 500)
        return resp

    for code in default_exceptions:
        app.register_error_handler(code, default_json_error)

    # Регистрация компонент приложения
    for bp in blueprints:
        app.register_blueprint(bp)
        bp.app = app

    # Инициализация БД и разворот схемы
    db.init_app(app)
    db.create_all(app=app)

    return app


if __name__ == '__main__':
    app = create_json_app()
    app.run()
