#!/usr/bin/env python

import os
import re
import sys
import tempfile
import subprocess
import shutil
from werkzeug import secure_filename
from celery import current_app
import Tasks

defaults = {
    'rmsdCut': '1.5',
    'topN': '25'
}


class MasterSearch(object):

    db_size = 0
    app = None

    def __init__(self, app):
        # could do things like load the database into memory or setup caching etc
        self.db_size = sum(1 for line in open(app.config['TARGET_LIST_PATH']) if line.rstrip())
        self.app = app
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
            results = self.search(pdsfile)

        except Exception as e:
            print("processing failed: " + e.message)

        # cleanup all files
        # shutil.rmtree(tempdir, ignore_errors=True)
        # TODO: need to clean up the above somewhere later
        return results

    # convert pdb to pds format
    def pdb2pds(self, pdbfilepath):
        # if already a pds do nothing
        if os.path.splitext(pdbfilepath)[1] == 'pds':
            return pdbfilepath

        pdsfilename = pdbfilepath.replace('.pdb', '.pds')
        try:
            cmd = [self.app.config['CREATEPDS_PATH'], '--type', 'query', '--pdb', pdbfilepath, '--pds', pdsfilename]
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE)
            out, err = p.communicate()
            # check for error
            assert(not err)
            return pdsfilename
        except Exception as e:
            raise Exception("couldn't convert file from pdb2pds: " + e.message)

    # perform the search
    def search(self, query_filepath, options={}):

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

        result = Tasks.search.delay(cmd, tempdir, self.db_size)
        result.wait()

        return ""
