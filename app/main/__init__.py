#!/usr/bin/python
# -*- UTF-8 -*-
from flask import Blueprint

main = Blueprint('main', __name__)

from . import forms
from . import views
