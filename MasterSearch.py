#!/usr/bin/env python
"""
the main master search functionality
"""

import os
import tempfile
import subprocess
from werkzeug import secure_filename
from rq import Queue
from redis import Redis
import Tasks


defaults = {
    'rmsdCut': '1.5',
    'topN': '25'
}


class MasterSearch(object):

    app = None
    db_size = 0

    def __init__(self, app):
        # could do things like load the database into memory or setup caching etc
        self.db_size = sum(1 for line in open(app.config['TARGET_LIST_PATH']) if line.rstrip())
        self.app = app
        self.redis_conn = Redis()
        self.rq = Queue(connection=self.redis_conn)
        print('init with db size: ' + str(self.db_size))

        # process the query
    def process(self, query_file, arguments):
        results = None
        tempdir = tempfile.mkdtemp(dir=self.app.config['PROCESSING_PATH'])
        query_filepath = os.path.join(tempdir, secure_filename(query_file.filename))
        try:
            # save file
            query_file.save(query_filepath)
            pdsfile = self.pdb2pds(query_filepath)
            search_job = self.qsearch(pdsfile)

        except Exception as e:
            print("processing failed: " + e.message)

        # cleanup all files
        # shutil.rmtree(tempdir, ignore_errors=True)
        # TODO: need to clean up the above somewhere later
        return search_job, tempdir

    # convert pdb to pds format
    def pdb2pds(self, pdbfilepath):
        # if already a pds do nothing
        ext = os.path.splitext(pdbfilepath)[1]
        if ext == '.pds' or ext == 'pds':
            return pdbfilepath

        pdsfilename = pdbfilepath.replace('.pdb', '.pds')
        try:
            cmd = [self.app.config['CREATEPDS_PATH'], '--type', 'query', '--pdb', pdbfilepath, '--pds', pdsfilename]
            p = subprocess.Popen(cmd,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 stdin=subprocess.PIPE)
            out, err = p.communicate()
            # check for error
            if err:
                raise Exception(err)
            return pdsfilename
        except Exception as e:
            raise Exception("couldn't convert file from pdb2pds: " + e.message)

    # perform the search
    def qsearch(self, query_filepath, options={}):

        tempdir, qfile = os.path.split(query_filepath)
        prefix, ext = os.path.splitext(qfile)
        match_out = os.path.join(tempdir, prefix+'.match')
        seq_out = os.path.join(tempdir, prefix+'.seq')
        struct_out = os.path.join(tempdir, prefix+'.struct')
        rmsd_cut = options['rmsdCut'] if 'rmsdCut' in options else defaults['rmsdCut']
        top_n = options['topN'] if 'topN' in options else defaults['topN']

        cmd = [self.app.config['MASTER_PATH'],
               '--query', query_filepath,
               '--targetList', self.app.config['TARGET_LIST_PATH'],
               '--rmsdCut', rmsd_cut,
               '--matchOutFile', match_out,
               '--seqOutFile', seq_out,
               '--topN', top_n,
               '--structOut', struct_out]

        job = self.rq.enqueue(Tasks.search, cmd, self.app.config['PROCESSING_PATH'], tempdir, self.db_size)

        return job

if __name__ == "__main__":
    pass
