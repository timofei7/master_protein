#!/usr/bin/env python
"""
could be used to add handling for errors
currently doesn't do anything
author:   Tim Tregubov, 12/2014
"""

import sys
from rq import Queue, Connection, Worker

# Preload libraries
# import library_that_you_want_preloaded

# Provide queue names to listen to as arguments to this script,
# similar to rqworker

def exc_handler(job, exc_type, exc_value, traceback):
    # progressfile_path = job.meta['progressfile']
    # progressfile = open(progressfile_path, "w+")
    # progressfile.seek(0)
    # progressfile.write(str(traceback))
    # progressfile.truncate()
    # progressfile.flush()

    return True

with Connection():
    qs = map(Queue, sys.argv[1:]) or [Queue()]

    w = Worker(qs)

    # w.push_exc_handler(exc_handler)

    w.work()


