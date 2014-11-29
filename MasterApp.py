#!/usr/bin/env python
# flask app for master
#

from flask import Flask, jsonify, request, render_template
from flask import redirect, url_for, send_from_directory
from MasterSearch import *
import Tasks

app = Flask(__name__)
app.config.from_object('Settings.Default')
celery = Tasks.make_celery(app)
masterSearch = MasterSearch(app)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


def allowed_args(list_of_args):
    # checks if list is allowed
    # returns: (bool isAllowed, listOfNotAllowed)
    argset = set(list_of_args)
    issubset = argset <= app.config['ALLOWED_ARGS']
    intersection = argset - app.config['ALLOWED_ARGS']
    return issubset, intersection

# routes
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
    (is_allowed, not_allowed_list) = allowed_args(request.form)
    if not is_allowed:
        return jsonify({'error': 'bad parameters: ' + ', '.join(not_allowed_list)})

    # check query file
    if len(request.files) == 1 and 'query_file' in request.files:
        query_file = request.files['query_file']
        if allowed_file(query_file.filename):
            print("found query_file: " + str(query_file))
        else:
            return jsonify({'error': 'bad query file!'}), 201
    else:
        return jsonify({'error': 'no query file!'}), 201

    results = masterSearch.process(query_file, request.form)

    return jsonify({'progress': '1', 'results': results}), 201
    # return redirect(url_for('uploaded_file',
    #                         filename=filename))

# an image, that image is going to be show after the upload
@app.route('/api/search/<filename>')
def processed_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)



if __name__ == "__main__":
    app.run(debug=True)
