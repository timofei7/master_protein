#!/usr/bin/env python
"""
a generic class for implementing a server task.
this class does not actually do anything. it needs
to be extended and the functions filled in with
something meaningful specific for a task
author:   Gevorg Grigoryan, 08/31/2016
"""

import os
import tempfile
import subprocess
from werkzeug.utils import secure_filename
from rq import Queue
from redis import Redis
import Tasks
import re


class ServerTask(object):
    """
    main class
    uses an rq redis worker to submit a background task
    to do something
    """

    def __init__(self, app):
        """
        sets up redis queue and connection
        """

        self.app = app
        self.redis_conn = Redis()
        self.rq = Queue(connection=self.redis_conn)
        self.inputs = ''
        self.maxTime = 3600

    def process(self):
        """
        override this
        actually process the request; does all the error checking
        and parsing, and prepares all needed information for function
        do in self.inputs variable
        """
	handle = 1
        error = False

        return handle, error

    def progress(self):
        """
        override this
        a generator for providing progress updates
        """
	yield ''

    @staticmethod
    def do(inp):
        """
        override this
        a static method that actually performs the computation
        """
	return True

    def enqueue(self):
        """
        schedule the job
        """
        job = self.rq.enqueue_call(self.do, args = self.inputs, timeout = self.maxTime)
        return job

if __name__ == "__main__":
    pass
