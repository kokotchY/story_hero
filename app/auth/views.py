#!/usr/bin/python
# -*- UTF-8 -*-

from flask import render_template, redirect, url_for, flash, request, current_app
from . import auth
from .forms import LoginForm
from ..models import User
from .. import login_manager
from flask.ext.login import login_required, login_user, logout_user

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username = form.username.data).first()
        if user and user.verify_password(form.password.data):
            login_user(user, remember = form.remember_me.data)

            flash('Logged in successfully.')

            next = request.args.get('next')

            return redirect(next or url_for('index'))
        else:
            flash('Unknown user or password')
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@auth.route('/login/<user>')
def login_username(user):
    if current_app.debug:
        user_db = User.query.filter_by(username=user).first()
        if user_db:
            login_user(user_db) 
            return redirect(url_for('index'))

