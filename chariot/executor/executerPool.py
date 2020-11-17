# import concurrent.futures
# import threading
# import queue
# from ..util import Context
#
#
# def pool_init(max_workers=None):
#     executor = Executor(max_workers)
#     Context.pool = executor
#
#
# class Executor(threading.Thread):
#     def __init__(self, max_workers=None):
#         super().__init__()
#         self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
#         self.queue = queue.Queue()
#         self.stop_flag = False
#
#     def add_task(self, fn, call_back, *args, **kwargs):
#         self.queue.put((fn, call_back, args, kwargs))
#
#     def stop(self):
#         self.stop_flag = True
#
#     def run(self):
#         while not self.stop_flag:
#             try:
#                 fn, call_back, args, kwargs = self.queue.get(block=True, timeout=1)
#                 future = self.executor.submit(fn, *args, **kwargs)
#                 if call_back is not None:
#                     future.add_done_callback(call_back)
#             except queue.Empty:
#                 continue
#
#         # The treading need to stop, close pool
#         self.executor.shutdown(wait=False)
#
#
