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

    def __init__(self, _url, _data):

        threading.Thread.__init__(self)
        self.databuffer = StringIO()
        self.url = _url
        self.data = _data
        self.returnObj = None
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
                    self.progress_handler(progs)
            elif 'error' in jsondata:
                self.error_handler(jsondata['error'])
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

    def results_handler(self, jasondata):
        """
           This method should be overridden by the parent class if
           you want anything intelligent done with progress messages
        """
        print "results_handler: don't know how to process results, this method must be overridden"

    def progress_handler(self, mess):
        """
           This method should be overridden by the parent class if
           you want anything intelligent done with progress messages
        """
        print "progress report: %s", mess
        print "override this method to act upon this progress"

    def error_handler(self, mess):
        """
           This method should be overridden by the parent class if
           you want anything intelligent done with error messages
        """
        print "error: %s", mess
        print "override this method to act upon this error"

    def on_finish(self, returnObj):
        """
           This method gets called right after the thread is about done.
           Override this method if you want anything intelligent to happen.
        """
        return True

    def setReturn(self, ret):
        """
        Prepare info for return from thread.
        """
        self.returnObj = ret
        
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

            self.conn.setopt(pycurl.HTTPPOST, self.data)

            # this runs the callback every time we get new data
            self.conn.setopt(pycurl.WRITEFUNCTION, self.on_receive)
            self.conn.perform()

            if not self.error:
                # now we parse our databuffer
                # once we're done check the stringbuffer for the complete json matches
                try:
                    jsondata = json.loads(self.databuffer.getvalue())
                    self.results_handler(jsondata)
                except Exception as e:
                    print('error processing response: ', e, "\nrawdata: " + str(self.databuffer.getvalue()))
                    print(traceback.format_exc())

                self.on_finish(self.returnObj)

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


