import os

from flask import Flask, render_template

from reader_app.db import get_db


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'reader_app.sqlite')
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # @app.route('/hello')
    # def hello():
    #     return 'Hello, World!'

    @app.route('/')
    def index():
        db = get_db()
        languages = db.execute('SELECT id, name FROM language').fetchall()
        return render_template('index.html', languages=languages)

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import language
    app.register_blueprint(language.bp)

    from . import collection
    app.register_blueprint(collection.bp)

    from . import text
    app.register_blueprint(text.bp)

    return app
