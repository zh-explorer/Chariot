from ..util import Context
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

ob = None


class FileWatch(FileSystemEventHandler):
    def __init__(self, notify_event):
        self.notify_event = notify_event
        self.exp_dir = Context.exp_path

    def on_modified(self, event):
        if not event.is_directory:
            if os.path.basename(event.src_path) == "update":
                self.notify_event.set()
                Context.notify_main_thread()


class Watcher(object):
    def __init__(self, notify_event):
        self.exp_path = Context.exp_path
        self.update_path = os.path.join(self.exp_path, "update")

        with open(self.update_path, 'w'):
            pass

        # take a dir snapshot first

        self.ob = Observer()
        self.ob.schedule(FileWatch(notify_event), self.update_path, recursive=True)
        self.ob.start()

    def stop(self):
        if self.ob:
            self.ob.stop()
            self.ob.join()
            self.ob = None


def watcher_start(notify_event):
    if Context.watcher:
        Context.watcher.stop()
        Context.watcher = None

    Context.watcher = Watcher(notify_event)


def watcher_stop():
    if Context.watcher:
        Context.watcher.stop()
        Context.watcher = None
