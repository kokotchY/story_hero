#!/usr/bin/python

from flask import Flask, render_template, session, make_response, request
from flask.ext.sqlalchemy import SQLAlchemy
from flask_debugtoolbar import DebugToolbarExtension
from flask.ext.session import Session
from flask.ext.login import LoginManager
import os

db = SQLAlchemy()
toolbar = DebugToolbarExtension()
session = Session()
login_manager = LoginManager()
login_manager.login_view = "login"

the_app = None

def create_app():
    global the_app
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/flask/test.db'
    app.config['DEBUG'] = True
    app.config['SECRET_KEY'] = 'asfd'
    app.config['SQLALCHEMY_ECHO'] = False
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_USE_SIGNER'] = True
    toolbar.init_app(app)
    session.init_app(app)
    login_manager.init_app(app)

    db.init_app(app)
    the_app = app
    from . import views
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    if app.debug:
        app.jinja_env.exception_formatter = format_exception

    @app.url_defaults
    def hashed_url_for_static_file(endpoint, values):
        if 'static' == endpoint or endpoint.endswith('.static'):
            filename = values.get('filename')
            if filename:
                if '.' in endpoint:
                    blueprint = endpoint.rsplit('.', 1)[0]
                else:
                    blueprint = request.blueprint

                if blueprint:
                    static_folder = the_app.blueprints[blueprint].static_folder
                else:
                    static_folder = the_app.static_folder

                param_name = 'h'
                while param_name in values:
                    param_name = '_' + param_name
                values[param_name] = static_file_hash(os.path.join(static_folder, filename))
    return app

def format_exception(tb):
    res = make_response(tb.render_as_text())
    res.content_type = 'text/plain'
    return res


def static_file_hash(filename):
    return int(os.stat(filename).st_mtime)
