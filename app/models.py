#!/usr/bin/python
# -*- UTF-8 -*-

from . import db
import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)
    stories = db.relationship('Story', backref='user', lazy='joined')

    def __init__(self, username, email):
        self.username = username
        self.email = email

    def __repr__(self):
        return '<User %r>' % self.username

class Step(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'))
    name = db.Column(db.String(50))
    content = db.Column(db.Text)
    first_choice = db.Column(db.String(50))
    first_choice_step_id = db.Column(db.Integer, db.ForeignKey('step.id'), nullable=True)
    first_choice_step = db.relationship('Step', uselist=False, remote_side=[id], foreign_keys=[first_choice_step_id])
    second_choice = db.Column(db.String(50))
    second_choice_step_id = db.Column(db.Integer, db.ForeignKey('step.id'), nullable=True)
    second_choice_step = db.relationship('Step', uselist=False, remote_side=[id], foreign_keys=[second_choice_step_id])
    final = db.Column(db.Boolean)

    def __init__(self, name, content, story_id):
        self.name = name
        self.content = content
        self.story_id = story_id

    def __repr__(self):
        return '<Step %r,%r,%r>' % (self.name, self.first_choice_step_id, self.second_choice_step_id)

class Story(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime)
    steps = db.relationship('Step', backref='story', lazy='joined', foreign_keys=[Step.story_id])
    initial_step_id = db.Column(db.Integer, db.ForeignKey('step.id'))

    def __init__(self, name, user_id):
        self.name = name
        self.user_id = user_id
        self.timestamp = datetime.datetime.now()

    def __repr__(self):
        return '<Story %r (%r)>' % (self.name, self.user_id)

