#!/usr/bin/python
# -*- UTF-8 -*-

from . import the_app as app
from . import db
from .models import User, Story, Step, InstanceStory, HistoryInstance
from flask import render_template, request, redirect, url_for, flash, session, Response, abort, Markup
import markdown
import datetime
from graphviz import Digraph
from flask.ext.login import login_required

@app.route('/users/add', methods=['GET', 'POST'])
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
    user = User.query.filter_by(id=user_id).first()
    return render_template('users/show.html', user = user)

@app.route('/users')
def list_users():
    users = User.query.all()
    return render_template('users.html', users = users)


@app.route('/users/delete/<int:user_id>')
def delete_user(user_id):
    user = User.query.filter_by(id = user_id).first()
    if user:
        message = 'User %r deleted' % user
        db.session.delete(user)
        db.session.commit()
        flash(message)
    else:
        flash('User %i does not exists' % user_id)
    return redirect(url_for('list_users'))

@app.route('/stories/<int:user_id>')
def display_stories(user_id):
    stories = Story.query.filter_by(user_id = user_id).all()
    user = User.query.filter_by(id = user_id).first()
    return render_template('stories/list.html', stories = stories, user = user)

@app.route('/stories/<int:user_id>/new', methods=['GET', 'POST'])
def new_story(user_id):
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
                instance.current_step_id = step.second_choice_step_id
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
def instances():
    instances = InstanceStory.query.filter_by(user_id = session['user_id']).all()
    return render_template('instances.html', instances = instances)

@app.route('/instances/<int:instance_id>/delete')
def delete_instance(instance_id):
    instance = InstanceStory.query.get_or_404(instance_id)
    db.session.delete(instance)
    db.session.commit()
    return redirect(url_for('instances'))

@app.route('/story/<int:story_id>.dot')
def generate_dot(story_id):
    print(request.url_rule)
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
    print(request.url_rule)
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
