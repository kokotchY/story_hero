#!/usr/bin/python
# -*- UTF-8 -*-

from . import stories
from ..decorators import permission_required
from ..models import Permission, Story, Step, User, InstanceStory, HistoryInstance
from .forms import BulkAddStepForm
from .. import db
from flask import request, redirect, url_for, render_template, Response, session, Markup, flash
from flask.ext.login import current_user, login_required
from graphviz import Digraph
import markdown
import datetime

@stories.route('/<int:story_id>/bulk_add_step', methods = ['GET', 'POST'])
@login_required
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
@login_required
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
@login_required
def show_story(story_id):
    story = Story.query.get_or_404(story_id)
    if story.initial_step_id:
        initial_step = Step.query.get(story.initial_step_id)
    else:
        initial_step = None
    return render_template('stories/show.html', story = story, initial_step = initial_step)

@stories.route('/<int:story_id>/new_step', methods = ['GET', 'POST'])
@login_required
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
        return redirect(url_for('stories.show_step', step_id = step.id))
    return render_template('stories/new_step.html', story_id = story_id, steps = steps)

@stories.route('/<int:story_id>/start')
@login_required
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
@login_required
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
@login_required
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
@login_required
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

@stories.route('/<int:story_id>/set_init/<int:step_id>')
@login_required
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

@stories.route('/<int:story_id>/remove_init/<int:step_id>')
@login_required
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


@stories.route('/step/<int:step_id>')
@login_required
def show_step(step_id):
    step = Step.query.get_or_404(step_id)
    story = Story.query.get_or_404(step.story_id)
    return render_template('steps/show.html', step = step, story = story)

@stories.route('/step/<int:step_id>/edit', methods = ['GET', 'POST'])
@login_required
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
        return redirect(url_for('stories.show_step', step_id = step.id))
    return render_template('steps/edit.html', story_id = step.story_id, inital = False, steps = steps, step = step)

@stories.route('/steps')
@login_required
def list_steps():
    steps = Step.query.all()
    return render_template('steps/list.html', steps = steps)

@stories.route('/step/<int:step_id>/delete')
@login_required
@permission_required(Permission.CREATE_STORY)
def delete_step(step_id):
    step = Step.query.get_or_404(step_id)
    if step.story.user_id == current_user.id:
        story_id = step.story_id
        db.session.delete(step)
        db.session.commit()
        flash('The step have been deleted')
        return redirect(url_for('stories.show_story', story_id = story_id))
    else:
        flash('The step is not part of one of your story')
        return redirect(url_for('main.index'))

@stories.route('/instances')
@login_required
def instances():
    instances = InstanceStory.query.filter_by(user_id = session['user_id']).all()
    return render_template('instances.html', instances = instances, HistoryInstance = HistoryInstance)

@stories.route('/instances/<int:instance_id>/delete')
@login_required
def delete_instance(instance_id):
    instance = InstanceStory.query.get_or_404(instance_id)
    db.session.delete(instance)
    db.session.commit()
    return redirect(url_for('stories.instances'))

@stories.route('/instance/<int:instance_id>/history')
@login_required
def display_history(instance_id):
    instance = InstanceStory.query.get_or_404(instance_id)
    return render_template('instance_history.html', instance = instance)

@stories.route('/instance/history-<int:instance_id>.png')
@login_required
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

@stories.route('/my_stories')
@login_required
@permission_required(Permission.CREATE_STORY)
def user_stories():
    stories = current_user.stories
    return render_template('stories/user.html', stories = stories, user = current_user)
