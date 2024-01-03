from celery import Celery

app = Celery('validator', broker='pyamqp://guest@localhost//')

@app.task
def add(x, y):
    return x + y
