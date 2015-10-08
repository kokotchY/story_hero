#!/usr/bin/bash

from flask.ext.script import Manager, Shell
from flask.ext.migrate import Migrate, MigrateCommand
from flask import url_for
from app import create_app, db
from app.models import User, Story, Role

app = create_app()
manager = Manager(app)
migrate = Migrate(app, db)

def make_shell_context():
    return dict(app=app, db=db, User=User,Story=Story, Role=Role)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command("db", MigrateCommand)

@manager.command
def init():
    'Define some defaults for the database'
    user = User('kokotchy', 'address@host.com')
    user.password = 'pass'
    db.session.add(user)
    db.session.commit()
    story = Story('This is a story', user.id)
    db.session.add(story)
    db.session.commit()
    Role.insert_roles()

@manager.command
def list_routes():
    "List all available routes"
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
