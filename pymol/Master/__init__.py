#!/usr/bin/env python
"""
PyMol plugin for MASTER protein search
connects to a remote server
author:   Tim Tregubov, 12/2014
"""

from pymol.wizard import Wizard
from pymol import cmd
from server_thread import *
from logo_popup import *
import Tkinter as tk
from constants import *
from server_thread import *
from search_thread import *
from logo_thread import *

class MasterSearch(Wizard):
    """
    This class  will create the wizard for performing MASTER searches.
    """
    def __init__(self, app, _self=cmd):
        Wizard.__init__(self, _self)

        # Clean the slate
        self.cmd.unpick()
        self.app = app
        self.ref = Wizard

        self.status = 'waiting for selection'
        self.statusPrompt = None
        self.searchProgress = 0.0
        self.errorMessage = ''
        self.makeLogo = 0

        self.popup_app = None
        self.live_app = False

        self.update()

    def update(self):
        """
        Checks to see what needs to be updated in/by the Wizard, updates, and quits.
        This could include opening a window to show the logo, updating the progress
        bar of an ongoing search, displaying an error or other message from a search...
        """
        if self.makeLogo == 3 and self.live_app != True:
            self.popup_app = WindowApp(self.app)
            self.live_app = True
        elif self.makeLogo == 1 and self.live_app == True:
            self.popup_app.make_ids()  # search just completed, add item to dropdown list
        elif self.makeLogo == 2 and self.live_app == True:
            if (self.popup_app is not None):
                self.popup_app.win.destroy()  # exit button pressed, close window
                self.live_app = False
        
        self.makeLogo = 0
        self.app.root.after(100, self.update)


    def set_searchProgress(self, progress):
        """
        Setter for search progress
        """
        self.searchProgress = progress
        self.cmd.refresh_wizard()

    def set_status(self, status, prompt = None):
        """
        Setter for status
        """
        self.status = status
        self.statusPrompt = prompt
        self.cmd.refresh_wizard()

    def set_errorMessage(self, mes):
        """
        Setter for error message
        """
        self.errorMessage = mes

    def cleanup(self):
        """
        Once we are done with the wizard, we should set various pymol
        parameters back to their original values.
        """
        self.popup_app.stop_search()

    def logo_helper(self, flag):
        self.makeLogo = flag

    def get_panel(self):
        """
        sets up the main menu panel
        """

        # num is the type of display  1 is title only, 2 is button, 3 is dropdown
        return [[2, 'Search Menu','cmd.get_wizard().logo_helper(3)'], [2, 'Exit', 'cmd.get_wizard().logo_helper(2); cmd.set_wizard()']]
    

    def get_prompt(self):
        defaultPrompt = ''
        if (self.status == 'waiting for selection'):
             defaultPrompt = [ 'Make a selection and then hit search...' ]
        elif (self.status == 'logo request launched'):
            defaultPrompt = [ 'Launched logo generation' ]
        elif (self.status == 'vector graphic requested'):
            defaultPrompt = [ 'Vector graphic requested' ]
        elif (self.status == 'vector graphic received'):
            defaultPrompt = [ 'Vector graphic received' ]
        elif (self.status == 'Save Cancelled'):
            defaultPrompt = [ 'Save Cancelled' ]
        elif (self.status == 'rmsd not number'):
            defaultPrompt = [ 'RMSD cutoff must be double' ]
        elif (self.status == 'num matches not number'):
            defaultPrompt = [ 'matches must be integer' ]
        elif (self.status == 'residue selected'):
            defaultPrompt = [ str(self.popup_app.win.res_info) ]
        elif (self.status == 'SequenceLogo saved'):
            defaultPrompt = [ 'SequenceLogo saved as ' + str(self.popup_app.win.filename)]
        elif (self.status == 'logo request finished'):
            defaultPrompt = [ 'Received logo from server' ]
            self.status = [ 'waiting for selection' ]
        elif (self.status == 'search launched'):
            defaultPrompt = [ 'Searching (%d%%)...' % round(100*self.searchProgress)  ]
        elif (self.status == 'search complete'):
            defaultPrompt = [ 'Search complete...' ]
            self.status = 'waiting for selection'
        elif (self.status == 'no selection'):
            defaultPrompt = [ 'Error: must have an active selection!' ]
            self.status = 'waiting for selection'

        if (self.statusPrompt is None):
            self.prompt = defaultPrompt
        else:
            self.prompt = [self.statusPrompt]
        return self.prompt

'''
Wrapper class for the MasterSearch client application
'''
def master_search(app):
    """
    MASTER search
    """

    # create a folder for storing temporary data
    if not os.path.exists(MAIN_CACHE):
        os.makedirs(MAIN_CACHE)

    if not os.path.exists(SEARCH_CACHE):
        os.makedirs(SEARCH_CACHE)

    if not os.path.exists(LOGO_CACHE):
        os.makedirs(LOGO_CACHE)

    wiz = MasterSearch(app)
    cmd.set_wizard(wiz)


# add "master_search" as pymol command
cmd.extend('master_search', master_search)

# trick to get "wizard master_search" working
sys.modules['pymol.wizard.master_search'] = sys.modules[__name__]

try:
    from pymol.plugins import addmenuitem

    # add item to plugin menu
    def __init_plugin__(self):
        addmenuitem('MASTER Search v0.1', lambda s = self: master_search(s))
except:
    def __init__(self):
        self.menuBar.addmenuitem('Plugin', 'command', 'MASTER search',
                                 label='MASTER search', command= lambda s = self: master_search(s))

