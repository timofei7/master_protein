'''
    authors: Ben Scammell and Nick Fiacco
    '''
import struct
import Tkinter as tk
from constants import *
from logo_thread import *
from pymol import cmd
import math
import tkFileDialog
from __init__ import *
from pymol.wizard import Wizard
from fragment_thread import *

class AutoScrollbar(tk.Scrollbar):
    # a scrollbar that hides itself if it's not needed.  only
    # works with the grid geometry manager.
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.tk.call("grid", "remove", self)
        else:
            self.grid()
        tk.Scrollbar.set(self, lo, hi)

class FuserApp():
    
    def __init__(self, app):
        
        # Widget Parents
        self.win = tk.Toplevel(app.root)
        self.win.protocol("WM_DELETE_WINDOW", self.callback)
        self.win.title('Fuser')
        self.lock_one = False
        self.lock_two = False
        
        self.strand_one_selection = None
        self.strand_two_selection = None
        
        self.res_list_one = []
        self.res_list_two = []
        self.res_string_one = ''
        self.res_string_two = ''
        self.n_c = 1
        
        self.fuse_max = None
        self.fuse_min = None
        self.fragmentThread = None
        
        self.serverURL = "http://ararat.cs.dartmouth.edu:5001"
        
        self.grafts = []
        self.graft = None
        self.done_adding = False
        
        self.pdbstr = None
        self.pdbstr_n = None
        self.pdbstr_c = None
        
        self.database_type = None
        self.full_match = None
        
        # Make the residue selection buttons
        self.strand_title = tk.Label(self.win, text = "Residue selection").grid(columnspan=2, sticky=N+E+S+W)
        self.string = tk.IntVar()
        self.string.set(1)
        self.string_one = tk.Radiobutton(self.win, text="N-stub", variable=self.string, command = lambda: self.enable_first(1), value=1).grid(row=1, sticky=N+E+S+W)
        self.string_two = tk.Radiobutton(self.win, text="C-stub", variable=self.string, command = lambda: self.enable_second(2), value=2).grid(row=2, sticky=N+E+S+W)
        
        # Make the load buttons for residue selection
        self.so_lock = tk.Button(self.win, text="lock", state="normal", command=lambda: self.so_lock_mech(self.lock_one))
        self.so_lock.grid(row=1, column=1, sticky=N+E+S+W)
        self.st_lock = tk.Button(self.win, text="lock", state="disabled", command=lambda: self.st_lock_mech(self.lock_two))
        self.st_lock.grid(row=2, column=1, sticky=N+E+S+W)
        

        # Make the range of lengths labels
        self.range_title = tk.Label(self.win, text = "Length of graft").grid(row=3, columnspan=2, sticky=N+E+S+W)
        self.range_label = tk.Label(self.win, text="-Min-                             -Max-").grid(row = 4, columnspan=2, sticky=N+E+S+W)
        
        # Make the range of lengths entry boxes
        self.range_min = tk.StringVar(self.win)
        self.range_min.set('1')
        self.min_entry = tk.Entry(self.win, textvariable=self.range_min).grid(row=5, sticky=N+E+S+W)
        
        self.range_max = tk.StringVar(self.win)
        self.range_max.set('10')
        self.max_entry = tk.Entry(self.win, textvariable=self.range_max).grid(row=5, column=1, sticky=N+E+S+W)
        
        # Blank space
        self.filler_two = tk.Label(self.win).grid(row=6, columnspan=2, sticky=N+E+S+W)
    
        
        # Make a label for RMSD and entry box
        self.rmsd_label = tk.Label(self.win, text = "RMSD cut", width=1).grid(row=7, column=0, sticky=N+E+S+W)
        self.rmsd = tk.StringVar(self.win)
        self.rmsd.set('0.5')
        self.rmsd_entry = tk.Entry(self.win, textvariable = self.rmsd, width=2).grid(row=7, column=1, sticky=N+E+S+W)
        
        # Make a label for the Number of Structures value
        self.num_structs_label = tk.Label(self.win, text = "# matches", width=1).grid(row=8, column=0, sticky=N+E+S+W)
        self.num_structs = tk.StringVar(self.win)
        self.num_structs.set('10')
        self.matches_entry = tk.Entry(self.win, textvariable = self.num_structs, width=1).grid(row=8, column=1, sticky=N+E+S+W)
        

        # Make Label and menu selection for database type
        self.database_label = tk.Label(self.win, text = "Database").grid(row=9, column=0, sticky=N+E+S+W)
        self.db = tk.StringVar(self.win)
        self.db.set("Test DB")
        self.database_select = tk.OptionMenu(self.win, self.db, "Test DB", "Full DB").grid(row=9, column=1, sticky=N+E+S+W)
        
        # Make Label and menu selection for match type
        self.match_label = tk.Label(self.win, text = "Match type").grid(row=10, column=0, sticky=N+E+S+W)
        self.fm = tk.StringVar(self.win)
        self.fm.set("Region")
        self.match_select = tk.OptionMenu(self.win, self.fm, "Region", "Full").grid(row=10, column=1, sticky=N+E+S+W)
        
        # Blank space
        self.filler_two = tk.Label(self.win).grid(row=11, columnspan=2, sticky=N+E+S+W)
        
   
        # Add a search button that calls searches for fragment to graft with
        self.search_button = tk.Button(self.win, text="Find Grafts", command=lambda: self.set_and_search()).grid(row=12, column=0, sticky=N+E+S+W)
        self.graft_id = tk.StringVar(self.win)
        self.graft_id.set('Graft IDs:')
        graft_id_button = tk.OptionMenu(self.win, self.graft_id, 'Graft IDs:').grid(row=12, column=1, sticky=N+E+S+W)

