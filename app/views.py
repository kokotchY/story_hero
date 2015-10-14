#!/usr/bin/python
# -*- UTF-8 -*-

from . import the_app as app
from . import db
from .models import User, Story, Step, InstanceStory, HistoryInstance, Role, Permission
from .forms import BulkAddStepForm, EditUserForm
from .decorators import admin_required, permission_required
from flask import render_template, request, redirect, url_for, flash, session, Response, abort, Markup, current_app
import markdown
import datetime
from graphviz import Digraph
from flask.ext.login import login_required, current_user
from flask.ext.sqlalchemy import get_debug_queries


@app.route('/users/add', methods=['GET', 'POST'])
@admin_required
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        user = User(username, email)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('show_user', user_id = user.id))
    return render_template('users/add.html')

@app.route('/users/<int:user_id>')
def show_user(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('users/show.html', user = user)

@app.route('/users')
@admin_required
def list_users():
    users = User.query.all()
    return render_template('users.html', users = users)


@app.route('/users/delete/<int:user_id>')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    message = 'User %r deleted' % user
    db.session.delete(user)
    db.session.commit()
    flash(message)
    return redirect(url_for('list_users'))

@app.route('/stories/<int:user_id>')
def display_stories(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('stories/list.html', stories = user.stories, user = user)

@app.route('/stories/<int:user_id>/new', methods=['GET', 'POST'])
@app.route('/stories/new', methods=['GET', 'POST'])
@permission_required(Permission.CREATE_STORY)
def new_story(user_id = None):
    if user_id is None:
        user_id = current_user.id
    if request.method == "POST":
        name = request.form['name']
        story = Story(name, user_id)
        db.session.add(story)
        db.session.commit()
        return redirect(url_for('show_story', story_id = story.id))
    return render_template("stories/new.html", user_id = user_id)

@app.route('/stories/show/<int:story_id>')
def show_story(story_id):
    story = Story.query.get_or_404(story_id)
    if story.initial_step_id:
        initial_step = Step.query.get(story.initial_step_id)
    else:
        initial_step = None
    return render_template('stories/show.html', story = story, initial_step = initial_step)

@app.route('/stories/<int:story_id>/new_initial_step', methods = ['GET', 'POST'])
def new_initial_step(story_id):
    story = Story.query.get_or_404(story_id)
    if request.method == 'POST':
        name = request.form['name']
        content = request.form['content']
        step = Step(name, content, story_id)
        db.session.add(step)
        db.session.commit()
        story.initial_step_id = step.id
        db.session.commit()
        print("New step %r created" % step)
        return redirect(url_for('show_story', story_id = story_id))
    return render_template('stories/new_step.html', story_id = story_id, initial = True, steps = [])

@app.route('/stories/<int:story_id>/new_step', methods = ['GET', 'POST'])
def new_step(story_id):
    steps = Step.query.filter_by(story_id = story_id).all()
    if request.method == "POST":
        step = Step(request.form['name'], request.form['content'], story_id)
        step.first_choice = request.form['first_choice_text']
        step.first_choice_step_id = request.form['first_choice']
        step.second_choice = request.form['second_choice_text']
        step.second_choice_step_id = request.form['second_choice']
        if "final_step" in request.form:
            step.final = request.form['final_step'] == "on"
        else:
            step.final = False
        db.session.add(step)
        db.session.commit()
        return redirect(url_for('show_step', step_id = step.id))
    return render_template('stories/new_step.html', story_id = story_id, initial = False, steps = steps)

@app.route('/step/<int:step_id>')
def show_step(step_id):
    step = Step.query.get_or_404(step_id)
    story = Story.query.get_or_404(step.story_id)
    return render_template('steps/show.html', step = step, story = story)

@app.route('/step/<int:step_id>/edit', methods = ['GET', 'POST'])
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
        return redirect(url_for('show_step', step_id = step.id))
    return render_template('steps/edit.html', story_id = step.story_id, inital = False, steps = steps, step = step)

@app.route('/steps')
def list_steps():
    steps = Step.query.all()
    return render_template('steps/list.html', steps = steps)

@app.route('/step/<int:step_id>/delete')
def delete_step(step_id):
    pass

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stories/<int:story_id>/start')
def start_story(story_id):
    story = Story.query.get_or_404(story_id)
    instance = InstanceStory(story.id, session['user_id'], story.initial_step_id)
    db.session.add(instance)
    db.session.commit()
    history = HistoryInstance(instance.id, None, story.initial_step_id, None)
    db.session.add(history)
    db.session.commit()
    return redirect(url_for('show_instance', instance_id = instance.id))

@app.route('/stories/<int:instance_id>/play')
@app.route('/stories/<int:instance_id>/play/<int:choice>')
def show_instance(instance_id, choice = None):
    instance = InstanceStory.query.get_or_404(instance_id)
    if 'user_id' in session and instance.user_id == int(session['user_id']):
        step = Step.query.get_or_404(instance.current_step_id)
        if choice:
            if choice == 1:
                from_step_id = step.id
                choice_text = step.first_choice
                step = Step.query.get_or_404(step.first_choice_step_id)
                history = HistoryInstance(instance.id, from_step_id, step.id, choice_text)
                instance.current_step_id = step.id
                if step.final:
                    instance.finished_timestamp = datetime.datetime.now()
                    instance.finished = True
                db.session.add(history)
                db.session.commit()
            elif choice == 2:
                from_step_id = step.id
                choice_text = step.second_choice
                step = Step.query.get_or_404(step.second_choice_step_id)
                history = HistoryInstance(instance.id, from_step_id, step.id, choice_text)
                instance.current_step_id = step.id
                if step.final:
                    instance.finished_timestamp = datetime.datetime.now()
                    instance.finished = True
                db.session.add(history)
                db.session.commit()
        content = Markup(markdown.markdown(step.content))
        return render_template('/steps/play.html', content = content, story = instance.story, step = step, instance_id = instance_id)
    else:
        return 'This is not your story! %s != %s' % (str(type(instance.user_id)), str(type(session['user_id'])))

@app.route('/stories')
def stories():
    stories = Story.query.all()
    return render_template('stories/all.html', stories = stories)

@app.route('/instances')
@login_required
def instances():
    instances = InstanceStory.query.filter_by(user_id = session['user_id']).all()
    return render_template('instances.html', instances = instances, HistoryInstance = HistoryInstance)

@app.route('/instances/<int:instance_id>/delete')
def delete_instance(instance_id):
    instance = InstanceStory.query.get_or_404(instance_id)
    db.session.delete(instance)
    db.session.commit()
    return redirect(url_for('instances'))

@app.route('/story/<int:story_id>.dot')
def generate_dot(story_id):
    story = Story.query.get_or_404(story_id)
    res = Response()
    g = Digraph(story.name)
    for step in story.steps:
        if step.final:
            g.node('step_%d' % step.id, label=step.name, color="lightblue2", style="filled")
        else:
            g.node('step_%d' % step.id, label=step.name)
        if step.first_choice_step_id:
            g.edge('step_%d' % step.id, 'step_%d' % step.first_choice_step_id, label = step.first_choice)
        if step.second_choice_step_id:
            g.edge('step_%d' % step.id, 'step_%d' % step.second_choice_step_id, label = step.second_choice)
    if str(request.url_rule).endswith('dot'):
        res.content_type = "text/plain"
        res.data = g.source
    elif str(request.url_rule).endswith('png'):
        g.format = 'png'
        res.content_type = 'image/png'
        res.data = g.pipe()
    return res

@app.route('/story/<int:story_id>.png')
def generate_png(story_id):
    story = Story.query.get_or_404(story_id)
    res = Response()
    g = Digraph(story.name)
    for step in story.steps:
        if step.final:
            g.node('step_%d' % step.id, label=step.name, color="lightblue2", style="filled")
        else:
            g.node('step_%d' % step.id, label=step.name)
        if step.first_choice_step_id:
            g.edge('step_%d' % step.id, 'step_%d' % step.first_choice_step_id, label = step.first_choice)
        if step.second_choice_step_id:
            g.edge('step_%d' % step.id, 'step_%d' % step.second_choice_step_id, label = step.second_choice)
    if str(request.url_rule).endswith('dot'):
        res.content_type = "text/plain"
        res.data = g.source
    elif str(request.url_rule).endswith('png'):
        g.format = 'png'
        res.content_type = 'image/png'
        res.data = g.pipe()
    return res

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@app.route('/debug')
def debug():
    if app.debug:
        return render_template('debug.html', users = User.query.all(), urls = app.url_map)
    return abort(404)

@app.route('/shutdown', methods=['POST'])
def shutdown():
    assert app.debug == True
    shutdown_server()
    return 'Server shutting down...'

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/story/<int:story_id>/set_init/<int:step_id>')
def set_initial_step(story_id, step_id):
    story = Story.query.get_or_404(story_id)
    step = Step.query.get_or_404(step_id)
    if step.story_id == story.id:
        story.initial_step_id = step.id
        db.session.commit()
        flash('The initial step of the story %d have been changed.' % story.id, 'info')
    else:
        flash('The step %d is not a step of story %d' % (step.id, story.id), 'error')
    return redirect(url_for('show_story', story_id = story.id))

@app.route('/story/<int:story_id>/remove_init/<int:step_id>')
def remove_initial_step(story_id, step_id):
    story = Story.query.get_or_404(story_id)
    step = Step.query.get_or_404(step_id)
    if step.story_id == story.id and story.initial_step_id == step.id:
        story.initial_step_id = None
        db.session.commit()
        flash('The initial step of the story %d have been removed.' % story.id, 'info')
    else:
        flash('The step %d is not a step of story %d or the initial step of story %d' % (step.id, story.id, story.id), 'error')
    return redirect(url_for('show_story', story_id = story.id))

@app.route('/instance/<int:instance_id>/history')
def display_history(instance_id):
    instance = InstanceStory.query.get_or_404(instance_id)
    return render_template('instance_history.html', instance = instance)

@app.route('/instance/history-<int:instance_id>.png')
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

@app.route('/stories/<int:story_id>/bulk_add_step', methods = ['GET', 'POST'])
def add_bulk_steps(story_id):
    form = BulkAddStepForm()
    if form.validate_on_submit():
        content = form.steps.data
        for line in content.split("\n"):
            sep_pos = line.strip().find(':')
            step_name = line[:sep_pos]
            step_content = line[sep_pos+1:].strip()
            new_step = Step(step_name, step_content, story_id)
            db.session.add(new_step)
        db.session.commit()
        return redirect(url_for('show_story', story_id = story_id))
    return render_template('stories/bulk_add_step.html', story_id = story_id, form = form)

@app.template_filter('markdown')
def markdown_filter(content):
    return Markup(markdown.markdown(content))

@app.route('/users/<int:user_id>/edit', methods = ['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = EditUserForm(request.form, obj = user)
    roles = [(r.id, r.name) for r in Role.query.order_by('name')]
    form.role_id.choices = roles
    if request.method == "POST" and form.validate_on_submit:
        modification_detected = []
        if user.username != form.username.data:
            user.username = form.username.data
            modification_detected.append('username')
        if user.email != form.email.data:
            user.email = form.email.data
            modification_detected.append('email')
        if form.password.data is not None and not form.password.data == "" and form.password.data == form.confirm.data:
            user.password = form.password.data
            modification_detected.append('password')
        if user.role_id != form.role_id.data:
            user.role_id = form.role_id.data
            modification_detected.append('role')
        db.session.commit()
        if len(modification_detected) > 0:
            message = 'User %s have been updated:<ul>' % user.username
            for modif in modification_detected:
                message += "<li>%s</li>" % modif
            message += "</ul>"
            flash(message)
            return redirect(url_for('list_users'))
        else:
            flash('No modification have been detected for user %s' % user.username, "warning")
    return render_template('users/edit.html', user = user, form = form)

@app.after_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['STORY_HERO_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                    'Slow query:%s\nParameters: %s\nDuration: %fs\nContext: %s\n' % (query.statement, query.parameters, query.duration, query.content))
    return response
