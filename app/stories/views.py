#!/usr/bin/python
# -*- UTF-8 -*-

from . import stories
from ..decorators import permission_required
from ..models import Permission, Story, Step, User, InstanceStory, HistoryInstance
from .forms import BulkAddStepForm
from .. import db
from flask import request, redirect, url_for, render_template, Response, session, Markup
from flask.ext.login import current_user
from graphviz import Digraph
import markdown
import datetime

@stories.route('/<int:story_id>/bulk_add_step', methods = ['GET', 'POST'])
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
        return redirect(url_for('stories.show_story', story_id = story_id))
    return render_template('stories/bulk_add_step.html', story_id = story_id, form = form)

@stories.route('/<int:user_id>')
def show(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('stories/list.html', stories = user.stories, user = user)

@stories.route('/<int:user_id>/new', methods=['GET', 'POST'])
@stories.route('/new', methods=['GET', 'POST'])
@permission_required(Permission.CREATE_STORY)
def new(user_id = None):
    if user_id is None:
        user_id = current_user.id
    if request.method == "POST":
        name = request.form['name']
        story = Story(name, user_id)
        db.session.add(story)
        db.session.commit()
        return redirect(url_for('stories.show_story', story_id = story.id))
    return render_template("stories/new.html", user_id = user_id)

@stories.route('/show/<int:story_id>')
def show_story(story_id):
    story = Story.query.get_or_404(story_id)
    if story.initial_step_id:
        initial_step = Step.query.get(story.initial_step_id)
    else:
        initial_step = None
    return render_template('stories/show.html', story = story, initial_step = initial_step)

@stories.route('/<int:story_id>/new_initial_step', methods = ['GET', 'POST'])
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
        return redirect(url_for('stories.show_story', story_id = story_id))
    return render_template('stories/new_step.html', story_id = story_id, initial = True, steps = [])

@stories.route('/<int:story_id>/new_step', methods = ['GET', 'POST'])
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
        return redirect(url_for('main.show_step', step_id = step.id))
    return render_template('stories/new_step.html', story_id = story_id, initial = False, steps = steps)

@stories.route('/<int:story_id>/start')
def start_story(story_id):
    story = Story.query.get_or_404(story_id)
    instance = InstanceStory(story.id, session['user_id'], story.initial_step_id)
    db.session.add(instance)
    db.session.commit()
    history = HistoryInstance(instance.id, None, story.initial_step_id, None)
    db.session.add(history)
    db.session.commit()
    return redirect(url_for('stories.show_instance', instance_id = instance.id))

@stories.route('/<int:instance_id>/play')
@stories.route('/<int:instance_id>/play/<int:choice>')
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

@stories.route('/')
def list():
    stories = Story.query.all()
    return render_template('stories/all.html', stories = stories)

@stories.route('/schema-<int:story_id>.dot')
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

@stories.route('/schema-<int:story_id>.png')
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
