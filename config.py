import os
basedir = os.path.abspath(os.path.dirname(__file__))

# The Datbase file and the Migration repo for the App
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

login_url = 'http://ampushinsight.com/account/login/?next=/'

activity_log_partial_url = 'http://ampushinsight.com/job/api/{0}/{1}/?limit=10000'
job_api_partial_url = 'http://ampushinsight.com/job/api/{0}'
task_api_partial_url = 'http://ampushinsight.com/job/api/task/{0}'
login_payload = {'next': '/',
                 'password': '4509th',
                 'signin': 'Sign In',
                 'username': 'nverma',
                 }

# Create a dictionary to store session variables while traversing the api
session_dict = dict()

# Email configuration
MAIL_SERVER = 'smtp.googlemail.com'
MAIL_PORT = 465
MAIL_USE_TLS = False
MAIL_USE_SSL = True
MAIL_USERNAME = 'ampmailuser@gmail.com'
MAIL_PASSWORD = 'ampmail4509th'
DEFAULT_MAIL_SENDER = 'ampmailuser@gmail.com'

# administrator list
ADMINS = ['ampmailuser@gmail.com']

# Recipent list for the email
recipent_list = ['nakkul.verma15@gmail.com',
                 'vaibhav.mathur@ampush.com',
                 'baonhat.nguyen@ampush.com',
                 ]
                 