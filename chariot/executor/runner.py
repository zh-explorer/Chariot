import subprocess
import concurrent.futures
import time
import os
import traceback

from ..util import Context
import queue
from ..db import ExpStatus, ExpLog, Flag, ChallengeInst


def pool_init(max_workers=None):
    if Context.exec_pool:
        Context.exec_pool.shutdown(wait=False)
        Context.exec_pool = None
    Context.exec_pool = concurrent.futures.ThreadPoolExecutor(max_workers)


def pool_stop():
    if Context.exec_pool:
        Context.exec_pool.shutdown(wait=False)
        Context.exec_pool = None


def flag_search(data: bytes):
    if not data:
        return []
    flags = []
    p = Context.flag_pattern
    idx = 0
    while True:
        result = p.search(data, idx)
        if result is None:
            break
        idx = result.end()
        flags.append(result.group())
    return flags


class ExecResult(object):
    def __init__(self, flag, ret_code, stdout, stderr):
        self.ret_code = ret_code
        self.stdout = stdout
        self.stderr = stderr
        self.flag = flag


class ExpRunner(object):
    def __init__(self, file_path: str, inst_id: int, notify_queue: queue.Queue, timeout=20):
        if Context.exec_pool is None:
            pool_init(Context.max_workers)
        self.file_path = file_path
        self.timeout = timeout
        self.exp_name = os.path.basename(self.file_path)
        self.process_time = int(time.time())
        self.notify_queue = notify_queue

        session = Context.db.get_session()
        inst = session.query(ChallengeInst).filter(ChallengeInst.id == inst_id).one()

        self.ip = inst.address
        self.port = inst.port
        self.team_name = inst.team.name
        self.challenge_name = inst.challenge.name
        self.flag_path = inst.challenge.flag_path

        # insert exp record
        r = ExpLog()
        r.timestamp = self.process_time
        # this should not failed
        r.inst_id = inst_id
        # r.inst_id = session.query(ChallengeInst).filter(ChallengeInst.team.name == self.team_name,
        #                                                    ChallengeInst.challenge.name == self.challenge_name).one()

        # we cache this id for next time use
        r.exp_name = self.exp_name
        session.add(r)
        session.commit()
        self.log_id = r.id
        session.close()

    def start(self):
        def _foo():
            try:
                return self.run()
            except Exception as e:
                Context.logger.error(traceback.format_exc())
                return ExecResult(None, -1, None, None)

        def _call_back(future):

            if future.exception():
                e = future.exception()
                Context.logger.error("A except was raise %s" % str(e))
                r = ExecResult(None, -1, None, None)
            else:
                r = future.result()
            self.run_finish(r)

        f = Context.exec_pool.submit(_foo)
        f.add_done_callback(_call_back)

    def run(self):
        # we pass ip and port as cmdline args and env
        cmd = [self.file_path]
        env = os.environ
        if self.ip:
            env["TARGET_IP"] = self.ip
            cmd.append(self.ip)
        if self.port:
            env["TARGET_PORT"] = str(self.port)
            cmd.append(str(self.port))
        env["CHARIOT"] = "true"
        env["FLAG_PATH"] = self.flag_path
        env["FLAG_PATTERN"] = Context.flag_pattern.pattern.decode()

        # TODO: move this to a better place
        env['PYTHONPATH'] = "/tmp/pwntools"

        # TODO: we should change cwd to tmp to avoid some error or should set this as a config?
        cwd = os.path.dirname(self.file_path)
        try:
            p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd, timeout=self.timeout,
                               env=env, bufsize=0)
            # at this time process run finish, return all data to main thread
            ret_code = p.returncode
            stdout = p.stdout
            stderr = p.stderr
        except subprocess.TimeoutExpired as e:
            ret_code = -1
            stdout = e.stdout
            stderr = e.stderr
        except subprocess.SubprocessError:
            Context.logger.error("unknown error when exec exp")
            return ExecResult(None, -1, None, None)

        flags = flag_search(stdout)
        flags += flag_search(stderr)
        if flags:
            flag_set = set(flags)
            if len(flag_set) > 1:
                Context.logger.warning("We find Multiple flags in log, and choose last one")

            flag = flags[-1].decode()
        else:
            flag = None
        r = ExecResult(flag, ret_code, stdout, stderr)
        return r

    def save_log(self, stdout, stderr):
        if not stdout:
            stdout = b''
        if not stderr:
            stderr = b''
        base_path = os.path.join(Context.log_path, self.challenge_name, self.team_name,
                                 os.path.splitext(self.exp_name)[0])
        if not os.path.exists(base_path):
            os.makedirs(base_path, exist_ok=True)
        max_num = 0
        for d in os.listdir(base_path):
            num = 0
            try:
                num = int(d)
            except ValueError:
                pass
            if num > max_num:
                max_num = num
        dir_num = max_num + 1
        base_path = os.path.join(base_path, "%05d" % dir_num)

        # this should not failed
        os.mkdir(base_path)

        with open(os.path.join(base_path, "stderr_" + str(self.process_time)), "wb") as fp:
            fp.write(stderr)

        with open(os.path.join(base_path, "stdout_" + str(self.process_time)), "wb") as fp:
            fp.write(stdout)
        return base_path

    def run_finish(self, result: ExecResult):
        # 1. save all log
        # 2. search flag in stdout and stderr
        # 3. log all data to database
        log_path = self.save_log(result.stdout, result.stderr)
        flag = result.flag
        # update record and flag
        session = Context.db.get_session()
        r = session.query(ExpLog).filter(ExpLog.id == self.log_id).one()
        if flag:
            f = Flag()
            f.flag_data = flag
            f.timestamp = int(time.time())
            f.inst_id = r.inst_id
            f.weight = r.inst.weight
            session.add(f)
            session.commit()
            r.flag_id = f.id
            r.status = ExpStatus.flag_submitting
        else:
            r.status = ExpStatus.attack_failed
        r.log_path = log_path
        session.commit()
        session.close()
        self.notify_queue.put(self.log_id)
        Context.notify_main_thread()
