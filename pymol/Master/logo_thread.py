#!/usr/bin/env python
"""
logo thread for the pymol master plugin
uses pycurl to connect to a remote server
and requests sequence logo

author: Nick Fiacco, 6/2015, using structure of search_thread.py from Tim Tregubov
"""


import threading
import json
import pycurl
import base64
from StringIO import StringIO
from constants import *
import traceback
from server_thread import *

class LogoThread(ServerThread):
    """
    logo thread allows the ui to remain responsive while this sends off the logo request and waits
    """

    def __init__(self, search_id, flag, url, cmd, logo_filepath = None, extension = "gif"):
        self.query          = search_id.strip()
        self.flag           = flag
        self.cmd            = cmd
        self.logo_filepath  = logo_filepath  # defalut value is None, will be set based on query name
        self.extension      = extension
        data = [
                ('query', self.query),
                ('flag', str(self.flag)),
                ('rmsdCut', "999"),
                ('ext', self.extension)
        ]
        super(LogoThread, self).__init__(url, data)

    # --------------- Overridden functions from base class --------------- #
    def error_handler(self, mess):
        self.wizard.set_status('Error: ' + mess)
    
    def results_handler(self, jsondata):
        if 'logo' in jsondata:
            unencoded = base64.standard_b64decode(jsondata['logo'])
                
        if self.logo_filepath == None:
            if self.flag == 1:
                logo_filepath = LOGO_CACHE + str(self.query)+'s.gif'
            elif self.flag == 2:
                logo_filepath = LOGO_CACHE + str(self.query)+'f.gif'
            else:
                logo_filepath = self.logo_filepath
            
            # write to the specified filepath
            print "trying to write %s..." % logo_filepath
            logo_file = open(logo_filepath, 'wb')
            logo_file.write(unencoded)
            logo_file.close()

    # -------- End of overridden functions from base class --------------- #
