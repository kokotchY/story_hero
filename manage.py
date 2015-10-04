#!/usr/bin/bash

from flask.ext.script import Manager, Shell
from flask.ext.migrate import Migrate, MigrateCommand
from flask import url_for
from app import create_app, db
from app.models import User, Story

app = create_app()
manager = Manager(app)
migrate = Migrate(app, db)

def make_shell_context():
    return dict(app=app, db=db)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command("db", MigrateCommand)

@manager.command
def init():
    user = User('kokotchy', 'address@host.com')
    db.session.add(user)
    db.session.commit()
    story = Story('This is a story', user.id)
    db.session.add(story)
    db.session.commit()

@manager.command
def list_routes():
    import urllib
    output = []
    for rule in app.url_map.iter_rules():
        options = {}
        for arg in rule.arguments:
            options[arg] = "[{0}]".format(arg)
        methods = ','.join(rule.methods)
        url = url_for(rule.endpoint, **options)
        line = urllib.unquote("{:50s} {:20s} {}".format(rule.endpoint, methods, url))
        output.append(line)
    for line in sorted(output):
        print(line)

if __name__ == "__main__":
    manager.run()
