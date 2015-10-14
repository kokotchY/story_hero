#!/usr/bin/python

from flask import Flask, render_template, make_response, request
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.session import Session
from flask.ext.login import LoginManager
import os
import sys

db = SQLAlchemy()
session = Session()

from .models import AnonymousUser, Permission

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.anonymous_user = AnonymousUser

def create_app(configname=None):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/flask/test.db'
    app.config['DEBUG'] = True
    app.config['SECRET_KEY'] = 'asfd'
    app.config['SQLALCHEMY_ECHO'] = False
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_USE_SIGNER'] = True
    if sys.version_info.major == 3 and app.config['SESSION_USE_SIGNER']:
        raise Exception('Impossible to activate the SESSION_SIGNER with python 3')
    app.config['STORY_HERO_ADMIN'] = 'kokotchy@gmail.com'
    app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
    app.config['STORY_HERO_SLOW_DB_QUERY_TIME'] = 0.5
    session.init_app(app)
    login_manager.init_app(app)
    db.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    #if app.debug:
        #app.jinja_env.exception_formatter = format_exception

    @app.url_defaults
    def hashed_url_for_static_file(endpoint, values):
        if 'static' == endpoint or endpoint.endswith('.static'):
            filename = values.get('filename')
            if filename:
                if '.' in endpoint:
                    blueprint = endpoint.rsplit('.', 1)[0]
                else:
                    blueprint = request.blueprint

                #if blueprint:
                    #print("From blueprint")
                    #static_folder = the_app.blueprints[blueprint].static_folder
                #else:
                    #static_folder = the_app.static_folder
                static_folder = app.static_folder

                param_name = 'h'
                while param_name in values:
                    param_name = '_' + param_name
                values[param_name] = static_file_hash(os.path.join(static_folder, filename))

    @app.context_processor
    def inject_permissions():
        return dict(Permission = Permission)
    return app

def format_exception(tb):
    res = make_response(tb.render_as_text())
    res.content_type = 'text/plain'
    return res


def static_file_hash(filename):
    return int(os.stat(filename).st_mtime)
