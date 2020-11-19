from ..config_validate import load_conf_file
from ..util import Context
from ..db import build_database, Team, Challenge, ChallengeInst, FlagStatus, Flag, ExpStatus, ExpLog
from ..executor import ExpRunner, flag_submit, pool_init, pool_stop, submit_init, submit_stop
from .exp_manager import exp_get
from .time_watcher import alarm_start, alarm_stop
from .file_watcher import watcher_start, watcher_stop
import threading
import queue


# def testfunc():
#     with open("config.yaml") as fp:
#         load_conf_file(fp)
#     build_database()
#     for i in exp_get("pwn2"):
#         print(i.__dict__)


def server_start(config_file: str):
    with open("config.yaml") as fp:
        load_conf_file(fp)

    build_database()
    Context.cv = threading.Condition()

    # start alarm clock
    time_event = threading.Event()
    time_event.set()
    alarm_start(time_event)

    # start file watch
    file_queue = queue.Queue()
    watcher_start(file_queue)

    # start runner thread pool
    runner_queue = queue.Queue()

    # start submitter pool
    submitter_queue = queue.Queue()

    def task_down():
        if not submitter_queue.empty():
            return True
        elif not runner_queue.empty():
            return True
        elif not file_queue.empty():
            return True
        elif time_event.is_set():
            return True
        else:
            return False

    # the thread pool will init in the first submit os task
    while True:
        try:
            with Context.cv:
                Context.cv.wait_for(task_down)

            session = Context.db.get_session()
            # a new round is start

        except KeyboardInterrupt:
            break

    # stop all thing and exit
    alarm_stop()
    pool_stop()
    submit_stop()
    watcher_stop()

