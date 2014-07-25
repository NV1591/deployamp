from flask import render_template
from rq_scheduler import Scheduler
from flask.ext.mail import Message
from datetime import timedelta, datetime
import requests
from app import app, db, mail, worker
from config import login_url, login_payload, job_api_partial_url, activity_log_partial_url, task_api_partial_url, session_dict, recipent_list
from datetime import datetime
from datetime import timedelta
from models import Task_List
import json
import cPickle
from sqlalchemy import distinct
from flask.ext.mail import Message


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
    app.logger.info('object created')


def task_api_call(session, task_id):
    """
    Generate a task api call for the tasks that have failed jobs
    and fetch the error message
    """
    task_api_url = task_api_partial_url.format(task_id)
    try:
        task_api_call = session.get(task_api_url)
        json_result = json.loads(task_api_call.content)
        app.logger.info('I have reached here!')
        # get the error message
        # responseData > Result > Message
        session_dict['MESSAGE'] = json_result['responseData']['result']['msg']
        add_task_entry()
        session_dict.clear()
    except:
        pass


def job_api_call(session, job_id):
    """
    Create a job api call for certain jobs that have atleast one failed
    task and store relevant data in the session to finally add that to the
    db
    """
    job_api_url = 'http://ampushinsight.com/job/api/{0}'.format(job_id)
    try:
        job_api_call = session.get(job_api_url)
        app.logger.info('job_api_call - {0}'.format(job_api_url))
        json_result = json.loads(job_api_call.content)
        for entry in json_result['responseData'][0]['task_list']:
            if entry['state'] != "SUCCESS":
                # Fetching the data relavant to the current job being read and
                # storing that to the session for further addition to database.
                session_dict['JOB_ID'] = json_result['responseData'][0]['job_id']
                session_dict['TYPE'] = entry['type']
                session_dict['OWNER'] = json_result['responseData'][0]['owner']
                task_api_call(session, entry['id'])
    except:
        pass


def activity_log_call(session):
    """
    Create an activity log call to get the high level idea about the jobs in
    general and look up to find what all jobs have failed tasks
    """
    # Get the time delta for the job
    current_time, last_time = get_time_delta()
    # Create the activity log url
    activity_log_api_url = activity_log_partial_url.format(last_time,
                                                           current_time)
    app.logger.info('ACTIVITY LOG API URL - {0}'.format(activity_log_api_url))
    job_list = []
    try:
        activity_log_call = session.get(activity_log_api_url)
        json_result = json.loads(activity_log_call.content)
        app.logger.info('length of results - {0}'.format(len(json_result['responseData'])))
        for entry in json_result['responseData']:
            # Get all the jobs that have failed
            app.logger.info('type of failed - {0}'.format(type(entry['failed'])))
            if entry['failed']:
                app.logger.info('number of failed - {0}'.format(entry['failed']))
                job_id = entry['job_id']
                job_list.append(job_id)
            # Iterate all the failed jobs to get more meaningful insight into this.
            app.logger.info('length of job-list  - {0}'.format(len(job_list)))
        i = 0
        for job_id in job_list:
            i += 1
            job_api_call(session, job_id)
            if i == 2:
                break

        app.logger.info('Honestly I am done!')
    except:
        pass


# def email_content_generation(email_dictionary, email_headers):
def email_content_generation(email_dictionary):
    current_time = datetime.utcnow().replace(microsecond=0, second=0, minute=0)
    # Take the current date time in utc and then map it correctly to PST.
    current_time_adjusted = current_time - timedelta(hours=7)
    current_time_adjusted = current_time_adjusted.time()
    current_time_adjusted = str(current_time_adjusted)
    html = render_template('email2.html',
                           email_dictionary=email_dictionary,
                           time=current_time_adjusted)
    app.logger.info(html)
    return html


def db_clean_up():
    rows_deleted = Task_List.query.delete()
    app.logger.info('number of rows deletd - {0}'.format(rows_deleted))


def process_job(job_type):
    dict_list = []
    dict_job = dict()
    # failed_tasks['count'] = 1
    rows = Task_List.query.filter(Task_List.job_type == job_type).all()
    for row in rows:
        job_dict = dict()
        job_dict['Job ID'] = row.job_id
        job_dict['Owner'] = row.job_owner
        job_dict['Failure Reason'] = row.task_message
        job_dict['Failed Tasks'] = 1
        dict_list.append(job_dict)

    for item in dict_list:
        job_id = item['Job ID']
        if job_id not in dict_job.keys():
            dict_job[job_id] = dict()
            dict_job[job_id][item['Failure Reason']] = 1
        else:
            if item['Failure Reason'] in dict_job[job_id].keys():
                dict_job[job_id][item['Failure Reason']] += 1
                dict_list.remove(item)
            else:
                dict_job[job_id][item['Failure Reason']] = 1

    for item in dict_list:
        item['Failed Tasks'] = dict_job[item['Job ID']][item['Failure Reason']]

    return dict_list


def email_scheduler(email_html):
    msg = Message(subject='Test Email Job Task Breakdown',
                  recipients=["nakkul.verma15@gmail.com"],
                  sender='ampmailuser@gmail.com')
    msg.html = email_html
    try:
        mail.send(msg)
    except Exception as e:
        app.logger.error('error - {0} | e - {1}'.format(e.__class__, e))


def database_feed():
    browser_session = login()
    activity_log_call(browser_session)


def database_retrieve():
    job_type_list = []
    jobs = []
    email_dict = dict()
    # fetch all the distinct job types from the database
    job_type_name = db.session.query(Task_List.job_type).distinct()
    # job_type_name = db.session.query(distinct(Task_List.job_type)).all()
    # app.logger.info('job type name length - {0}'.format(len(job_type_name)))
    # i = 0
    for job in job_type_name:
        app.logger.info('job type - {0}'.format(job.job_type))
        job_type_list.append(job.job_type)

    # app.logger.info('number of rows returned - {0}'.format(i))

    for job_type in job_type_list:
        email_dict[job_type] = process_job(job_type)

    return email_dict


@worker.task
def main():
    # database_feed()
    # email_dictionary, email_headers = database_retrieve()
    email_dictionary = database_retrieve()
    # email_html = email_content_generation(email_dictionary, email_headers)
    email_html = email_content_generation(email_dictionary)
    app.logger.info(type(email_html))
    email_scheduler(email_html)
    # db_clean_up()
    return 'I am not fucked yet!'


# # RQ code
# from rq import Queue
# from worker import conn

# q = Queue(connection=conn)
# result = q.enqueue(main, 'http://127.0.0.1:5000')


# Get a scheduler for the "default" queue
# scheduler = Scheduler('high', connection=conn)

# scheduler.schedule(
#     scheduled_time=datetime.utcnow() - timedelta(hours=7),
#     func=main,
#     interval=3600,
#     repeat=None
# )


	