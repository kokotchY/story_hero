#!/usr/bin/python
# -*- UTF-8 -*-
from flask import Blueprint

stories = Blueprint('stories', __name__)

#from . import forms
from . import views
