#!/usr/bin/env python
"""
the main master search functionality
author:   Tim Tregubov, 12/2014
author:   Gevorg Grigoryan, 08/2016
"""

import os
import tempfile
import subprocess
from werkzeug.utils import secure_filename
from rq import Queue
from redis import Redis
import Tasks
import re


defaults = {
    'rmsdCut': '1.5',
    'topN': '25',
    'outType': 'match',
    'bbRMSD':  True,
    'rmsdMode': '0',
    'tune': '0.5',
    'dEps': False,
    'phiEps': '180.0',
    'psiEps': '180.0',
    'ddZScore': '3.5'
}


class MasterSearch(ServerTask):
    """
    class that handles MASTER search requests
    """

    def process(self, request):
        """
        process the query
        """

        # --- do some error checking
        sanitized = Checks.sanitize_args(request.form)

        # check args
        (is_allowed, not_allowed_list) = Checks.allowed_args(request.form)
        if not is_allowed:
            return None, 'bad parameters: ' + ', '.join(not_allowed_list)

        # check query file
        if len(request.files) == 1 and 'query' in request.files:
            query_file = request.files['query']
            database = str(sanitized['database'])
            if Checks.allowed_file(query_file.filename):
                print("found query_file: " + str(query_file))
            else:
                return None, 'bad query file!'
        else:
            return None, 'no query file!'

        # start processing the search query
        error = None
        search_job = None
        self.tempdir = tempfile.mkdtemp(dir=self.app.config['PROCESSING_PATH'])
        query_filepath = os.path.join(tempdir, secure_filename(query_file.filename))
        sequence = ''
        self.progressfile = os.path.join(self.tempdir, 'progress')
        try:
            # save file
            query_file.save(query_filepath)
            pdsfile = self.pdb2pds(query_filepath)
            search_job = self.qsearch(pdsfile, database, arguments)
            sequence = self.sequenceFromPDB(query_filepath)
        except Exception as e:
            print("processing failed: ", e)
            return None, str(e)

        # cleanup all files
        # shutil.rmtree(tempdir, ignore_errors=True)
        # TODO: need to clean up the above somewhere later
        return [('job', search_job), ('tempdir', tempdir), ('sequence', sequence)], ''

    def progress(self):
        while True:
            time.sleep(1)
            if search_job.is_failed:
                yield json.dumps({'error': 'failed'})
            elif search_job.get_status() != 'finished':  # keep sending progress update
                try:
                    yield json.dumps({'progress': open(progressfile, 'r').readline()})
                except Exception as e:
                    yield json.dumps({'error': e.message})

            # finished finding matches, send the fileid to the client
            else:
                if re.search('ERROR', search_job.return_value):
                    yield json.dumps({'error': search_job.return_value.replace("ERROR:", "")})

                matches = []
                structdir = os.path.join(tempdir, "struct")
                for f in os.listdir(structdir):
                    if f.endswith(".pdb"):
                        filepath = os.path.join(structdir, f)
                        str_file = str(open(filepath).read())
                        compressed_file = zlib.compress(str_file, 5)
                        encoded_file = base64.standard_b64encode(compressed_file)
                        matches.append(encoded_file)
                yield json.dumps({'results': search_job.result,
                                  'tempdir': tempdir,
                                  'message': 'will be available for 24 hours',
                                  'matches': matches,
                                  'qSeq': qSeq})
                # TODO: implement cleaning up files
                break

    def sequenceFromPDB(self, pdbfilepath):
        """
        get a formatted sequence string from the PDB file
        """
        cmd = [self.app.config['SCRIPTS_PATH']+'/getSeq', pdbfilepath]
        print("getting query sequence: " + ' '.join(cmd))
        seqStr, err = self.runCommand(cmd, "could not extract sequence from query PDB file")
        return seqStr
       

    def pdb2pds(self, pdbfilepath):
        """
        convert pdb to pds format
        """
        # if already a pds do nothing
        ext = os.path.splitext(pdbfilepath)[1]
        if ext == '.pds' or ext == 'pds':
            return pdbfilepath

        pdsfilename = pdbfilepath.replace('.pdb', '.pds')
        cmd = [self.app.config['CREATEPDS_PATH'], '--type', 'query', '--pdb', pdbfilepath, '--pds', pdsfilename]
        print("attempting to convert: " + ' '.join(cmd))
        self.runCommand(cmd, "could not create PDS file from the query PDB file")
        return pdsfilename

    def runCommand(self, cmd, errMessBase):
        try:
            p = subprocess.Popen(cmd,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 stdin=subprocess.PIPE)
            out, err = p.communicate()
            # check for error
            if re.search('Error:', out):
                # might not return -1 so check for text here
                err += out
            if err:
                raise Exception(err)
            return out, err
        except Exception as e:
            raise Exception(errMessBase + "\ncommand: " + cmd + "\n" + e.message)

    def qsearch(self, query_filepath, database, arguments):
        """
        perform the search
        """

        print("OPTIONS" + str(arguments))
        # required arguments
        tempdir, qfile = os.path.split(query_filepath)
        # prefix, ext = os.path.splitext(qfile)
        match_out = os.path.join(tempdir, 'matches')
        seq_out = os.path.join(tempdir, 'seq')
        struct_out = os.path.join(tempdir, 'struct')
        rmsd_cut = arguments['rmsdCut'] if 'rmsdCut' in arguments else defaults['rmsdCut']
        top_n = arguments['topN'] if 'topN' in arguments else defaults['topN']
        out_type = arguments['outType'] if 'outType' in arguments else defaults['outType']

        cmd = [self.app.config['MASTER_PATH'],
               '--query', query_filepath,
               '--targetList', os.path.join(self.app.config['CONFIG_PATH'], database),
               '--rmsdCut', rmsd_cut,
               '--matchOut', match_out,
               '--seqOut', seq_out,
               '--topN', top_n,
               '--structOut', struct_out,
               '--outType', out_type]

        if 'bbRMSD' in arguments:
          cmd.append('--bbRMSD')

        self.db_size = sum(1 for line in open(os.path.join(self.app.config['CONFIG_PATH'], database)) if line.rstrip())
        job = self.rq.enqueue_call(Tasks.search, args=(cmd, self.app.config['PROCESSING_PATH'], tempdir, self.db_size), timeout=3600)

        return job

if __name__ == "__main__":
    pass
