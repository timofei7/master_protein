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
import sys


class MasterSearch(ServerTask):
    """
    class that handles MASTER search requests
    """

    def process(self, request):
        """
        process the query
        """

        # --- do some error checking
        arguments = Checks.sanitize_args(request.form)

        # check args
        (is_allowed, not_allowed_list) = Checks.allowed_args(request.form)
        if not is_allowed:
            return None, 'bad parameters: ' + ', '.join(not_allowed_list)

        # check query file
        if len(request.files) == 1 and 'query' in request.files:
            query_file = request.files['query']
            database = str(arguments['database'])
            if Checks.allowed_file(query_file.filename):
                print("found query_file: " + str(query_file))
            else:
                return None, 'bad query file!'
        else:
            return None, 'no query file!'

        # start processing the search query
        error = None
        tempdir = tempfile.mkdtemp(dir=self.app.config['PROCESSING_PATH'])
        query_filepath = os.path.join(tempdir, secure_filename(query_file.filename))
        sequence = ''
        self.progressfile = os.path.join(tempdir, 'progress')
        try:
            # save file
            query_file.save(query_filepath)
            pdsfile = self.pdb2pds(query_filepath)
            sequence = self.sequenceFromPDB(query_filepath)
        except Exception as e:
            print("processing failed: ", e)
            return None, str(e)

        # encode the call to MASTER
        match_out = os.path.join(tempdir, 'matches')
        seq_out = os.path.join(tempdir, 'seq')
        struct_out = os.path.join(tempdir, 'struct')
        rmsd_cut = arguments['rmsdCut'] if 'rmsdCut' in arguments else 1.0
        top_n = arguments['topN'] if 'topN' in arguments else 25
        out_type = arguments['outType'] if 'outType' in arguments else 'match'
        cmd = [self.app.config['MASTER_PATH'],
               '--query', pdsfile,
               '--targetList', os.path.join(self.app.config['CONFIG_PATH'], database),
               '--rmsdCut', rmsd_cut,
               '--matchOut', match_out,
               '--seqOut', seq_out,
               '--topN', top_n,
               '--structOut', struct_out,
               '--outType', out_type]
        if 'bbRMSD' in arguments:
          cmd.append('--bbRMSD')

        # enqueue job
        self.db_size = sum(1 for line in open(os.path.join(self.app.config['CONFIG_PATH'], database)) if line.rstrip())
        self.job = self.enqueue((cmd, self.app.config['PROCESSING_PATH'], tempdir, self.db_size))

        # cleanup old files somewhere
        # shutil.rmtree(tempdir, ignore_errors=True)

        return self.job, None

    def progress(self):
        while True:
            time.sleep(1)
            if self.job.is_failed:
                yield json.dumps({'error': 'failed'})
            elif self.job.get_status() != 'finished':  # keep sending progress update
                try:
                    yield json.dumps({'progress': open(progressfile, 'r').readline()})
                except Exception as e:
                    yield json.dumps({'error': e.message})

            # finished finding matches, send the fileid to the client
            else:
                if re.search('ERROR', self.job.return_value):
                    yield json.dumps({'error': self.job.return_value.replace("ERROR:", "")})

                matches = []
                structdir = os.path.join(tempdir, "struct")
                for f in os.listdir(structdir):
                    if f.endswith(".pdb"):
                        filepath = os.path.join(structdir, f)
                        str_file = str(open(filepath).read())
                        compressed_file = zlib.compress(str_file, 5)
                        encoded_file = base64.standard_b64encode(compressed_file)
                        matches.append(encoded_file)
                yield json.dumps({'results': self.job.result,
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

    @staticmethod
    def do(cmd, basedr, tempdir, db_size):
        """
        perform the search
        this is a long running process best called asynchronously via rq
        this is a static function
        """

        progressfile_path = os.path.join(tempdir, 'progress')
        progressfile = open(progressfile_path, "w+")
        fileid = os.path.basename(os.path.normpath(tempdir)).strip()

        tardir = os.path.join(basedir, '../compressed/')
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
        compress_cmd = ['/usr/bin/tar', '-cf', os.path.join(tardir, tarname), os.path.join(basedir, fileid)]

#        compress_cmd = ['/usr/bin/tar', '-C', basedir, '-czf', os.path.join(basedir, tarname), fileid]
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


if __name__ == "__main__":
    pass
