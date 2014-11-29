#!/usr/bin/env python

from celery import Celery
from celery import current_app
from celery import shared_task
import os, re, subprocess, sys


def make_celery(app):
    celery = Celery(app.import_name,
                    backend=app.config['CELERY_BACKEND'],
                    broker=app.config['CELERY_BROKER_URL'],
                    set_as_current=True)
    celery.conf.update(app.config)
    # taskbase = celery.Task
    #
    # class ContextTask(taskbase):
    #     abstract = True
    #
    #     def __call__(self, *args, **kwargs):
    #         with app.app_context():
    #             return taskbase.__call__(self, *args, **kwargs)
    #
    # celery.Task = ContextTask
    return celery


# perform the search
# note the decorator -- you need this for any celery task
# @current_app.task()
@shared_task()
def search(cmd, tempdir, db_size):

        progressfile = open(os.path.join(tempdir, 'progress'), "w+")

        process = subprocess.Popen(cmd,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   stdin=subprocess.PIPE)
        out = []
        err = []
        count = 0.0
        # process each line while running so we can get progress and monitor
        while True:
            line = process.stdout.readline()
            if not line:
                break
            sline = line.strip()
            # check for progress, don't store visiting
            if re.search('Visiting', sline):
                count += 1
                progress = str(count / float(db_size))
                progressfile.write(progress)
                progressfile.flush()
            # check for error -- master returns true regardless if it hits an error...
            elif re.search('Error:', sline):
                err.append(sline)
            else:
                out.append(sline)
            sys.stdout.flush()
        err += process.stderr.readlines()  # append any stderr to stdout "Errors"
        if err:
            pass
        # TODO: handle errors how?
