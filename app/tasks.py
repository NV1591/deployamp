from celery import Celery
from views import database_feed, database_retrieve, email_content_generation, email_scheduler

celery = Celery('tasks', backend='amqp', broker='amqp://guest:guest@localhost:5672//')
celery.config_from_object('celeryconfig')


@celery.task
def main():
    database_feed()
    # email_dictionary, email_headers = database_retrieve()
    email_dictionary = database_retrieve()
    # email_html = email_content_generation(email_dictionary, email_headers)
    email_html = email_content_generation(email_dictionary)
    email_scheduler(email_html)
    # db_clean_up()
    return 'I am not fucked yet!'
