#!/usr/bin/python
# -*- UTF-8 -*-

from . import main
from .. import db
from ..models import User

from flask import render_template, request, abort, current_app
from flask.ext.login import login_required
from flask.ext.sqlalchemy import get_debug_queries

@main.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@main.route('/debug')
def debug():
    if app.debug:
        return render_template('debug.html', users = User.query.all(), urls = app.url_map)
    return abort(404)

@main.route('/shutdown', methods=['POST'])
def shutdown():
    assert app.debug == True
    shutdown_server()
    return 'Server shutting down...'

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@main.app_template_filter
def markdown_filter(content):
    return Markup(markdown.markdown(content))

@main.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['STORY_HERO_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                    'Slow query:%s\nParameters: %s\nDuration: %fs\nContext: %s\n' % (query.statement, query.parameters, query.duration, query.content))
    return response


@main.route('/')
def index():
    return render_template('index.html')
