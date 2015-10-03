#!/usr/bin/python

from flask import Flask, render_template, session
from flask.ext.sqlalchemy import SQLAlchemy
from flask_debugtoolbar import DebugToolbarExtension
from flask.ext.session import Session
from flask.ext.login import LoginManager

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
    return app
