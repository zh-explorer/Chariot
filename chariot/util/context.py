from logging import Logger


class Context:
    timeout = None
    log_file = None
    log_level = None
    logger: Logger = None
    conf = None
