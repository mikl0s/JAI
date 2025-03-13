from celery import Celery, current_app
from ip_geolocation import get_ip_geolocation, format_geolocation_data

@current_app.task
def get_ip_geolocation_task(ip_address):
    return get_ip_geolocation(ip_address)