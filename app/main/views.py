#!/usr/bin/python
# -*- UTF-8 -*-

from . import main
from .. import db
from ..decorators import admin_required, permission_required
from ..models import User, Story, Step, InstanceStory, HistoryInstance, Role, Permission

from flask import render_template, request, redirect, url_for, flash, session, Response, abort,  current_app
from flask.ext.login import login_required, current_user
from flask.ext.sqlalchemy import get_debug_queries
import datetime
from graphviz import Digraph

@main.route('/step/<int:step_id>')
def show_step(step_id):
    step = Step.query.get_or_404(step_id)
    story = Story.query.get_or_404(step.story_id)
    return render_template('steps/show.html', step = step, story = story)

@main.route('/step/<int:step_id>/edit', methods = ['GET', 'POST'])
def edit_step(step_id):
    step = Step.query.get_or_404(step_id)
    steps = Step.query.filter_by(story_id = step.story_id).all()
    if request.method == "POST":
        step.name = request.form['name']
        step.content = request.form['content']
        step.first_choice = request.form['first_choice_text']
        step.first_choice_step_id = request.form['first_choice']
        step.second_choice = request.form['second_choice_text']
        step.second_choice_step_id = request.form['second_choice']
        if "final_step" in request.form:
            step.final = request.form['final_step'] == "on"
        else:
            step.final = False
        db.session.commit()
        return redirect(url_for('.show_step', step_id = step.id))
    return render_template('steps/edit.html', story_id = step.story_id, inital = False, steps = steps, step = step)

@main.route('/steps')
def list_steps():
    steps = Step.query.all()
    return render_template('steps/list.html', steps = steps)

@main.route('/step/<int:step_id>/delete')
def delete_step(step_id):
    pass

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/instances')
@login_required
def instances():
    instances = InstanceStory.query.filter_by(user_id = session['user_id']).all()
    return render_template('instances.html', instances = instances, HistoryInstance = HistoryInstance)

@main.route('/instances/<int:instance_id>/delete')
def delete_instance(instance_id):
    instance = InstanceStory.query.get_or_404(instance_id)
    db.session.delete(instance)
    db.session.commit()
    return redirect(url_for('.instances'))

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

@main.route('/story/<int:story_id>/set_init/<int:step_id>')
def set_initial_step(story_id, step_id):
    story = Story.query.get_or_404(story_id)
    step = Step.query.get_or_404(step_id)
    if step.story_id == story.id:
        story.initial_step_id = step.id
        db.session.commit()
        flash('The initial step of the story %d have been changed.' % story.id, 'info')
    else:
        flash('The step %d is not a step of story %d' % (step.id, story.id), 'error')
    return redirect(url_for('stories.show_story', story_id = story.id))

@main.route('/story/<int:story_id>/remove_init/<int:step_id>')
def remove_initial_step(story_id, step_id):
    story = Story.query.get_or_404(story_id)
    step = Step.query.get_or_404(step_id)
    if step.story_id == story.id and story.initial_step_id == step.id:
        story.initial_step_id = None
        db.session.commit()
        flash('The initial step of the story %d have been removed.' % story.id, 'info')
    else:
        flash('The step %d is not a step of story %d or the initial step of story %d' % (step.id, story.id, story.id), 'error')
    return redirect(url_for('stories.show_story', story_id = story.id))

@main.route('/instance/<int:instance_id>/history')
def display_history(instance_id):
    instance = InstanceStory.query.get_or_404(instance_id)
    return render_template('instance_history.html', instance = instance)

@main.route('/instance/history-<int:instance_id>.png')
def display_history_png(instance_id):
    instance = InstanceStory.query.get_or_404(instance_id)
    histories = instance.history.order_by(HistoryInstance.timestamp.asc()).all()
    res = Response()
    g = Digraph(instance.story.name)
    step_ids = []
    for history in histories:
        if history.from_step_id and not history.from_step_id in step_ids:
            step_ids.append(history.from_step_id)
        if history.to_step_id and not history.to_step_id in step_ids:
            step_ids.append(history.to_step_id)

    steps_tmp = Step.query.filter(Step.id.in_(step_ids))
    steps = {}
    for step in steps_tmp:
        steps[step.id] = step

    for history in histories:
        if history.from_step_id and not history.from_step_id in steps:
            step = Step.query.get(history.from_step_id)
            steps[history.from_step_id] = step
        if history.to_step_id and not history.to_step_id in steps:
            step = Step.query.get(history.to_step_id)
            steps[history.to_step_id] = step
    for step_id in steps:
        step = steps[step_id]
        if step.final:
            g.node('step_%d' % step.id, label=step.name, color="lightblue2", style="filled")
        else:
            g.node('step_%d' % step.id, label=step.name)

    index = 1
    for history in histories:
        if history.from_step_id:
            g.edge('step_%d' % history.from_step_id, 'step_%d' % history.to_step_id, label = "%d. %s" % (index, history.choice_text))
            index += 1

    g.format = 'png'
    res.content_type = "image/png"
    res.data = g.pipe()
    return res

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
