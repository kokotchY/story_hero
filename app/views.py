#!/usr/bin/python
# -*- UTF-8 -*-

from . import the_app as app
from . import db
from .models import User, Story, Step
from flask import render_template, request, redirect, url_for, flash

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
