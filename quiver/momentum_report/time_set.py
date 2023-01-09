from venv import create
from apscheduler.schedulers.background import BackgroundScheduler
from . views import update_Report

def start():
    scheduler = BackgroundScheduler()
    # scheduler.add_job(update_Report, 'interval', minutes=20)
    #Runs from Monday to Sunday at 5:30 (am)
    scheduler.add_job(update_Report, 'cron', day_of_week='fri', hour=15, minute=00)
    scheduler.start()