#!/usr/bin/env python
#
#
#
from pymol.wizard import Wizard
from pymol import cmd
from search_thread import *

URL = "http://127.0.0.1:5000/api/search"
# URL = "http://ararat.cs.dartmouth.edu:5000/api/search"

#TODO: use:
#--matchInFile     a file produced by --matchOutFile. If specified with
#    --query, can skip search and produce outputs directly.
# to pull in full match for a previously searched


class MasterSearch(Wizard):
    """
    This class  will create the wizard for performing MASTER searches.
    """
    def __init__(self, app, _self=cmd):
        Wizard.__init__(self, _self)

        # Clean the slate
        self.cmd.unpick()
        self.prompt = ['Make a selection and then hit search!']
        self.app = app

        # Default values
        self.rmsd_cutoff = 1.0
        self.number_of_structures = 25
        self.full_match = False
        self.url = URL

        self.searchThread = None

    #
    def cleanup(self):
        """
        Once we are done with the wizard, we should set various pymol
        parameters back to their original values.
        """
        self.stop_search()

    #
    def get_panel(self):
        """
        main menu panel
        """
        rmsd_menu = self.create_rmsd_menu()
        self.menu['rmsd'] = rmsd_menu
        num_structures_menu = self.create_num_structures_menu()
        self.menu['num_structures'] = num_structures_menu
        full_matches_menu = self.create_full_matches_menu()
        self.menu['full_matches'] = full_matches_menu

        return [
            [1, 'MASTER Search Engine', ''],
            [3, 'RMSD Cutoff: ' + str(self.rmsd_cutoff) + ' Angstroms', 'rmsd'],
            [3, 'Max Matches: ' + str(self.number_of_structures) + ' results', 'num_structures'],
            [3, 'Full Matches: ' + ['No', 'Yes'][self.full_match], 'full_matches'],
            [2, 'Search', 'cmd.get_wizard().launch_search()'],
            [2, 'Done', 'cmd.set_wizard()']]

    #
    def set_rmsd(self, rmsd):
        """
        This is the method that will be called once the user has
        selected an rmsd cutoff via the wizard menu.
        """
        self.rmsd_cutoff = rmsd
        self.cmd.refresh_wizard()

    #
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

    #
    def set_num_structures(self, num_structures):
        """
        This is the method that will be called once the user
        has set the maximum number of structures to return.
        """
        self.number_of_structures = num_structures
        self.cmd.refresh_wizard()

    #
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

    #
    def set_full_matches(self, full_matches):
        """
        """
        self.full_match = full_matches
        self.cmd.refresh_wizard()

    #
    def create_full_matches_menu(self):
        """
        """
        full_matches_menu = []
        full_matches_menu.append([2, 'Full Matches', ''])
        full_matches_menu.append(
            [1, 'No', 'cmd.get_wizard().set_full_matches(False)'])
        full_matches_menu.append(
            [1, 'Yes', 'cmd.get_wizard().set_full_matches(True)'])
        return full_matches_menu

    #
    def launch_search(self):
        active_selections = cmd.get_names('selections', 1)

        if len(active_selections) == 0:
            self.prompt = ['must have an active selection!']
        else:
            selection = active_selections[0]
            pdbstr = cmd.get_pdbstr(selection)

            self.stop_search()
            self.searchThread = SearchThread(
                self.rmsd_cutoff,
                self.number_of_structures,
                self.full_match,
                pdbstr,
                self.url,
                self.cmd)
            self.searchThread.start()

    #
    def stop_search(self, message=''):
        if self.searchThread:
            self.searchThread.stop(message)


def master_search(app):
    """
    MASTER search
    """
    wiz = MasterSearch(app)
    cmd.set_wizard(wiz)


# add "suns_search" as pymol command
cmd.extend('master_search', master_search)

# trick to get "wizard master_search" working
sys.modules['pymol.wizard.master_search'] = sys.modules[__name__]

try:
    from pymol.plugins import addmenuitem

    # add item to plugin menu
    def __init_plugin__(self):
        addmenuitem('MASTER Search', lambda s=self : master_search(s))
except:
    def __init__(self):
        self.menuBar.addmenuitem('Plugin', 'command', 'MASTER search',
                                 label='MASTER search', command=lambda s=self: master_search(s))
