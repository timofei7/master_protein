#!/usr/bin/env python
"""
testing file for masterapp showing how to send it a file and retrieve progress
and the file itself
"""


import pycurl, json, subprocess

URL = "http://127.0.0.1:5000/api/search"


def download(fileid):
    subprocess.call(['curl', URL+'/'+fileid, '-o', fileid+'.tar.gz'])


# callback for processing data
def on_receive(streamdata):
    try:
        jsondata = json.loads(streamdata)
        if 'progress' in jsondata:
            print('progress: ' + jsondata['progress'].strip())
        if 'results' in jsondata:
            print('results: ' + json.dumps(jsondata['results'], sort_keys=True, indent=4))
            fileid = jsondata['results'].strip()
            print('initiating download...')
            download(fileid)
    except Exception as e:
        print('error processing response: ' + e.message + "\nrawdata: " + str(streamdata))

conn = pycurl.Curl()
conn.setopt(pycurl.URL, URL)
conn.setopt(pycurl.FOLLOWLOCATION, 1)
conn.setopt(pycurl.MAXREDIRS, 5)

conn.setopt(pycurl.POST, 1)
data = [
    ("query", "just a test string"),
    ("query_file", (pycurl.FORM_FILE, "sele.pds"))
]
conn.setopt(pycurl.HTTPPOST, data)

# this runs the callpack every time we get new data
conn.setopt(pycurl.WRITEFUNCTION, on_receive)
conn.perform()

