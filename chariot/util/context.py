from logging import Logger
import re


class Context:
    # parse from config
    log_path: str = None
    log_level: str = None
    logger: Logger = None
    conf = None
    round_time: int = None
    teams = []
    challenges = []
    # TODO: paste from config
    flag_pattern = None
    start_time = None
    max_workers = None

    # init when start
    db = None
    exec_pool = None
