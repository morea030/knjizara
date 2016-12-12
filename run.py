# server startujemo python run.py  runserver
import os
from app import create_app, db
from app.models import User, Post, Knjige, Source, Role, Comment
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager =Manager(app)
migrate = Migrate(app, db)

def make_shell_context():
    return dict(app=app, db=db, User=User, Post=Post, Knjige=Knjige, Source=Source, Role=Role, Comment=Comment)
manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)
#manager.add_command(('migrate'))

@manager.command
def test():
    """Run the unit test"""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

if __name__=='__main__':
    manager.run()
