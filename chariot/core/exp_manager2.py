import os
import traceback
from functools import reduce
from os import path
from ..util import Context
from ..config_validate import load_exp_config
from watchdog.utils import dirsnapshot


class Exp:
    def __init__(self, name, entry, retry_time, timeout, weight, snapshot: dirsnapshot.DirectorySnapshot):
        self.name = name
        self.entry = entry
        self.retry_time = retry_time
        self.timeout = timeout
        self.weight = weight
        self.snapshot = snapshot

    def __lt__(self, other):
        if self.weight == other.weight:
            return self.name < other.name
        else:
            return self.weight < other.weight


class ExpManager(object):
    def __init__(self, challenge_name):
        self.challenge_name = challenge_name
        self.challenge_path = path.join(Context.exp_path, challenge_name)

        self.exps_o = self.get_exps()
        self.exps = []
        for i in self.exps_o:
            self.exps.append([i, i.retry_time])
        self.exp_index = 0

    def get_exp_from_conf(self, exp_name):
        try:
            with open(path.join(self.challenge_path, exp_name, "config.yaml"), 'r') as fp:
                conf = load_exp_config(fp)
        except Exception as e:
            Context.logger.error(traceback.format_exc())
            return None
        snapshot = dirsnapshot.DirectorySnapshot(path.join(self.challenge_path, exp_name))
        return Exp(exp_name, path.join(self.challenge_path, exp_name, conf['path']), conf['retry'], conf['timeout'],
                   conf['weight'], snapshot)

    def get_exp_default(self, exp_name):
        entry = None
        for f in os.listdir(path.join(self.challenge_path, exp_name)):
            if f[:3] == "exp":
                entry = f
                break
        if entry:
            snapshot = dirsnapshot.DirectorySnapshot(path.join(self.challenge_path, exp_name))
            return Exp(exp_name, path.join(self.challenge_path, exp_name, entry), 3, 30, 10, snapshot)
        else:
            return None

    def get_exp(self, exp_name):
        if path.exists(path.join(self.challenge_path, exp_name, "config.yaml")):
            exp_obj = self.get_exp_from_conf(exp_name)
        else:
            exp_obj = self.get_exp_default(exp_name)
        return exp_obj

    def get_exps(self):
        exp_dirs = []
        for f in os.listdir(self.challenge_path):
            if path.isdir(path.join(self.challenge_path, f)):
                exp_dirs.append(f)

        exps = []
        for exp in exp_dirs:
            exp_obj = self.get_exp(exp)
            if exp_obj:
                exps.append(exp_obj)
        exps.sort()
        return exps

    def is_modify(self, ref, snapshot):
        diff = dirsnapshot.DirectorySnapshotDiff(ref, snapshot)
        return diff.dirs_created or \
               diff.dirs_deleted or \
               diff.dirs_moved or \
               diff.dirs_modified or \
               diff.files_modified or \
               diff.files_created or \
               diff.files_deleted or \
               diff.files_modified

    def check_exp_update(self):
        modify_exps = []

        old_exp_name = set()
        for exp in self.exps_o:
            old_exp_name.add(exp.name)

        new_exp_name = set()
        for f in os.listdir(self.challenge_path):
            if path.isdir(path.join(self.challenge_path, f)):
                new_exp_name.add(f)

        add_exp_name = new_exp_name.difference(old_exp_name)
        del_exp_name = old_exp_name.difference(new_exp_name)

        remain_exp = new_exp_name.intersection(old_exp_name)
        for exp_name in remain_exp:
            exp = None
            for e in self.exps_o:
                if e.name == exp_name:
                    exp = e
                    break
            # exp will not be None
            snapshot = dirsnapshot.DirectorySnapshot(path.join(self.challenge_path, exp_name), recursive=True)
            if not self.is_modify(exp.snapshot, snapshot):
                continue
            exp_obj = self.get_exp(exp_name)
            if not exp_obj:
                # we deal this as exp is delete
                del_exp_name.add(exp_name)
            else:
                modify_exps.append(exp_obj)
        add_exps = []
        for name in add_exp_name:
            exp_obj = self.get_exp(name)
            if exp_obj:
                add_exps.append(exp_obj)

        self.resort_exp(add_exps, del_exp_name, modify_exps)

    def in_list(self, exp, list2):
        for e in list2:
            if e.name == exp.name:
                return True
        return False

    def resort_exp(self, add_exps, del_exps, modify_exps):
        # first del exp from list
        new_exps = []
        for e in add_exps:
            new_exps.append([e, e.retry_time])
        for e in modify_exps:
            new_exps.append([e, e.retry_time])

        for e, times in self.exps:
            if e.name in del_exps:
                continue
            if self.in_list(e, modify_exps):
                continue
            new_exps.append([e, times])
        self.exps = new_exps
        self.exps.sort()
        self.exps_o = []
        for e, i in self.exps:
            self.exps_o.append(e)

    def exp_iter(self) -> Exp:
        if not self.exps:
            return None
        if self.exp_index >= len(self.exps):
            self.exp_index = 0
        exp, retry = self.exps[self.exp_index]
        retry -= 1
        if retry == 0:
            self.exps.pop(self.exp_index)
        else:
            self.exps[self.exp_index][1] = retry
            self.exp_index += 1
        return exp
