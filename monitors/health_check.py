"""
Threading class to check the health of the End of Run Monitor service
"""
from datetime import datetime
import logging
import time
import threading
import csv

from monitors import end_of_run_monitor
from monitors import icat_monitor
from settings import (INSTRUMENTS, EORM_LAST_RUN_FILE)


# pylint:disable=missing-docstring
class HealthCheckThread(threading.Thread):

    def __init__(self, time_interval):
        threading.Thread.__init__(self)
        self.time_interval = time_interval
        self.exit = False

    def run(self):
        """
        Perform a service health check every time_interval
        """
        while self.exit is False:
            service_okay = self.health_check()
            if service_okay:
                logging.info("No Problems detected with service")
            else:
                logging.warning("Problem detected with service. Restarting service...")
                self.restart_service()
            time.sleep(self.time_interval)
        logging.info('Main Health check thread loop stopped')

    @staticmethod
    def health_check():
        """
        Check to see if the service is still running as expected
        :return: True: Service is okay, False: Service requires restart
        """
        logging.info('Performing Health Check at %s', datetime.now())

        # Loop through the instrument list, getting the last run on each
        with open(EORM_LAST_RUN_FILE, 'rb') as last_run_file:
            last_run_reader = csv.reader(last_run_file)
            for row in last_run_reader:
                # Query the ICAT
                icat_last_run = icat_monitor.get_last_run(row[0])
                if icat_last_run:
                    if int(icat_last_run) > int(row[1]):
                        return False
        return True

    @staticmethod
    def restart_service():
        """
        Restart the end of run monitor service
        """
        end_of_run_monitor.stop()
        end_of_run_monitor.main()

    def stop(self):
        """
        Send a signal to stop the main thread loop
        """
        logging.info('Received stop signal for the Health Check thread')
        self.exit = True
