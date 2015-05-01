#!/usr/bin/env python
"""
Put settings here for various files necessary
author:   Tim Tregubov, 12/2014
"""

import os


class Default(object):
    """
    default settings for the server"
    """

    BASEDIR = os.path.dirname(__file__)

    # # # #  edit this section # # # #
    MASTER_PATH = os.path.join(BASEDIR, 'external/master/master')           #
    CREATEPDS_PATH = os.path.join(BASEDIR, 'external/master/createPDS')     #
    EXTRACTPDB_PATH = os.path.join(BASEDIR, 'external/master/extractPDB')   #
    PROCESSING_PATH = os.path.join(BASEDIR, 'processing')                   # directory to hold output files
    CONFIG_PATH = os.path.join(BASEDIR, 'config')                           # config dir for targetlists
    TARGET_LIST_PATH = os.path.join(CONFIG_PATH, 'targetList-fullBB')          # this is the name of the targetList file
    # # # #  done edits # # # #

    ALLOWED_EXTENSIONS = frozenset(['pdb', 'pds'])
    ALLOWED_ARGS = frozenset(['bbRMSD', 'dEps', 'ddZScore',
                              'matchIn', 'matchOut', 'phiEps', 'psiEps',
                              'query', 'rmsdCut', 'rmsdMode', 'seqOut', 'structOut',
                              'outType', 'target', 'targetList', 'topN', 'tune'])
