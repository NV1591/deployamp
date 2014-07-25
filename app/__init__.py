from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.mail import Mail
from celery import Celery

# Instantiate the app object and define the config
app = Flask(__name__)

# Define a celery broker agent to queue tasks
worker = Celery('tasks', backend='amqp', broker='amqp://')

app.config.from_object('config')

mail = Mail(app)

# Initialize the DataBase with SQLAlchemy object
db = SQLAlchemy(app)

from app import views, models
