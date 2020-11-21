import concurrent.futures
from ..util import Context
import queue
from ..db import Flag, FlagStatus, ExpStatus
import traceback



def submit_init():
    if Context.submit_pool:
        Context.submit_pool.shutdown(wait=False)
        Context.submit_pool = None

    Context.submit_pool = concurrent.futures.ThreadPoolExecutor()


def submit_stop():
    if Context.submit_pool:
        Context.submit_pool.shutdown(wait=False)
        Context.submit_pool = None


class FlagSubmitter(object):
    def __init__(self, flag_id: int, notify_queue: queue.Queue, scheduler=None):
        if Context.submit_pool is None:
            submit_init()
        self.scheduler = scheduler
        self.notify_queue = notify_queue
        self.flag_id = flag_id

        session = Context.db.get_session()
        flag = session.query(Flag).filter(Flag.id == flag_id).one()
        self.flag_data = flag.flag_data
        self.flag_time = flag.timestamp
        self.flag_weight = flag.weight
        if flag.inst_id is not None:
            inst = flag.inst
            self.challenge_name = inst.challenge.name
            self.team_name = inst.team.name

        session.commit()
        session.close()

    def start(self):
        def _foo():
            try:
                return self.run()
            except Exception as e:
                Context.logger.error(traceback.format_exc())
                return FlagStatus.internal_error, "internal code error"

        def _call_back(future):
            if future.exception():
                e = future.exception()
                Context.logger.error("A except was raise %s" % str(e))
                r = FlagStatus.internal_error, "internal code error"
            else:
                r = future.result()
            self.run_finish(r)

        future = Context.submit_pool.submit(_foo)
        future.add_done_callback(_call_back)

    def run_finish(self, result):
        session = Context.db.get_session()
        flag = session.query(Flag).filter(Flag.id == self.flag_id).one()
        flag.submit_status = result[0]
        flag.comment = result[1]

        Context.logger.info(f"flag {flag.flag_data} submit status {flag.submit_status.name}")

        for l in flag.exp_log:
            l.status = ExpStatus.success if flag.submit_status == FlagStatus.submit_success else ExpStatus.flag_error

        session.commit()
        session.close()
        self.notify_queue.put((self.flag_id, self.scheduler))
        Context.notify_main_thread()

    def run(self):
        return FlagStatus.submit_success, "success"
