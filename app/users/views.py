#!/usr/bin/python

from . import users
from .forms import EditUserForm
from ..models import User, Role
from .. import db
from ..decorators import admin_required
from flask.ext.login import login_required
from flask import render_template, request, redirect, url_for, flash

@users.route('/<int:user_id>')
def show(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('users/show.html', user = user)

@users.route('/add', methods=['GET', 'POST'])
@admin_required
def add():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        user = User(username, email)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('users.show', user_id = user.id))
    return render_template('users/add.html')

@users.route('/<int:user_id>/edit', methods = ['GET', 'POST'])
@login_required
@admin_required
def edit(user_id):
    user = User.query.get_or_404(user_id)
    form = EditUserForm(request.form, obj = user)
    roles = [(r.id, r.name) for r in Role.query.order_by('name')]
    form.role_id.choices = roles
    if request.method == "POST" and form.validate_on_submit:
        modification_detected = []
        if user.username != form.username.data:
            user.username = form.username.data
            modification_detected.append('username')
        if user.email != form.email.data:
            user.email = form.email.data
            modification_detected.append('email')
        if form.password.data is not None and not form.password.data == "" and form.password.data == form.confirm.data:
            user.password = form.password.data
            modification_detected.append('password')
        if user.role_id != form.role_id.data:
            user.role_id = form.role_id.data
            modification_detected.append('role')
        db.session.commit()
        if len(modification_detected) > 0:
            message = 'User %s have been updated:<ul>' % user.username
            for modif in modification_detected:
                message += "<li>%s</li>" % modif
            message += "</ul>"
            flash(message)
            return redirect(url_for('users.list'))
        else:
            flash('No modification have been detected for user %s' % user.username, "warning")
    return render_template('users/edit.html', user = user, form = form)

@users.route('/')
@admin_required
def list():
    users = User.query.all()
    return render_template('users.html', users = users)


@users.route('/<int:user_id>/delete')
def delete(user_id):
    user = User.query.get_or_404(user_id)
    message = 'User %r deleted' % user
    db.session.delete(user)
    db.session.commit()
    flash(message)
    return redirect(url_for('users.list'))
