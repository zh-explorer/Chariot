import os
from ..util import Context
from ..config_validate import load_exp_config


def exp_finder(exp_path):
    exp_files = []
    for root, dirs, files in os.walk(exp_path):
        for f in files:
            if f[:3] == "exp":
                exp_files.append(os.path.join(root, f))
    exp_files.sort()
    return exp_files


class Exp:
    def __init__(self, path, retry_time, timeout, weight):
        self.path = path
        self.retry_time = retry_time
        self.timeout = timeout
        self.weight = weight

    def __lt__(self, other):
        if self.weight == other.weight:
            return self.path < other.path
        else:
            return self.weight < other.weight


def get_exp_default(exp_file_path):
    exp_files = exp_finder(exp_file_path)
    exps = []
    for e in exp_files:
        exps.append(Exp(os.path.join(exp_file_path, e), 3, 30, 10))
    return exps


def get_exp_from_conf(exp_file_path):
    with open(os.path.join(exp_file_path, "config.yaml"), 'r') as fp:
        conf = load_exp_config(fp)

    exps = []
    for e in conf:
        exps.append(Exp(os.path.join(exp_file_path, e['path']), e['retry'], e['timeout'], e['weight']))
    return exps


def exp_get(challenge_name):
    # first check is exp config is exists
    exp_file_path = os.path.join(Context.exp_path, challenge_name)
    if os.path.exists(os.path.join(exp_file_path, "config.yaml")):
        return get_exp_from_conf(exp_file_path)
    else:
        return get_exp_default(exp_file_path)
