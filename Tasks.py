#!/usr/bin/env python
"""
breaks out the processes that are run asynchronously into its own file
author:   Tim Tregubov, 12/2014
"""


import os
import re
import subprocess
import sys


def search(cmd, basedir, tempdir, db_size):
    """
    perform the search
    this is a long running process best called asynchronously via rq
    """
    progressfile_path = os.path.join(tempdir, 'progress')
    progressfile = open(progressfile_path, "w+")
    fileid = os.path.basename(os.path.normpath(tempdir)).strip()

    tardir = os.path.join(basedir, 'compressed/')
    if not os.path.exists(tardir):
        os.makedirs(tardir)
    tarname = fileid+".tar.gz"

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
            progressfile.seek(0)
            progressfile.write(progress+"\n")
            progressfile.truncate()
            progressfile.flush()
        # check for error -- master returns true regardless if it hits an error...
        elif re.search('Error:', sline):
            err.append(sline)
        else:
            out.append(sline)
        sys.stdout.flush()
    err += process.stderr.readlines()  # append any stderr to stdout "Errors"

    # compress the resultsdir
    compress_cmd = ['/usr/bin/tar', '-C', tardir, '-cf', tarname, os.path.join(basedir, fileid)]
#    compress_cmd = ['/usr/bin/tar', '-C', basedir, '-czf', os.path.join(basedir, tarname), fileid]
    compress_process = subprocess.Popen(compress_cmd,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        stdin=subprocess.PIPE)
    c_out, c_err = compress_process.communicate()

    if c_err and not re.search('Removing', c_err):
        err.append(str(c_err))

    # return the fileid once all done processing
    if err:
        return 'ERROR: ' + ','.join(err)
    else:
        return fileid
    # TODO: handle errors better here
