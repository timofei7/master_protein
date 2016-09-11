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
    TARGET_LIST_PATH = os.path.join(CONFIG_PATH, 'targetList-fullBB')       # this is the name of the targetList file
    SCRIPTS_PATH = os.path.join(BASEDIR, 'scripts')                         # directory with utility scripts
    LOG_PATH = os.path.join(BASEDIR, 'log')

    # # # #  done edits # # # #

    ALLOWED_EXTENSIONS = frozenset(['pdb', 'pds'])
    ALLOWED_ARGS = frozenset(['bbRMSD', 'dEps', 'ddZScore', 'ext', 'flag',
                              'matchIn', 'matchOut', 'phiEps', 'psiEps', 'query',
                              'database', 'rmsdCut', 'rmsdMode', 'seqOut', 'structOut',
                              'outType', 'target', 'targetList', 'topN', 'tune'])
