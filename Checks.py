"""
some sanity checks
author:   Tim Tregubov, 12/2014
"""

from werkzeug.utils import secure_filename
# app is injected in here later ignore errors


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


def sanitize_args(arg_dict):
    # TODO: should we catch and return errors or just fix and move on
    # secure_filename does basically what we need
    return {secure_filename(k).strip(): secure_filename(v).strip() for k, v in arg_dict.iteritems()}