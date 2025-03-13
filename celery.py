from celery import Celery
import os

def make_celery(app_name=__name__):
    return Celery(app_name, broker='redis://localhost:6379/0', backend='redis://localhost:6379/0') #TODO change this in production

celery = make_celery()