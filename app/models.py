#!/usr/bin/python
# -*- UTF-8 -*-

from . import db
import datetime
from flask.ext.login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password_hash = db.Column(db.String(128))
    email = db.Column(db.String(120), unique=True)
    stories = db.relationship('Story', backref='user', lazy='joined')
    instances = db.relationship('InstanceStory', backref='user', lazy='dynamic')
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))

    def __init__(self, username, email):
        self.username = username
        self.email = email
        if self.role is None:
            if self.email == current_app.config['STORY_HERO_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()

    def __repr__(self):
        return '<User %r>' % self.username

    def can(self, permissions):
        return self.role is not None and (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

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
    instances = db.relationship('InstanceStory', backref='story', lazy='dynamic')

    def __init__(self, name, user_id):
        self.name = name
        self.user_id = user_id
        self.timestamp = datetime.datetime.now()

    def __repr__(self):
        return '<Story %r (%r)>' % (self.name, self.user_id)


class InstanceStory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    current_step_id = db.Column(db.Integer, db.ForeignKey('step.id'))
    finished = db.Column(db.Boolean)
    started = db.Column(db.DateTime)
    finished_timestamp = db.Column(db.DateTime)
    history = db.relationship('HistoryInstance', backref='instance', lazy='dynamic')

    def __init__(self, story_id, user_id, current_step_id):
        self.story_id = story_id
        self.user_id = user_id
        self.current_step_id = current_step_id
        self.started = datetime.datetime.now()
        self.finished = False

    def __repr__(self):
        return '<InstanceStory %r %r %r>' % (self.story_id, self.user_id, self.current_step_id)

class HistoryInstance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    instance_id = db.Column(db.Integer, db.ForeignKey('instance_story.id'))
    from_step_id = db.Column(db.Integer, db.ForeignKey('step.id'))
    to_step_id = db.Column(db.Integer, db.ForeignKey('step.id'))
    choice_text = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime)

    def __init__(self, instance_id, from_step_id, to_step_id, choice_text):
        self.instance_id = instance_id
        self.from_step_id = from_step_id
        self.to_step_id = to_step_id
        self.choice_text = choice_text
        self.timestamp = datetime.datetime.now()

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name

    @staticmethod
    def insert_roles():
        roles = {
            'User': (Permission.PLAY_STORY, True),
            'Writer': (Permission.PLAY_STORY | Permission.CREATE_STORY, False),
            'Administrator': (0xFF, False)
        }

        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

class Permission(object):
    PLAY_STORY = 0x01
    CREATE_STORY = 0x02
    ADMINISTER = 0x80
