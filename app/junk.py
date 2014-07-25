import requests
from app import app, db
from config import login_url, login_payload, job_api_partial_url, activity_log_partial_url, task_api_partial_url, session_dict, recipent_list
from datetime import datetime
from datetime import timedelta
from models import Task_List
import json
import cPickle
from sqlalchemy import distinct
from models import Task_List
from flask import render_template

from flask.ext.mail import Mail, Message


def login():
    """
    Generic login method after the creation of a session on top of the
    login credentials
    """
    try:
        # Create session here
        session_object = requests.Session()
        # Send login request and bind that to seesion
        login_request = session_object.post(login_url, data=login_payload)
        return session_object
    except:
        app.logger.error('Login Failed!')


def get_time_delta():
    """
    Get the time delta for the api start time and end time creation
    """
    # The current UTC time
    current_time = datetime.utcnow().replace(microsecond=0)
    # Take the current date time in utc and then map it correctly to PST.
    current_time_adjusted = current_time - timedelta(hours=7)
    # Calculate the last time (Remember delta is one)
    last_time = current_time_adjusted - timedelta(hours=1)
    # Adjust start and end time to get the api kind of time format
    adjusted_current_time = str(current_time_adjusted.replace(minute=0, second=0)).replace(':', '').replace(' ', '').replace('-', '')
    adjusted_last_time = str(last_time.replace(minute=0, second=0)).replace(':', '').replace(' ', '').replace('-', '')
    return adjusted_current_time, adjusted_last_time


def add_task_entry():
    """
    Method used to add the final task api message for the second email and
    create an entry for the last one hour in the database.
    """
    # Craete a task api object that can be used to generate the HTML table
    # directly
    task_object = Task_List(
        job_id=session_dict['JOB_ID'],
        job_type=session_dict['TYPE'],
        job_owner=session_dict['OWNER'],
        task_message=session_dict['MESSAGE'])
    db.session.add(task_object)
    db.session.commit()


def task_api_call(session, job_id):
    """
    Generate a task api call for the tasks that have failed jobs
    and fetch the error message
    """
    try:
        task_api_call = session.get(task_api_partial_url)
        json_result = json.loads(task_api_call.content)
        # get the error message
        # responseData > Result > Message
        session_dict['MESSAGE'] = json_result['responseData']['result']['msg']
        add_task_entry()
        session_dict.clear()
    except:
        app.logger.info('Task api call failed for the current hour - {0}'.format(datetime.utcnow().replace(microsecond=0)))


def job_api_call(session, job_id):
    """
    Create a job api call for certain jobs that have atleast one failed
    task and store relevant data in the session to finally add that to the
    db
    """
    try:
        job_api_call = session.get(job_api_partial_url)
        json_result = json.loads(job_api_call.content)
        for entry in json_result['responseData']['task_list']:
            if entry['state'] != "SUCCESS":
                # Fetching the data relavant to the current job being read and
                # storing that to the session for further addition to database.
                session['JOB_ID'] = json_result['responseData']['job_id']
                session['TYPE'] = json_result['responseData']['type']
                session['OWNER'] = json_result['responseData']['owner']
                task_api_call(session, entry['id'])
    except:
        app.logger.info('Job api call failed for the current hour - {0}'.format(datetime.utcnow().replace(microsecond=0)))


def activity_log_call(session):
    """
    Create an activity log call to get the high level idea about the jobs in
    general and look up to find what all jobs have failed tasks
    """
    # Get the time delta for the job
    current_time, last_time = get_time_delta()
    # Create the activity log url
    activity_log_api_url = activity_log_partial_url.format(current_time,
                                                           last_time)
    app.logger.info('ACTIVITY LOG API URL - {0}'.format(job_api_url))
    job_list = []
    try:
        activity_log_call = session.get(activity_log_api_url)
        json_result = json.loads(activity_log_call.content)
        for entry in json_result['responseData']:
            # Get all the jobs that have failed
            if not int(entry['failed']):
                job_id = entry['job_id']
                jobs_list.append(job_id)
        # Iterate all the failed jobs to get more meaningful insight into this.
        for job_id in jobs_list:
            job_api_call(session, job_id)

        if session:
            session.clear()
    except:
        app.logger.info('Activity Log api call failed for the current hour - {0}'.format(datetime.utcnow().replace(microsecond=0)))


def email_content_generation(email_dictionary, email_headers):
    html = render_template(email_dictionary,
                           email_headers,
                           'email2.html')


def db_clean_up():
    pass


def process_job(job_type):
    dict_list = []
    dict_job = dict()
    email_headers = []
    counter = 0
    rows = Task_List.query.filter(job_type=job_type).all()
    for row in rows:
        job_dict = dict()
        job_dict['Job ID'] = row.job_id
        job_dict['Owner'] = row.job_owner
        job_dict['Failure Reason'] = row.task_message
        if not counter:
            for key in job_dict.keys():
                email_headers.append(key)
        dict_list.append(job_dict)
        counter += 1

    for item in dict_list:
        job_id = item['Job ID']
        if job_id not in dict_job.keys():
            dict_job[job_id] = []
            dict_job[job_id].append(item['Failure Reason'])
        else:
            if item['Failure Reason'] in dict_job[job_id]:
                item.remove()
            else:
                dict_job[job_id].append(item['Failure Reason'])

    return dict_list, email_headers


def email_scheduler(email_html):
    app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'ampmailuser@gmail.com'
    app.config['MAIL_PASSWORD'] = 'ampuser4901th'

    mail = Mail(app)
    msg = Message(subject='Test Email Job Task Breakdown',
                  sender=app.config['FLASKY_MAIL_SENDER'],
                  recipients=recipent_list)
    msg.body = email_html
    mail.send(msg)


def database_feed():
    browser_session = login()
    activity_log_call(browser_session)


def db_cleanup():
    pass


def database_retrieve():
    job_type_list = []
    jobs = []
    email_dict = dict()
    # fetch all the distinct job types from the database
    job_type_name = db.session.query(distinct(Task_List.job_type)).all()
    for job in job_type_name:
        job_type_list.append(job.job_type)

    for job_type in job_type_list:
        email_dict[job_type] = process_job(job_type)

    return email_dict


def main():
    database_feed()
    email_dictionary, email_headers = database_retrieve()
    email_html = email_content_generation(email_dictionary, email_headers)
    email_scheduler(email_html)
    db_cleanup()
