from ..util import Context
import time, datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger


def current_round():
    return round_calc(int(time.time()))


def round_calc(now_time):
    now_time = int(now_time)
    round_time = Context.round_time
    start_time = Context.start_time
    return int((now_time - start_time) / (round_time * 60))


def round_range(round_num):
    round_start = Context.start_time + round_num * 60 * Context.round_time
    round_end = round_start + 60 * Context.round_time
    return round_start, round_end


class AlarmClock(object):
    def __init__(self, event):
        self.event = event
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()

        def run_job():
            self.alarm()

        trigger = IntervalTrigger(minutes=Context.round_time, start_date=datetime.datetime.fromtimestamp(
            Context.start_time + 30))  # add a 30s delay
        self.job = self.scheduler.add_job(run_job, trigger)

    def alarm(self):
        self.event.set()
        Context.notify_main_thread()

    def stop(self):
        self.scheduler.shutdown()


def alarm_start(event):
    if Context.alarm:
        Context.alarm.stop()
        Context.alarm = None

    Context.alarm = AlarmClock(event)


def alarm_stop():
    if Context.alarm:
        Context.alarm.stop()
        Context.alarm = None
