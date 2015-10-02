#!/usr/bin/python

from flask import Flask, render_template
from flask.ext.sqlalchemy import SQLAlchemy
from flask_debugtoolbar import DebugToolbarExtension

db = SQLAlchemy()
toolbar = DebugToolbarExtension()

the_app = None

def create_app():
    global the_app
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/flask/test.db'
    app.config['DEBUG'] = True
    app.config['SECRET_KEY'] = 'asfd'
    app.config['SQLALCHEMY_ECHO'] = False
    toolbar.init_app(app)

    db.init_app(app)
    the_app = app
    from . import views
    return app
