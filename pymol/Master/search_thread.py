
from pymol.wizard import Wizard
from pymol import cmd
import threading
import json
import socket
import tkSimpleDialog
import tkMessageBox
import sys
import pymol
from Tkinter import *

import tkSimpleDialog
import tkMessageBox
import sys
import urllib2
import zlib
import pycurl
import base64
import subprocess
from StringIO import StringIO
import traceback



class SearchThread(threading.Thread):
    def __init__(
            self, rmsd, num_struct, full_matches, pdbstrs, url, thecmd):
        """
        This is the constructor for our SearchThread.  Each time we perform
        a structural search, a new thread will be created.
        """
        threading.Thread.__init__(self)

        self.databuffer = StringIO()

        self.rmsd_cutoff    = rmsd
        self.num_structures = num_struct
        self.full_matches   = full_matches
        self.query          = pdbstrs

        # PyMOL routines keep their own copy of the 'cmd' object why?
        self.cmd = thecmd

        self.url = url  # Currently selected host
        self.match_id = ''
        self.conn = None

        self.concurrency_management = {'begun': False,  # True once the thread begins consuming
                                       'ended': False,  # True once the thread finishes consuming
                                       'lock': threading.Lock()}  # This guards the 'begun' and 'end' variables

        # def remote(pdb_code):
#     pdb_code = pdb_code.upper()
#     try:
#         pdbFile = urllib2.urlopen('http://www.rcsb.org/pdb/cgi/export.cgi/' +
#                                   pdb_code + '.pdb.gz?format=PDB&pdbId=' +
#                                   pdb_code + '&compression=gz')
#         cmd.read_pdbstr(zlib.decompress(pdbFile.read()[22:], -zlib.MAX_WBITS), pdb_code)
#     except Exception as e:
#         print "Unexpected error:", e.message
#         tkMessageBox.showerror('Invalid Code',
#                                'You entered an invalid pdb code:' + pdb_code)


    # callback for processing data
    def on_receive(self, streamdata):
        try:
            jsondata = json.loads(streamdata)
            if 'progress' in jsondata:
                print('progress: ' + jsondata['progress'].strip())
            else:
                self.databuffer.write(streamdata.strip())
                # we just append cause this could be multiple packets
            # if 'results' in jsondata:
            #     self.match_id = jsondata['results'].strip()
            #     if 'matches' in jsondata:
            #         for index, match in enumerate(jsondata['matches']):
            #             unencoded = base64.decodestring(match)
            #             uncompressed = zlib.decompress(unencoded)
            #             print('decoded file header: ' + uncompressed.splitlines()[0])
            #             matches.append(uncompressed)
            #             self.cmd.read_pdbstr(str(uncompressed), self.match_id)  # +"_"+index)
            #             # self.pdbs[pdbid] += 1
            #     # print('results: ' + json.dumps(jsondata['results'], sort_keys=True, indent=4))
            #     # print('initiating download...')
            #     # self.download(fileid)
        except ValueError:
            self.databuffer.write(streamdata.strip())
            # for valueerror we just append cause this could be multiple packets
        except Exception as e:
            print('error processing response: ' + e.message + "\nrawdata: " + str(streamdata))

        # # If there is an existing result of the same name, delete it,
        # # otherwise PyMOL will load the new result as an additional
        # # model to the existing result.
        # self.cmd.delete(self.match_id)
        #
        # # Load the structure into pymol.
        # self.cmd.read_pdbstr(body[5:], sele_name)
        # curr_group_name = self.group_name + '_' + RESULT_SUFFIX
        # self.cmd.group(curr_group_name, sele_name)
        # self.cmd.group(self.group_name, curr_group_name)        #

    # Send a search request and await results
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

            # import StringIO
            # import uu
            #
            # def uu2string(data, mode=None):
            #     outfile = StringIO.StringIO()
            # infile = StringIO.StringIO(data)
            # uu.decode(infile, outfile, mode)
            # return outfile.getvalue()

            # contents = 'hello, world!'
            #    send = [
            #        ('field2', (pycurl.FORM_BUFFER, 'uploaded.file', pycurl.FORM_BUFFERPTR, contents)),
            #    ]
            # make connection

            self.conn = pycurl.Curl()
            self.conn.setopt(pycurl.URL, self.url)
            self.conn.setopt(pycurl.FOLLOWLOCATION, 1)
            self.conn.setopt(pycurl.MAXREDIRS, 5)
            self.conn.setopt(pycurl.POST, 1)

            #             ziped = sio()
            # with gzip.GzipFile(fileobj=ziped, mode='w') as f:
            #     f.write(xml_content)
            # run_data = ziped.getvalue()

            print("pdbs: " + str(self.query))

            data = [
                ("topN", str(self.num_structures)),
                ("query", (pycurl.FORM_BUFFER, 'sele.pdb', pycurl.FORM_BUFFERPTR, self.query))
            ]
            self.conn.setopt(pycurl.HTTPPOST, data)

            # this runs the callpack every time we get new data
            self.conn.setopt(pycurl.WRITEFUNCTION, self.on_receive)
            self.conn.perform()

            #  now we parse our databuffer
            # once we're done check the stringbuffer for the complete json matches
            try:
                jsondata = json.loads(self.databuffer.getvalue())
                if 'results' in jsondata:
                    self.match_id = jsondata['results'].strip()
                    if 'matches' in jsondata:
                        for index, match in enumerate(jsondata['matches']):
                            unencoded = base64.standard_b64decode(match)
                            uncompressed = zlib.decompress(unencoded)
                            print('decoded file header: ' + uncompressed.splitlines()[0])
                            self.cmd.read_pdbstr(str(uncompressed), self.match_id)  # +"_"+index)
                            # self.pdbs[pdbid] += 1
            except Exception as e:
                print('error processing response: ' + e.message + "\nrawdata: " + str(self.databuffer.getvalue()))
                print(traceback.format_exc())

        except Exception as e:
            print("Trouble posting request: " + e.message)
            print(traceback.format_exc())

        finally:
            # once done set ended atomically
            self.concurrency_management['lock'].acquire()
            try:
                self.concurrency_management['ended'] = True
            finally:
                self.concurrency_management['lock'].release()

            #self.cmd.orient(SELECTION_NAME)

    def stop(self, message=''):
        """
        abort abort
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
