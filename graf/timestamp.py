# -*- coding: utf8 -*-

import sys
import time

class Timestamp():
    timestamp = None
    log = None

    def __init__(self, log_file=None):
        self.timestamp = time.time()
        if log_file:
            self.connect_log(log_file)

    def elapsed(self):
        interval = time.time() - self.timestamp
        if interval < 10:
            return "{: 2.2f}s".format(interval)
        interval = int(round(interval))
        if interval < 60:
            return "{:>2d}s".format(interval)
        if interval < 3600:
            return "{:>2d}m {:>02d}s".format(interval // 60, interval % 60)
        return "{:>2d}h {:>02d}m {:>02d}s".format(interval // 3600, (interval % 3600) // 60, interval % 60)

    def connect_log(self, log_file):
        self.log = log_file

    def progress(self, msg, newline=True):
        timed_msg = "{} {}{}".format(self.elapsed(), msg, "\n" if newline else "")
        sys.stdout.write(timed_msg)
        sys.stdout.flush()
        if self.log:
            self.log.write(timed_msg)
