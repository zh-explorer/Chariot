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
    start_time = None

    # init when start
    db = None
    exec_pool = None
    watcher = None
    alarm = None
    cv = None
