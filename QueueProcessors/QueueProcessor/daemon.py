#!/usr/bin/env python
"""
    Code taken from:
    http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/
"""
import logging
import os
import sys
import time

import atexit
from signal import SIGTERM


class Daemon(object):
    """
    A generic daemon class.
    Usage: subclass the Daemon class and override the run() method
    """
    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile

    def daemonize(self):
        """
        do the UNIX double-fork magic, see Stevens' "Advanced
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try:
            # pylint: disable=no-member
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError, exp:
            logging.error("fork #1 failed: %d (%s)\n", exp.errno, exp.strerror)
            sys.exit(1)

        # decouple from parent environment
        os.chdir("/")
        # pylint: disable=no-member
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            # pylint: disable=no-member
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except OSError, exp:
            logging.error("fork #2 failed: %d (%s)\n", exp.errno, exp.strerror)
            sys.exit(1)

        # redirect standard file descriptors
        if self.stdin is not None and self.stdout is not None and self.stderr is not None:
            sys.stdout.flush()
            sys.stderr.flush()
            s_in = file(self.stdin, 'r')
            s_out = file(self.stdout, 'a+')
            s_err = file(self.stderr, 'a+', 0)
            os.dup2(s_in.fileno(), sys.stdin.fileno())
            os.dup2(s_out.fileno(), sys.stdout.fileno())
            os.dup2(s_err.fileno(), sys.stderr.fileno())

        # write pidfile
        atexit.register(self.delpid)
        pid = str(os.getpid())
        file(self.pidfile, 'w+').write("%s\n" % pid)
        logging.info("Started daemon with PID %s", str(pid))

    def delpid(self):
        """ delete the pid file """
        os.remove(self.pidfile)

    def start(self):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        try:
            pid_file = file(self.pidfile, 'r')
            pid = int(pid_file.read().strip())
            pid_file.close()
        except IOError:
            pid = None

        if pid:
            message = "pidfile %s already exist. Daemon already running?\n"
            logging.warning(message, self.pidfile)
            sys.exit(1)

        # Start the daemon
        self.daemonize()
        self.run()

    def stop(self):
        """
        Stop the daemon
        """
        # Get the pid from the pidfile
        try:
            pid_file = file(self.pidfile, 'r')
            pid = int(pid_file.read().strip())
            pid_file.close()
        except IOError:
            pid = None

        if not pid:
            message = "pidfile %s does not exist. Daemon not running?\n"
            logging.error(message, self.pidfile)
            # Not an error in a restart
            return

        logging.info("Stopping daemon with PID %s", str(pid))

        # Try killing the daemon process
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError, err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                logging.error(str(err))
                sys.exit(1)

    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        self.start()

    def run(self):
        """
        You should override this method when you subclass Daemon. It will be called after the
        process has been daemonized by start() or restart().
        """