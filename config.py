import os
basedir = os.path.abspath(os.path.dirname(__file__))

# The Datbase file and the Migration repo for the App
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

# Create a dictionary to store session variables while traversing the api
session_dict = dict()

# Email configuration
MAIL_SERVER = 'smtp.googlemail.com'
MAIL_PORT = 465
MAIL_USE_TLS = False
MAIL_USE_SSL = True
