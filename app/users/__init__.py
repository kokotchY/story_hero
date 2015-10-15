#!/usr/bin/python
# -*- UTF-8 -*-
from flask import Blueprint

users = Blueprint('users', __name__)

#from . import forms
from . import views
