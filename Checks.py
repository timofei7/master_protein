"""
some sanity checks
"""

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
