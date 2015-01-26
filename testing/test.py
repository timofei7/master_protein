#!/usr/bin/env python
"""
testing file for masterapp showing how to send it a file and retrieve progress
and the file itself
author:   Tim Tregubov, 12/2014
"""


import pycurl
import json
import subprocess
import zlib
import base64
import traceback
from StringIO import StringIO


URL = "http://127.0.0.1:5000/api/search"

databuffer = StringIO()


def download(fileid):
    subprocess.call(['curl', URL+'/'+fileid, '-o', fileid+'.tar.gz'])


# callback for processing data
def on_receive(streamdata):
    try:
        jsondata = json.loads(streamdata)
        if 'progress' in jsondata:
            print('progress: ' + jsondata['progress'].strip())
        else:
            databuffer.write(streamdata.strip())
            # for matches we just append cause this could be multiple packets
    except ValueError:
        databuffer.write(streamdata.strip())
        # for valueerror we just append cause this could be multiple packets
    except Exception as e:
        print('error processing response: ' + e.message + "\nrawdata: " + str(streamdata))
        print(traceback.format_exc())

conn = pycurl.Curl()
conn.setopt(pycurl.URL, URL)
conn.setopt(pycurl.FOLLOWLOCATION, 1)
conn.setopt(pycurl.MAXREDIRS, 5)

conn.setopt(pycurl.POST, 1)
data = [
    ("topN", "5"),   # optional options
    ("bbRMSD", "True"),
    ("tune", "0.45"),
    ("phiEps", "182.0"),
    ("query", (pycurl.FORM_FILE, "sele.pdb"))  # this one is required
]
conn.setopt(pycurl.HTTPPOST, data)

# this runs the callpack every time we get new data
conn.setopt(pycurl.WRITEFUNCTION, on_receive)
conn.perform()
print "done getting data..."

# once we're done check the stringbuffer for the complete json matches
try:
    jsondata = json.loads(databuffer.getvalue())
    if 'matches' in jsondata:
        for match in jsondata['matches']:
            unencoded = base64.standard_b64decode(match)
            uncompressed = zlib.decompress(unencoded)
            print('decoded file header: ' + uncompressed.splitlines()[0])
except Exception as e:
    print('error processing response: ' + e.message + "\nrawdata: " + str(databuffer.getvalue()))
    print(traceback.format_exc())

