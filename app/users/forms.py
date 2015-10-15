#!/usr/bin/python
# -*- UTF-8 -*-

from flask_wtf import Form
from wtforms import StringField, PasswordField, SelectField, validators, ValidationError
from wtforms.validators import DataRequired

class EditUserForm(Form):
    username = StringField('Username', validators = [DataRequired()])
    password = PasswordField('Password', validators=[validators.EqualTo('confirm', message="Password must match")])
    confirm = PasswordField('Password')
    email = StringField('Email', validators=[validators.Email('Invalid email address.')])
    role_id = SelectField('Role', coerce=int)

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')
