from ..config_validate import load_conf_file
from ..util import Context
from ..db import build_database, Team, Challenge, ChallengeInst, FlagStatus, Flag, ExpStatus, ExpLog
from ..executor import ExpRunner, FlagSubmitter, pool_init, pool_stop, submit_init, submit_stop
from .time_watcher import alarm_start, alarm_stop, current_round, round_range
from .file_watcher import watcher_start, watcher_stop
from .exp_manager2 import ExpManager
from .exploit import ExploitScheduler
import signal
import threading
import queue


def testfunc():
    with open("config.yaml") as fp:
        load_conf_file(fp)
    build_database()
    Context.cv = threading.Condition()
    e = threading.Event()
    watcher_start(e)
    manager = ExpManager("pwn1")

    for i in range(4):
        exp = manager.exp_iter()
        if exp:
            print(exp.name)
        else:
            print("stop")
    print("wait")
    while True:
        try:
            with Context.cv:
                Context.cv.wait_for(lambda: e.is_set())
            e.clear()
            manager.check_exp_update()
            while True:
                exp = manager.exp_iter()
                if exp:
                    print(exp.name)
                else:
                    print("end")
                    break
        except KeyboardInterrupt:
            break


def signal_init(flag_submit, time_event):
    signal.signal(signal.SIGUSR1, lambda: flag_submit.notify_new_flag())
    signal.signal(signal.SIGUSR2, lambda: time_event.set())


class FlagSubmitQueue(object):
    def __init__(self, notify_queue):
        self.notify_queue = notify_queue
        self.free_worker_count = Context.max_submitters
        # TODO: not good
        if self.free_worker_count is None:
            self.free_worker_count = 100
        self.notify_new_flag()  # submit flag that not upload

    def notify_submit_flag(self):
        self.free_worker_count += 1

    def notify_new_flag(self):
        if self.free_worker_count != 0:
            start, end = round_range(current_round())
            session = Context.db.get_session()
            flags = session.query(Flag).filter(Flag.timestamp >= start, Flag.timestamp <= end,
                                               Flag.submit_status == FlagStatus.wait_submit).order_by(
                Flag.weight).all()

            c = min(len(flags), self.free_worker_count)
            for i in range(c):
                f = flags[i]
                e = None
                for exploit in Context.exploit_list:
                    if exploit.inst_id == f.inst_id:
                        e = exploit
                        break
                submitter = FlagSubmitter(f.id, self.notify_queue, e)
                submitter.start()
            self.free_worker_count -= c
            session.commit()
            session.close()


def server_start(config_file: str):
    with open(config_file) as fp:
        load_conf_file(fp)

    build_database()
    Context.cv = threading.Condition()

    # start alarm clock
    time_event = threading.Event()
    time_event.set()
    alarm_start(time_event)

    # start file watch
    file_event = threading.Event()
    watcher_start(file_event)

    # start runner thread pool
    runner_queue = queue.Queue()

    # start submitter pool
    submitter_queue = queue.Queue()

    flag_submit_queue = FlagSubmitQueue(submitter_queue)

    def task_down():
        if not submitter_queue.empty():
            return True
        elif not runner_queue.empty():
            return True
        elif file_event.is_set():
            return True
        elif time_event.is_set():
            return True
        else:
            return False

    signal_init(flag_submit_queue, time_event)

    # the thread pool will init in the first submit os task
    while True:
        try:
            with Context.cv:
                Context.cv.wait_for(task_down)
            # a new round is start
            if time_event.is_set():
                Context.logger.info("new round")
                time_event.clear()
                session = Context.db.get_session()
                now_round = current_round()
                for exploit in Context.exploit_list:
                    exploit.stop()
                Context.exploit_list = []

                start, end = round_range(current_round())
                for flag in session.query(Flag).filter(Flag.timestamp < start,
                                                       Flag.submit_status == FlagStatus.wait_submit):
                    flag.submit_status = FlagStatus.flag_expire
                session.commit()

                for inst in session.query(ChallengeInst).join(Challenge).join(Team).filter(Team.active == 1,
                                                                                           Challenge.active == 1).all():
                    exploit = ExploitScheduler(inst.id, now_round, runner_queue, submitter_queue)
                    exploit.start()
                    Context.exploit_list.append(exploit)
                session.commit()
                session.close()

            if file_event.is_set():
                file_event.clear()
                for inst in Context.exploit_list:
                    inst.exp_modify()

            while not runner_queue.empty():
                log_id, exploit, is_success = runner_queue.get()
                exploit.task_update(log_id, is_success)
                if is_success:
                    flag_submit_queue.notify_new_flag()

            while not submitter_queue.empty():
                flag_id, exploit = submitter_queue.get()
                if exploit:
                    exploit.flag_submitted(flag_id)
                flag_submit_queue.notify_submit_flag()

        except KeyboardInterrupt:
            break

    # stop all thing and exit
    alarm_stop()
    pool_stop()
    submit_stop()
    watcher_stop()