#        # Blank space
#        self.filler_three = tk.Label(self.win).grid(row=9, columnspan=2, sticky=N+E+S+W)
#        
#        # Fuse label and Fuse command
#        self.fuse_label = tk.Label(self.win, text="Fuse").grid(row=10, columnspan=2, sticky=N+E+S+W)
#        self.fuse_button = tk.Button(self.win, text="--->").grid(row=11, columnspan=2, sticky=N+E+S+W)

        # Start make id list
        self.make_ids()
    
    
    # Remake ID menu after it been appended to searches
    def make_ids(self):
        
        if self.done_adding == True:
            
            # Set search options and current search
            grafts = self.grafts[0:]
            grafts.insert(0, 'Graft IDs: ')
            self.graft_id.set(grafts[0])
            
            # Remake window
            graft_id = tk.OptionMenu(self.win, self.graft_id, *grafts).grid(row=10, column=0, rowspan=2, sticky=N+E+S+W)
            
            # Reset flag
            self.done_adding = False
        
    def complete_search(self, numMatches = -1):
        """
        callback called by FragmentThread when the
        search is complete
        """

        if (numMatches >= 0):
            print "number of matches = ", numMatches
            cmd.get_wizard().set_status('search complete', 'Search complete, %d matches' % numMatches)
        else:
            cmd.get_wizard().set_status('search complete')
        
        cmd.get_wizard().makeLogo = 7; # add search to menu
                                     
    def add_new_graft(self, search_id):
        '''
        add current search to search history after it finishes
        '''
        # print 'add new search'
        self.grafts.append(graft_id)
        cmd.refresh_wizard()

        # Trip flag for window
        self.done_adding = True
        cmd.get_wizard().makeLogo = 7
    
    
    def so_lock_mech(self, bool):
        if bool == False:
            
            
            active_selections = cmd.get_names('selections', 1)
            selection = active_selections[0]
            self.pdbstr_n = cmd.get_pdbstr(selection)
            split_pdbstr = self.pdbstr_n.split()
            
            self.res_list_one = [-1]
            
            i = 5
            self.res_string_one = ''
            while i < len(split_pdbstr):
                
                if split_pdbstr[i] != self.res_list_one[-1]:
                    self.res_list_one.append(split_pdbstr[i])
                    
                    self.res_string_one += str(self.find_aa(split_pdbstr[i-2]))
                i += 12
            
            
            self.res_list_one = self.res_list_one[1:]
            for num in self.res_list_one:
 
                if num in self.res_list_two:
                    print 'residue selections must not overlap'
                    break
                elif num == self.res_list_one[-1] and num not in self.res_list_two:
                    self.strand_one_selection = self.res_list_one
                    print self.strand_one_selection
                    self.so_lock.config(text=self.res_string_one)

    

        else:
            self.so_lock.config(text="lock")
        self.lock_one = not bool
    
    def st_lock_mech(self, bool):
        if bool == False:
            
            
            active_selections = cmd.get_names('selections', 1)
            selection = active_selections[0]
            self.pdbstr_c = cmd.get_pdbstr(selection)
            split_pdbstr = self.pdbstr_c.split()
            
            self.res_list_two = [-1]
            
            i = 5
            self.res_string_two = ''
            while i < len(split_pdbstr):
                
                if split_pdbstr[i] != self.res_list_two[-1]:
                    self.res_list_two.append(split_pdbstr[i])
                    
                    self.res_string_two += str(self.find_aa(split_pdbstr[i-2]))

                i += 12
            
            
            self.res_list_two = self.res_list_two[1:]
            
            for num in self.res_list_two:
                if num in self.res_list_one:
                    print 'residue selections must not overlap'
                    break
                elif num == self.res_list_two[-1] and num not in self.res_list_one:
                    self.strand_two_selection = self.res_list_two
                    print self.strand_two_selection
                    self.st_lock.config(text=self.res_string_two)

    
        else:
            self.st_lock.config(text="lock")
        self.lock_two = not bool
    
    def enable_first(self, v):
        self.so_lock.config(state="normal")
        self.st_lock.config(state="disabled")
    
    def enable_second(self, v):
        self.so_lock.config(state="disabled")
        self.st_lock.config(state="normal")
    
    
    def set_and_search(self):
        print 'a'
        
        # Max and Min fuse length checks
        if self.is_num(str(self.range_max.get())):
            print 'b'
            pass
        else:
            print 'c'
            cmd.get_wizard().status = 'range input not number'
            cmd.refresh_wizard()
            return
        
        if self.is_num(str(self.range_min.get())):
            pass
        else:
            cmd.get_wizard().status = 'range input not number'
            cmd.refresh_wizard()
            return
        print 'q'
        if self.pdbstr_n == None or self.pdbstr_c == None:
            print 'requires two stubs'
            return
        print 't'
        
        
        # Set RMSD cutoff
        if self.is_num(self.rmsd.get()):
            pass
        else:
            cmd.get_wizard().status = 'rmsd not number'
            cmd.refresh_wizard()
            return
        print 'o'
        # Set number of structures
        if self.is_num(self.num_structs.get()):
            pass
        else:
            cmd.get_wizard().status = 'num matches not number'
            cmd.refresh_wizard()
            return
        print '3'
        # Set Database
        if self.db.get() == "Test DB":
            self.database_type = DATABASE_TEST
        elif self.db.get() == "Full DB":
            self.database_type = DATABASE_FULL
        print '6'
        # Set Full matches
        if self.fm.get() == "Region":
            print 7
            self.full_match = False
        elif self.fm.get() == "Full":
            print 9
            self.full_match = True
        print 10


        print self.pdbstr, self.rmsd.get(), self.num_structs.get(), self.full_match, self.database_type, float(self.range_max.get()), float(self.range_min.get()), self.serverURL

        self.stop_search()
        print 'go'
        self.pdbstr = (self.pdbstr_n[:-4] + self.pdbstr_c) # without 'END'
        print 'gogo'
        self.fragmentThread = FragmentThread(cmd.get_wizard(), self.pdbstr, self.rmsd.get(), self.num_structs.get(), self.full_match, self.database_type, float(self.range_max.get()), float(self.range_min.get()), self.serverURL, cmd.get_wizard().cmd)
                            
        self.fragmentThread.start()
        cmd.get_wizard().set_status('search launched')
        cmd.get_wizard().searchProgress = 0
        
        cmd.refresh_wizard()
            
    def stop_search(self, message=''):
        if self.fragmentThread:
            print 'stop'
            self.fragmentThread.stop(message)
    
    def find_aa(self, tc):
        oc = None
        if tc == 'ALA':
            oc = 'A'
        elif tc == 'ARG':
            oc = 'R'
        elif tc == 'ASN':
            oc = 'N'
        elif tc == 'ASP':
            oc = 'D'
        elif tc == 'ASX':
            oc = 'B'
        elif tc == 'CYS':
            oc = 'C'
        elif tc == 'GLU':
            oc = 'E'
        elif tc == 'GLN':
            oc = 'Q'
        elif tc == 'GLX':
            oc = 'Z'
        elif tc == 'GLY':
            oc = 'G'
        elif tc == 'HIS':
            oc = 'H'
        elif tc == 'ILE':
            oc = 'I'
        elif tc == 'LEU':
            oc = 'L'
        elif tc == 'LYS':
            oc = 'K'
        elif tc == 'MET':
            oc = 'M'
        elif tc == 'PHE':
            oc = 'F'
        elif tc == 'PRO':
            oc = 'P'
        elif tc == 'SER':
            oc = 'S'
        elif tc == 'THR':
            oc = 'T'
        elif tc == 'TRP':
            oc = 'W'
        elif tc == 'TYR':
            oc = 'Y'
        elif tc == 'VAL':
            oc = 'V'
        return oc
            
    def callback(self):
        cmd.refresh_wizard()
        # Reset flag for making popup
        cmd.get_wizard().fuser_app = False
        self.win.destroy()

    def is_num(self, num):
    
    # Check to make sure input is only numerals and '.'
        for i in range(len(num)):
            if 48 <= ord(num[i]) <= 57 or ord(num[i]) == 46:
                pass
            else:
                return False
        return True


