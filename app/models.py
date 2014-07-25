from app import db


class Task_List(db.Model):
    """Stores primary information about the tasks that have failed in the last
    one hour"""
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    job_id = db.Column(db.String)
    job_type = db.Column(db.String)
    job_owner = db.Column(db.String)
    task_message = db.Column(db.String)
