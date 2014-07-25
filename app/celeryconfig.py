from celery.schedules import crontab

CELERYBEAT_SCHEDULE = {
    'every-hour': {
        'task': 'tasks.main',
        'schedule': crontab(hour='*/1'),
    },
}
