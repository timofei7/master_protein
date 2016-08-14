#!/usr/bin/env python
"""
search thread for the pymol master plugin
uses pycurl to connect to a remote server
and uses a long running http pull to get processing updates
this is because the processing is never really very long so this is sufficient
uses http for simplicity and compatibility.
author:   Tim Tregubov, 12/2014
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

class SearchThread(ServerThread):
    """
    search thread allows the ui to remain responsive while this sends off the search request and waits
    """

    def __init__(self, wiz, rmsd, num_struct, full_matches, database, pdbstrs, serverURL, thecmd, dictionary):

        self.dictionary = dictionary
        self.wizard         = wiz
        self.cmd = thecmd
        self.match_id = self.new_group_name()

        data = [
                ("topN", str(num_struct)),
                ("outType", "match" if not full_matches else "full"),
                ("database", str(database)),
                ("query", (pycurl.FORM_BUFFER, 'sele.pdb', pycurl.FORM_BUFFERPTR, pdbstrs)),
                ("bbRMSD", "on"),
                ("rmsdCut", str(rmsd))
               ]

        super(SearchThread, self).__init__(serverURL + '/api/search', data)


    def new_group_name(self):
        """
        This method returns a string for a new PyMOL object name to be used
        for storing the latest search results
        """
        name = ''
        for k in range(1, 1001):
            name = 'S%02d' % (k)
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
                self.wizard.popup_app.qSeqs[self.match_id] = str(jsondata['qSeq'])
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
                    self.cmd.group(self.match_id, hid)
                    numMatches = numMatches + 1

                self.dictionary[self.match_id] = str(jsondata['tempdir']).split('/')[-1]

        # add current search to search history
        self.setReturn(numMatches)
        if (numMatches):
                    self.cmd.get_wizard().add_new_search(self.match_id)

    def on_finish(self, numMatches):
        self.wizard.popup_app.complete_search(numMatches)

    # -------- End of overridden functions from base class --------------- #
