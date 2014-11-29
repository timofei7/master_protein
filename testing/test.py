#!/usr/bin/env python

import pycurl, json
from urllib import urlencode

URL = "http://127.0.0.1:5000/api/search"

# callback for processing data
def on_receive(streamdata):
    try:
        jsondata = json.loads(streamdata)
        if 'progress' in jsondata:
            print('got progress: ' + jsondata['progress'])
        if 'results' in jsondata:
            print('got results: ' + json.dumps(jsondata['results'], sort_keys=True, indent=4))
    except Exception as e:
        print('error processing response: ' + e.message)

conn = pycurl.Curl()
conn.setopt(pycurl.URL, URL)

conn.setopt(pycurl.POST, 1)
data = [
    ("query", "just a test string"),
    ("query_file", (pycurl.FORM_FILE, "sele.pds"))
]
conn.setopt(pycurl.HTTPPOST, data)

# this runs the callpack every time we get new data
conn.setopt(pycurl.WRITEFUNCTION, on_receive)
conn.perform()

