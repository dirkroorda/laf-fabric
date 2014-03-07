import sys
import collections
import time

class Timestamp(object):
    '''Time management.

    Objects remember their creation time. So they can issue statements about how much time has been elapsed.
    All timed log messages of the program should be issued through the :meth:`progress` method of this class.

    It is also possible to connect a logfile to these objects.
    When progress messages are issued, they are also written to the connected log file.
    '''

    verbose_level = collections.OrderedDict((
        ('SILENT', -1),
        ('NORMAL', 0),
        ('INFO', 1),
        ('VERBOSE', 2),
        ('DEBUG', 10),
    ))


    def __init__(self, log_file=None):
        '''Upon creation, retrieves the time.

        Args:
            log_file (file):
                open file handle for writing. Optional. If not ``None`` stores the handle in the object's data.
        '''
        self.timestamp = time.time()
        '''Instance member holding the time the object was created'''

        self.log = None
        '''Instance member holding a handle to a logfile, open for writing, if a log file has been attached to the object.'''

        self.verbose = 0
        '''Instance member reflecting the verbosity level of the application run.  '''

        if log_file:
            self.connect_log(log_file)

    def elapsed(self):
        '''Returns the time elapsed since creation of the :class:`Timestamp` object.

        Returns:
            A pretty formatted string, ready to include in a message.
        '''

        interval = time.time() - self.timestamp
        if interval < 10:
            return "{: 2.2f}s".format(interval)
        interval = int(round(interval))
        if interval < 60:
            return "{:>2d}s".format(interval)
        if interval < 3600:
            return "{:>2d}m {:>02d}s".format(interval // 60, interval % 60)
        return "{:>2d}h {:>02d}m {:>02d}s".format(interval // 3600, (interval % 3600) // 60, interval % 60)

    def set_verbose(self, verbose):
        '''Set the verbosity level

        Args:
            verbose (string): indicator of verbosity. Values in increasing order:
            SILENT NORMAL INFO VERBOSE DEBUG

            Messages with a higher *verbose* will be suppressed.
        '''
        self.verbose = self.verbose_level[verbose if verbose else 'NORMAL']

    def reset(self):
        '''Set the time to the current time
        '''
        self.timestamp = time.time()

    def connect_log(self, log_file):
        '''Connects a log file to the object.

        Args:
            log_file (file):
                open handle for writing.
        '''

        self.log = log_file

    def disconnect_log(self):
        '''Connects a log file to the object.

        Args:
            log_file (file):
                open handle for writing.
        '''

        self.log = None

    def progress(self, msg, newline=True, withtime=True, verbose=None):
        '''Issues a timed progress message.

        The message is issued to the standard error, and, if a log file has been connected, also to the log file.

        Args:
            msg (str):
                text of the message
            newline (bool):
                whether or not to add a newline. Optional. Make it ``False`` to not add a newline.
            withtime (bool):
                whether to precede the text with timing information (time elapsed since the last reset of the
                underlying :class:`laf.timestamp.Stamp` object.
            verbose (int):
                if it is not higher than the application-wide verbosity the message will be printed.
                Default 0. So, unless verbosity level is less than 0, a message without explicit *verbose*
                will always be printed.
        '''
        verbose = 'NORMAL' if verbose == None else verbose
        if self.verbose_level[verbose] > self.verbose:
            return 
        timed_msg = "{:>7} ".format(self.elapsed()) if withtime else ''
        timed_msg += msg
        if newline:
            timed_msg += "\n"
        sys.stderr.write(timed_msg)
        sys.stderr.flush()
        if self.log:
            self.log.write(timed_msg)
