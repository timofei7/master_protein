#!/usr/bin/env python
"""
Flask App for MasterServer
see README.md for instructions on how to get this running
"""


from flask import Flask, jsonify, request, render_template
from flask import redirect, url_for, send_from_directory
from flask import Response
import json
import time
from MasterSearch import *
import zlib
import base64
import re

# set up the flask app
app = Flask(__name__)
app.config.from_object('Settings.Default')
masterSearch = MasterSearch(app)

import Checks
Checks.app = app

# routes #
@app.after_request
def after(response):
    return response

# default web route just returns an intro page
@app.route("/", methods=['GET', 'OPTIONS'])
def hello():
    return render_template('index.html')

# api route for submitting a search
@app.route("/api/search", methods=['POST', 'OPTIONS'])
def search():

    # check args
    (is_allowed, not_allowed_list) = Checks.allowed_args(request.form)
    if not is_allowed:
        return jsonify({'error': 'bad parameters: ' + ', '.join(not_allowed_list)})

    sanitized = Checks.sanitize_args(request.form)

    # check query file
    if len(request.files) == 1 and 'query' in request.files:
        query_file = request.files['query']
        if Checks.allowed_file(query_file.filename):
            print("found query_file: " + str(query_file))
        else:
            return jsonify({'error': 'bad query file!'}), 201
    else:
        return jsonify({'error': 'no query file!'}), 201

    # start processing the query and give us some progress

    search_job, tempdir, error = masterSearch.process(query_file, sanitized)
    if error:
        return jsonify({'error': error}), 201

    progressfile = os.path.join(tempdir, 'progress')

    # generator to provide updates and status to client
    def generate():
        while search_job.get_status() != 'finished':
            time.sleep(1)
            if search_job.is_failed:
                yield json.dumps({'error': 'failed'})
            elif search_job.get_status() != 'finished':  # keep sending progress update
                try:
                    yield json.dumps({'progress': open(progressfile, 'r').readline()})
                except Exception as e:
                    yield json.dumps({'error': e.message})
            else:
                if re.search('ERROR', search_job.return_value):
                    yield json.dumps({'error': search_job.return_value.replace("ERROR:", "")})

                matches = []
                structdir = os.path.join(tempdir, "struct")
                for f in os.listdir(structdir):
                    if f.endswith(".pdb"):
                        filepath = os.path.join(structdir, f)
                        str_file = str(open(filepath).read())
                        compressed_file = zlib.compress(str_file, 5)
                        encoded_file = base64.standard_b64encode(compressed_file)
                        matches.append(encoded_file)
                yield json.dumps({'results': search_job.result,
                                  'message': 'will be available for 24 hours',
                                  'matches': matches})
                # TODO: implement cleaning up files

    return Response(generate(),  mimetype='application/json')

# url to fetch results
@app.route("/api/search/<filename>", methods=['GET'])
def processed_file(filename):
    return send_from_directory(app.config['PROCESSING_PATH'],
                               filename+".tar.gz")


if __name__ == "__main__":
    app.run(debug=True, threaded=True)
