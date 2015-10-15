#!/usr/bin/python
# -*- UTF-8 -*-

from flask_wtf import Form
from wtforms import TextAreaField, StringField, PasswordField, SelectField, validators, ValidationError
from wtforms.validators import DataRequired

class BulkAddStepForm(Form):
    steps = TextAreaField('Steps', validators = [DataRequired()])
