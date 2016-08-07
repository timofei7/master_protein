#!/usr/bin/env python
"""
    search thread for the pymol master plugin
    uses pycurl to connect to a remote server
    and uses a long running http pull to get processing updates
    this is because the processing is never really very long so this is sufficient
    uses http for simplicity and compatibility.
    authors:   Tim Tregubov, 12/2014
    Nick Fiacco 2016
    Ben Scammell 2016
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


class ServerThread(threading.Thread):
    """
        search thread allows the ui to remain responsive while this sends off the search request and waits
        """

    def __init__(self, type):

        threading.Thread.__init__(self)
        self.databuffer = StringIO()
        self.thread_type = type


        # Search thread variables
        if self.thread_type[0] == 1:

            self.type = 'search'
            self.wizard = self.thread_type[1]
            self.rmsd_cutoff = self.thread_type[2]
            self.num_structures = self.thread_type[3]
            self.full_matches   = self.thread_type[4]
            self.database = self.thread_type[5]
            self.query = self.thread_type[6]
            self.url = self.thread_type[7]
            self.cmd = self.thread_type[8]
            self.dictionary = self.thread_type[9]
            self.match_id = ''

        # Search thread variables
        if self.thread_type[0] == 2:

            self.type = 'logo'
            self.rmsd_cutoff = self.thread_type[1]
            self.query = self.thread_type[2].strip()
            self.flag = self.thread_type[3]
            self.url = self.thread_type[4]
            self.cmd = self.thread_type[5]
            self.seqs = []

            if len(self.thread_type) > 6:
                self.logo_filepath = self.thread_type[6]  # defalut value is None, will be set based on query name
                self.extension = self.thread_type[7]

            else:
                self.logo_filepath = None
                self.extension = "gif"


        self.conn = None
        self.error = None


        self.concurrency_management = {'begun': False,  # True once the thread begins consuming
                                       'ended': False,  # True once the thread finishes consuming
                                       'lock': threading.Lock()}  # This guards the 'begun' and 'end' variables


    def on_receive(self, streamdata):
        """
            callback for processing data
            """
        try:
            jsondata = json.loads(streamdata)
            if 'progress' in jsondata:
                if not jsondata['progress'] == "":
                    progs = jsondata['progress'].strip()
                    #print("processing: {0:.0%}".format(float(progs)))
                    self.wizard.set_searchProgress(float(progs))
            elif 'error' in jsondata:
                #raise Exception(jsondata['error'])
                self.wizard.set_errorMessage(jsondata['error'])
                self.wizard.set_status('MASTER error')
            else:
                self.databuffer.write(streamdata.strip())
                # append to databuffer cause sometimes packets for results span multiple calls
        except ValueError:
            self.databuffer.write(streamdata.strip())
            # for valueerror we just append cause this could be multiple packets
        except Exception as e:
            # stop on error
            self.error = 'error processing response: ', e
            return -1  # will trigger a close

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

    def run(self):
        """
            This method will send the search request to the server
            """

        try:

            # set begun atomically
            self.concurrency_management['lock'].acquire()
            try:
                self.concurrency_management['begun'] = True
            finally:
                self.concurrency_management['lock'].release()

            # setup pycurl connection to server
            self.conn = pycurl.Curl()
            self.conn.setopt(pycurl.URL, self.url)
            self.conn.setopt(pycurl.FOLLOWLOCATION, 1)
            self.conn.setopt(pycurl.MAXREDIRS, 5)
            self.conn.setopt(pycurl.POST, 1)
            self.conn.setopt(pycurl.CONNECTTIMEOUT, 1200)
            self.conn.setopt(pycurl.TIMEOUT, 1200)
            self.conn.setopt(pycurl.NOSIGNAL, 1)

            # create a new unique ID
            if self.type == 'search':
                self.match_id = self.new_group_name();

            # create JSON data object
            # for search
            if self.type == 'search':
                data = [
                                             ("topN", str(self.num_structures)),
                                             ("outType", "match" if not self.full_matches else "full"),
                                             ("database", str(self.database)),
                                             ("query", (pycurl.FORM_BUFFER, 'sele.pdb', pycurl.FORM_BUFFERPTR, self.query)),
                                             ("bbRMSD", "on"),
                                             ("rmsdCut", str(self.rmsd_cutoff))
                                         ]

            #or for logo thread
            if self.type == 'logo':
                data = [
                                                 ('query', self.query),
                                                 ('flag', str(self.flag)),
                                                 ('rmsdCut', "999"),
                                                 ('ext', self.extension)
                                                 ]

            self.conn.setopt(pycurl.HTTPPOST, data)

            # this runs the callback every time we get new data
            self.conn.setopt(pycurl.WRITEFUNCTION, self.on_receive)
            self.conn.perform()

            if not self.error:
                # now we parse our databuffer
                # once we're done check the stringbuffer for the complete json matches
                try:
                    jsondata = json.loads(self.databuffer.getvalue())
                    if 'results' in jsondata:

                        # For search thread
                        if 'qSeq' in jsondata:
                            self.wizard.qSeqs[self.match_id] = str(jsondata['qSeq'])
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

                            self.dictionary[self.match_id] = str(jsondata['tempdir']).split('/')[-1]

                            # add current search to search history
                            self.cmd.get_wizard().add_new_search(self.match_id)

                        # For logo thread
                        if 'logo' in jsondata:
                            unencoded = base64.standard_b64decode(jsondata['logo'])

                            if self.logo_filepath == None:
                                if self.flag == 1:
                                    logo_filepath = LOGO_CACHE + str(self.query) + 's.gif'
                                elif self.flag == 2:
                                    logo_filepath = LOGO_CACHE + str(self.query) + 'f.gif'
                            else:
                                logo_filepath = self.logo_filepath

                            # write to the specified filepath
                            print "trying to write %s..." % logo_filepath
                            logo_file = open(logo_filepath, 'wb')
                            logo_file.write(unencoded)
                            logo_file.close()



                except Exception as e:
                    print('error processing response: ', e, "\nrawdata: " + str(self.databuffer.getvalue()))
                    print(traceback.format_exc())

                if self.type == 'search':
                    self.wizard.complete_search()

        except Exception as e:
            # check for self.error as that would contain certain types of errors that weren't exceptions
            if self.error:
                print("Trouble posting request: " + self.error)
            else:
                print("Trouble posting request: " + e.message)
                print(traceback.format_exc())

        finally:
            # once done set ended atomically
            self.concurrency_management['lock'].acquire()
            try:
                self.concurrency_management['ended'] = True
            finally:
                self.concurrency_management['lock'].release()


    def stop(self, message=''):
        """
            abort abort!
            """
        self.concurrency_management['lock'].acquire()
        try:
            if not self.concurrency_management['ended']:
                if self.concurrency_management['begun']:
                    try:
                        self.conn.close()
                    except Exception as e:
                        print("ran into trouble closing the connection: " + e.message)
                self.concurrency_management['ended'] = True
        finally:
            self.concurrency_management['lock'].release()
            if message != '':
                print message


    # def cacheData(self):