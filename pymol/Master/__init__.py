#!/usr/bin/env python
"""
PyMol plugin for MASTER protein search
connects to a remote server
author:   Tim Tregubov, 12/2014
"""

from pymol.wizard import Wizard
from pymol import cmd
from search_thread import *
from logo_thread import *
from Tkinter import *
import os
import subprocess
import threading
import shutil
from constants import *

# URL = "http://127.0.0.1:5000/api/search"
URL = "http://ararat.cs.dartmouth.edu:5001/api/search"
LOGOURL = "http://ararat.cs.dartmouth.edu:5001/api/logo"

class MasterSearch(Wizard):
    """
    This class  will create the wizard for performing MASTER searches.
    """
    def __init__(self, app, _self=cmd):
        Wizard.__init__(self, _self)

        # Clean the slate
        self.cmd.unpick()
        self.app = app

        # Default values
        self.rmsd_cutoff = 1.0
        self.number_of_structures = 25
        self.full_match = False
        self.url = URL
        self.LOGOurl = LOGOURL

        self.ref = Wizard

        # default values for sequence logo UI
        self.operations = []
        self.searches = []
        self.search = None # current search action
        self.operation = None # current operation

        self.dictionary = {}

        self.searchThread = None
        self.logoThread = None

        self.status = 'waiting for selection'
        self.searchProgress = 0.0
        self.errorMessage = ''
        self.makeLogo = 0
        self.update()


    def update(self):
        """
        Checks to see what needs to be updated in/by the Wizard, updates, and quits.
        This could include opening a window to show the logo, updating the progress
        bar of an ongoing search, displaying an error or other message from a search...
        """
        if (self.makeLogo != 0):
          self.launch_logo_search(self.makeLogo)
          self.makeLogo = 0
        self.app.root.after(100, self.update)

    def set_searchProgress(self, progress):
        """
        Setter for search progress
        """
        self.searchProgress = progress
        self.cmd.refresh_wizard()

    def set_status(self, status):
        """
        Setter for status
        """
        self.status = status
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
        self.stop_search()


    def get_panel(self):
        """
        sets up the main menu panel
        """
        rmsd_menu = self.create_rmsd_menu()
        self.menu['rmsd'] = rmsd_menu
        num_structures_menu = self.create_num_structures_menu()
        self.menu['num_structures'] = num_structures_menu
        full_matches_menu = self.create_full_matches_menu()
        self.menu['full_matches'] = full_matches_menu

        '''
        sets up the menu ui for sequence logo
        '''
        select_search_menu = self.create_select_search_menu()
        select_operation_menu = self.create_select_operation_menu()
        self.menu['searches'] = select_search_menu
        self.menu['operations'] = select_operation_menu

        # num is the type of display  1 is title only, 2 is button, 3 is dropdown
        return [
            [1, 'MASTER Search Engine', ''],
            [3, 'RMSD Cutoff: ' + str(self.rmsd_cutoff) + ' Angstroms', 'rmsd'],
            [3, 'Max Matches: ' + str(self.number_of_structures) + ' results', 'num_structures'],
            [3, 'Full Matches: ' + ['No', 'Yes'][self.full_match], 'full_matches'],
            [2, 'Search', 'cmd.get_wizard().launch_search()'],
            [1, 'Sequence Logo', ''],
            [3, 'select search: ' + str(self.search), 'searches'],
            [3, 'select operation: ', 'operations'],
            # [2, 'Execute', 'cmd.get_wizard().launch_operation()'],
            [2, 'Done', 'cmd.set_wizard()']]


    def set_rmsd(self, rmsd):
        """
        This is the method that will be called once the user has
        selected an rmsd cutoff via the wizard menu.
        """
        self.rmsd_cutoff = rmsd
        self.cmd.refresh_wizard()


    def create_rmsd_menu(self):
        """
        This method will create a wizard menu for the possible RMSD cutoff values.
        Currently the values range from 0.1 to 2 A RMSD.
        """
        rmsd_menu = [[2, 'RMSD Cutoff', '']]
        for rmsd_choice in range(1,21):
            rmsd = float(rmsd_choice) / 10.0
            rmsd_menu.append(
                [1, str(rmsd), 'cmd.get_wizard().set_rmsd(' + str(rmsd) + ')'])
        return rmsd_menu


    def set_num_structures(self, num_structures):
        """
        This is the method that will be called once the user
        has set the maximum number of structures to return.
        """
        self.number_of_structures = num_structures
        self.cmd.refresh_wizard()


    def create_num_structures_menu(self):
        """
        This method will create a wizard menu for the possible number of structures
        to return.  Values range from 10 to 2000.
        """
        num_structures_menu = [[2, 'Number of Results', '']]
        for n in [10, 20, 50, 100, 200, 500]:
            num_structures_menu.append(
                [1, str(n), 'cmd.get_wizard().set_num_structures(' + str(n) + ')'])
        return num_structures_menu


    def set_full_matches(self, full_matches):
        """
        """
        self.full_match = full_matches
        self.cmd.refresh_wizard()


    def create_full_matches_menu(self):
        """
        creates the wiard menu for the full matches boolean option
        """
        full_matches_menu = []
        full_matches_menu.append([2, 'Full Matches', ''])
        full_matches_menu.append(
            [1, 'No', 'cmd.get_wizard().set_full_matches(False)'])
        full_matches_menu.append(
            [1, 'Yes', 'cmd.get_wizard().set_full_matches(True)'])
        return full_matches_menu


    def add_new_search(self, search_id):
        '''
        add current search to search history after it finishes
        '''
        # print 'add new search'
        self.searches.append(search_id)
        self.cmd.refresh_wizard()


    '''
    This is the section for adding Sequence Logo UI
    '''
    def create_select_search_menu(self):
        select_search_menu = []
        select_search_menu.append([2, 'History', ''])
        for i in range(len(self.searches)):
            select_search_menu.append([1, 'id: '+self.searches[i], 'cmd.get_wizard().set_search('+str(i)+')'])
        return select_search_menu


    def set_search(self, i):
        # print 'set search with id: '+self.searches[int(i)]
        self.search = self.searches[int(i)]
        self.cmd.refresh_wizard()


    def create_select_operation_menu(self):
        select_operation_menu = []
        select_operation_menu.append([2, 'Operation', ''])

        #TODO: change launch show logo operation to my version

        select_operation_menu.append([1, 'show sequence logo', 'cmd.get_wizard().makeLogo = 1'])
        select_operation_menu.append([1, 'show frequency logo', 'cmd.get_wizard().makeLogo = 2'])
        return select_operation_menu


    # def seq_show_thread(self, flag):
    #     # start_seq_logo_thread(cmd, self.search)
    #     search_action_id = self.search
    #     stm = ''
    #
    #     search_id = str(search_action_id)
    #     flag = str(flag)
    #
    #     p = subprocess.Popen(["python", os.path.dirname(os.path.realpath(__file__)) + '/logo_script.py', str(search_action_id), str(flag)], stdout=subprocess.PIPE, bufsize=1)
    #
    #     out, err = p.communicate()
    #     print out
    #
    #     while True:
    #         # print "Looping"
    #         line = p.stdout.readline()
    #         if not line:
    #             break
    #         if 'click' not in line:
    #             continue
    #         line = line.strip()
    #         toks = line.split()
    #         chain = str(toks[4])
    #         num = str(toks[6])
    #         if stm != '':
    #             stm += ', '
    #         stm += 'chain '+chain+' and resi '+num
    #         # print stm
    #         # print 'highlight chain ',chain, 'num ',num
    #         self.cmd.select(search_action_id+'sele', stm)
    #         '''
    #         highlight selected residue
    #         '''
    #         sys.stdout.flush()
    #
    #     # clear cache data
    #     if os.path.exists(CACHE_PATH+search_action_id):
    #         print 'clean up for search ',search_action_id
    #         shutil.rmtree(CACHE_PATH+search_action_id)

    #
    # def launch_show_logo_operation(self, flag):
    #     # flag used as indicator for Sequence or Frequency logo
    #     if self.search is None:
    #         print 'please select target search'
    #         return
    #     # start a new thread
    #     thread = threading.Thread(target = self.seq_show_thread, args=[flag])
    #     thread.start()


    def launch_logo_search(self, flag):
        """
        launches the show logo operation in the separate thread
        does some basic checking and gets selection
        """

        if self.search is None:
            print 'please select target search'
            return

        else:
            print str(self.dictionary[self.search])
            self.logoThread = LogoThread(
                self.rmsd_cutoff,
                self.dictionary[self.search],
                int(flag),
                self.LOGOurl,
                self.cmd)
            self.logoThread.start()
            self.logoThread.join()

            path = 'cache/'+str(self.search)
            with open(path, 'r') as f:
                residues = f.readline().strip()

            query = self.dictionary[self.search]

            display_logo(self.app, query, residues)

    def stop_logo(self, message=''):
        if self.logoThread:
            self.logoThread.stop(message)

    def launch_search(self):
        """
        launches the search in the separate thread
        does some basic checking and gets selection
        """

        # gets the active selections from pymol
        active_selections = cmd.get_names('selections', 1)
        if len(active_selections) == 0:
            self.status = 'no selection'
        else:
            print str(active_selections)
            selection = active_selections[0]
            pdbstr = cmd.get_pdbstr(selection)
            print 'pdbstr is', pdbstr
            self.stop_search()
            self.searchThread = SearchThread(self,
                self.rmsd_cutoff,
                self.number_of_structures,
                self.full_match,
                pdbstr,
                self.url,
                self.cmd,
                self.dictionary)
            self.searchThread.start()
            self.status = 'search launched'
            self.searchProgress = 0
        self.cmd.refresh_wizard()

    def stop_search(self, message=''):
        if self.searchThread:
            self.searchThread.stop(message)
    

    def get_prompt(self):
        self.prompt = None
        if (self.status == 'waiting for selection'):
             self.prompt = [ 'Make a selection and then hit search...' ]
        elif (self.status == 'search launched'):
            self.prompt = [ 'Searching (%d%%)...' % round(100*self.searchProgress)  ]
        elif (self.status == 'search complete'):
            self.prompt = [ 'Search complete...' ]
            self.status = 'waiting for selection'
        elif (self.status == 'no selection'):
            self.prompt = [ 'Error: must have an active selection!' ]
            self.status = 'waiting for selection'
        return self.prompt

def master_search(app):
    """
    MASTER search
    """
    # create a folder for storing temporary data
    if not os.path.exists('cache/'):
        os.makedirs('cache/')


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
        addmenuitem('MASTER Search v0.1', lambda s=self : master_search(s))
except:
    def __init__(self):
        self.menuBar.addmenuitem('Plugin', 'command', 'MASTER search',
                                 label='MASTER search', command=lambda s=self: master_search(s))

def display_logo(app, query, residues):

    window = Toplevel(app.root)

#    print "thread:"
#    print threading.current_thread()


    logo_filepath = "cache/logos/"+str(query)+".gif"
    img = PhotoImage(file = logo_filepath)

    canvas = Label(window)
    canvas.pack()

    canvas.configure(image=img)

    size = str(LOGO_GUI_WIDTH)+'x'+str(LOGO_GUI_HEIGHT)
    window.geometry(size)

    window.mainloop()