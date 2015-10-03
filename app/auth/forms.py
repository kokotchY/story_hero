#!/usr/bin/python
# -*- UTF-8 -*-

from flask_wtf import Form
from wtforms import StringField, PasswordField, BooleanField, validators, ValidationError
from wtforms.validators import DataRequired
from ..models import User

class LoginForm(Form):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me?')

class RegisterForm(Form):
    username = StringField('Username', validators=[DataRequired(), validators.Length(5)])
    password = PasswordField('Password', validators=[DataRequired(), validators.EqualTo('confirm', message="Password must match")])
    confirm = PasswordField('Password', validators=[DataRequired()])
    email = StringField('Email', validators=[validators.Email('Invalid email address.')])

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')
