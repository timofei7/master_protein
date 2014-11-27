#!/usr/bin/env python

import os, re
import tempfile
import subprocess
import shutil
from werkzeug import secure_filename

baseDir = os.path.dirname(__file__)
master_path = os.path.join(baseDir, 'external/master/master')
createPDS_path = os.path.join(baseDir, 'external/master/createPDS')
extractPDB_path = os.path.join(baseDir, 'external/master/extractPDB')
processing_path = os.path.join(baseDir, 'processing')
library_path = os.path.join(baseDir, 'bc-30-sc-correct-20141022')
target_list_path = os.path.join(library_path, 'list')

defaults = {
    'rmsdCut': '1.5',
    'topN': '25'
}


class MasterSearch(object):

    def __init__(self):
        # could do things like load the database into ram here
        # thats why this is a class, for now do nothing
        pass

    def process(self, query_file, arguments):
        results = None
        tempdir = tempfile.mkdtemp(dir=processing_path)
        query_filepath = os.path.join(tempdir, secure_filename(query_file.filename))
        try:
            # save file
            query_file.save(query_filepath)
            pdsfile = self.pdb2pds(query_filepath)
            results = self.search(pdsfile)

        except Exception as e:
            print("processing failed: " + e.message)

        #cleanup all files
        shutil.rmtree(tempdir, ignore_errors=True)
        return results

    # convert pdb to pds format
    def pdb2pds(self, pdbfilepath):
        # if already a pds do nothing
        if os.path.splitext(pdbfilepath)[1] == 'pds':
            return pdbfilepath

        pdsfilename = pdbfilepath.replace('.pdb', '.pds')
        try:
            cmd = [createPDS_path, '--type', 'query', '--pdb', pdbfilepath, '--pds', pdsfilename]
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
        try:
            cmd = [master_path,
                   '--query', query_filepath,
                   '--targetList', target_list_path,
                   '--rmsdCut', rmsd_cut,
                   '--matchOutFile', match_out,
                   '--seqOutFile', seq_out,
                   '--topN', top_n,
                   '--structOut', struct_out]
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 stdin=subprocess.PIPE)
            out, err = p.communicate()
            print('out: ' + out)
            if re.match('Error:', out):
                err += out
            # check for error
            if err:
                raise Exception(err)
            return seq_out, struct_out, match_out
        except Exception as e:
            raise Exception("search failed! " + e.message)

def main():
    masterSearch = MasterSearch()
# if run standalone
if __name__ == '__main__':
    main()
