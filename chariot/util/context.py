from logging import Logger
import re


class Context:
    # parse from config
    exp_path: str = None
    log_path: str = None
    log_level: str = None
    logger: Logger = None
    conf = None
    round_time: int = None
    teams = []
    challenges = []
    flag_pattern = None
    max_workers = None
    max_submitters = None
    start_time = None

    # init when start
    db = None
    exec_pool = None
    submit_pool = None
    watcher = None
    alarm = None
    cv = None

    @staticmethod
    def notify_main_thread():
        if not Context.cv:
            raise RuntimeError("The main thread is not init")
        with Context.cv:
            Context.cv.notify()
