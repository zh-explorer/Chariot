from logging import Logger


class Context:
    log_file: str = None
    log_level: str = None
    logger: Logger = None
    conf = None
    round_time: int = None
    teams = []
    challenges = []
    db = None
