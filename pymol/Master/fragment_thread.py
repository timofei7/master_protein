#!/usr/bin/env python
"""
thread for finding fragment to stitch
between n and c termini
First part of Fuser application
"""


import threading
import json
from Tkinter import *
import zlib
import pycurl
import base64
from StringIO import StringIO
import traceback
from constants import *
from server_thread import *
from fuser import *

class FragmentThread(ServerThread):
    """
    search thread allows the ui to remain responsive while this sends off the search request and waits
    """

    def __init__(self, wiz, pdbstr, rmsd, num_struct, full_matches, database, range_max, range_min, serverURL, thecmd, dictionary, pdbstr_n = None, pdbstr_c = None):
 
        self.dictionary = dictionary
        self.wizard         = wiz
        self.cmd = thecmd
        self.graft_id = self.new_group_name()

        data = [
                ("rangeMax", str(range_max)),
                ("rangeMin", str(range_min)),

                ("topN", str(num_struct)),
                ("outType", "match" if not full_matches else "full"),
                ("database", str(database)),
                ("query", (pycurl.FORM_BUFFER, 'sele.pdb', pycurl.FORM_BUFFERPTR, pdbstrs)),
                ("bbRMSD", "on"),
                ("rmsdCut", str(rmsd))
               ]

        super(FragmentThread, self).__init__(serverURL + '/api/StageOneFuser', data)


    def new_group_name(self):
        """
        This method returns a string for a new PyMOL object name to be used
        for storing the latest search results
        """
        name = ''
        for k in range(1, 1001):
            name = 'graft%02d' % (k)
            if (not (name in self.cmd.get_names())):
                break
        return name


    # --------------- Overridden functions from base class --------------- #
    def progress_handler(self, progs):
        self.wizard.set_searchProgress(float(progs))

    def error_handler(self, mess):
        self.wizard.set_status('Error: ' + mess)

    def results_handler(self, jsondata):
        numMatches = 0
        if 'results' in jsondata:
            if 'qSeq' in jsondata:
                self.wizard.popup_app.win.qSeqs[self.graft_id] = str(jsondata['qSeq'])
            if 'matches' in jsondata:
                for index, match in enumerate(jsondata['matches']):
                    # uncompress and decode matches
                    unencoded = base64.standard_b64decode(match)
                    uncompressed = zlib.decompress(unencoded)
                    header = uncompressed.splitlines()[0]
                    phid = re.search('/(.*?).pds', header).group(1).split('/')
                    hid = phid[len(phid)-1] + '.' + str(index)
                    print('found: ' + hid + ' ' + header.split('pds')[1])

                    # load the pdb and group
                    self.cmd.read_pdbstr(str(uncompressed), hid)
                    self.cmd.group(self.graft_id, hid)
                    numMatches = numMatches + 1

                self.dictionary[self.graft_id] = str(jsondata['tempdir']).split('/')[-1]

        # add current search to search history
        self.setReturn(numMatches)
        if (numMatches):
            self.cmd.get_wizard().fuser_app.add_new_graft(self.graft_id)

    def on_finish(self, numMatches):
        self.wizard.fuser_app.complete_search(numMatches)

    # -------- End of overridden functions from base class --------------- #
