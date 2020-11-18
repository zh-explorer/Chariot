from ..util import Context
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from watchdog.utils import dirsnapshot

ob = None


class FileWatch(FileSystemEventHandler):
    def __init__(self, notify_queue):
        self.notify_queue = notify_queue
        self.exp_dir = Context.exp_path
        self.snapshot = dirsnapshot.DirectorySnapshot(self.exp_dir, recursive=True)

    def on_modified(self, event):
        if not event.is_directory:
            if os.path.basename(event.src_path) == "update":
                s = dirsnapshot.DirectorySnapshot(self.exp_dir, recursive=True)
                diff = dirsnapshot.DirectorySnapshotDiff(self.snapshot, s)
                diff = set(diff.files_created + diff.files_modified)
                for file_path in diff:
                    if os.path.basename(file_path)[:3] == "exp":
                        self.notify_queue.put(file_path)
                self.snapshot = s


class Watcher(object):
    def __init__(self, notify_queue):
        self.exp_path = Context.exp_path
        self.update_path = os.path.join(self.exp_path, "update")

        with open(self.update_path, 'w'):
            pass

        # take a dir snapshot first

        self.ob = Observer()
        self.ob.schedule(FileWatch(notify_queue), self.update_path, recursive=True)
        self.ob.start()

    def stop(self):
        if self.ob:
            self.ob.stop()
            self.ob.join()
            self.ob = None


def watcher_start(notify_query):
    if Context.watcher:
        Context.watcher.stop()
        Context.watcher = None

    Context.watcher = Watcher(notify_query)


def watcher_stop():
    if Context.watcher:
        Context.watcher.stop()
        Context.watcher = None
