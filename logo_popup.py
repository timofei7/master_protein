'''
authors: Ben Scammell and Nick Fiacco
'''

import Tkinter as tk
#from Tkinter import *
from constants import *
from logo_thread import *
from pymol import cmd
import math
import tkFileDialog
from __init__ import *
from pymol.wizard import Wizard

class WindowApp(tk.Tk):
    
    def __init__(self, app, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.title('MASTER Search')
        
        # Instance variables to be used in logos
        self.start = None
        self.textview = None
        self.sb = None
        self.total_num_residues = None
        self.selected_list = None
        self.residue_list = None
        #self.img = None
        #self.logo = None

        # Make a label for RMSD and entry box
        rmsd_label = tk.Label(self, text = "RMSD cut").grid(rowspan=2, sticky=N+E+S+W)
        rmsd = tk.DoubleVar(self)
        rmsd.set(0.5)
        rmsd_entry = tk.Entry(self, textvariable = rmsd).grid(row=0, column=1, rowspan=2, sticky=N+E+S+W)
        
        # Make a label for the Number of Structures value
        num_structs_label = tk.Label(self, text = "# matches").grid(row=2, column=0, rowspan=2, sticky=N+E+S+W)
        
        # Make a number of structures selection menu
        num_structs = tk.IntVar(self)
        num_structs.set(10)
        matches_entry = tk.Entry(self, textvariable = num_structs).grid(row=2, column=1, rowspan=2, sticky=N+E+S+W)
        

        # Make Label and menu selection for database type
        database_label = tk.Label(self, text = "Database").grid(row=4, column=0, rowspan=2, sticky=N+E+S+W)
        db = tk.StringVar(self)
        db.set("Test DB")
        database_select = tk.OptionMenu(self, db, "Test DB", "Full DB").grid(row=4, column=1, rowspan=2, sticky=N+E+S+W)
        
        # Make Label and menu selection for match type
        match_label = tk.Label(self, text = "Match type").grid(row=6, column=0, rowspan=2, sticky=N+E+S+W)
        fm = tk.StringVar(self)
        fm.set("Region")
        match_select = tk.OptionMenu(self, fm, "Region", "Full").grid(row=6, column=1, rowspan=2, sticky=N+E+S+W)

        # Add a search button that calls search when clicked
        search_button = tk.Button(self, text="Search", command=lambda: self.set_and_search(float(rmsd.get()), int(num_structs.get()), str(db.get()), str(fm.get()))).grid(row=8, column=0, rowspan=2, columnspan=2, sticky=N+E+S+W)
        
        # Pick search
        self.search_id = tk.StringVar(self)
        self.search_id.set('Search IDs:')
        search_id_button = tk.OptionMenu(self, self.search_id, 'Search IDs').grid(row=10, column=0, rowspan=2, sticky=N+E+S+W)

        # Info or freq checkbuttons
        logo_choice = tk.IntVar(self)
        logo_choice.set(1)
        info_check = tk.Checkbutton(self, text="info", variable=logo_choice, onvalue=1, offvalue=2).grid(row=10, column=1, sticky=N+E+S+W)
        freq_check = tk.Checkbutton(self, text="freq", variable=logo_choice, onvalue=2, offvalue=1).grid(row=11, column=1, sticky=N+E+S+W)

        # Make a button to run the Sequence Logo
        show_logo_button = tk.Button(self, text="Show Logo", command=lambda: self.set_and_display(int(logo_choice.get()), str(self.search_id.get()))).grid(row=12, column=0, rowspan=2, sticky=N+E+S+W)
        
        # Make a button to run Frequency Logo
        save_button = tk.Button(self, text="Save Logo", command=self.saveFile).grid(row=12, column=1, rowspan=2, sticky=N+E+S+W)
        
        # Labels placeholding for logo graphic
        placeholder = tk.Label(self, background='white', text = "                                                                                                                 ").grid(row=0, column=3, rowspan=10, columnspan=4, sticky=N+E+S+W)
        
        residue_placeholder = tk.Label(self, background='black', text = "                                                                                                                 ").grid(row=10, column=3, rowspan=2, columnspan=4, sticky=N+E+S+W)
       
        scrollbar_placeholder = tk.Label(self, text = "                                                                                                                 ").grid(row=12, column=3, rowspan=2, columnspan=4, sticky=N+E+S+W)
        
        print 82
        logo_filepath = "/Users/bscammell/MASTER/pymol/Master/cache/logos/tmpbhWv2Ts.gif"
        self.img = tk.PhotoImage(file = logo_filepath)
        print self
        self.logo = tk.Label(self, image=self.img)
        print 84
        self.logo.photo = self.img
        print 85
        self.logo.grid(row=0, column=3, rowspan=10, columnspan=4)
        print 89
    

    # Function to set flag and ID number
    def set_and_display(self, flag, id):
        
        print "Flag: " + str(flag) + " ID: " + str(id)
        
        # Set search
        cmd.get_wizard().set_search(int(id[-1])-1)
        print 60
        # Show logo
        cmd.get_wizard().launch_logo_search(flag)
        print 70


    # Function to set all values for searching
    def set_and_search(self, rmsd_cutoff, number_structs, database, full_matches):

        # Set RMSD cutoff
        cmd.get_wizard().set_rmsd(float(rmsd_cutoff))

        # Set number of structures
        cmd.get_wizard().set_num_structures(number_structs)
        print 21
        # Set Database
        if database == "Test DB":
            cmd.get_wizard().set_database("Test")
        elif database == "Full DB":
            cmd.get_wizard().set_database("Full")

        # Set Full matches
        if full_matches == "Region":
            cmd.get_wizard().set_full_matches(False)
        elif full_matches == "Full":
            cmd.get_wizard().set_full_matches(True)
        print 22

        # Launch the search
        cmd.get_wizard().launch_search()
        print 23
            
    # Remake the optionmenu
    def refresh_id_options(self):
        print 10
        searches = cmd.get_wizard().searches
        self.search_id.set(searches[0])
        search_id = tk.OptionMenu(self, self.search_id, *searches).grid(row=10, column=0, rowspan=2, sticky=N+E+S+W)
        print 11


    def saveFile(self):

        extensions = [('PDF', '.pdf'), ('EPS', '.eps'), ('GIF', '.gif'), ('PNG', '.png')]
        f = tkFileDialog.asksaveasfile(mode='w', defaultextension=".pdf", filetypes=extensions)

        # the user cancelled the save
        if f is None:
            print("Save cancelled")
            return

        print f.name

        # get the EPS file from the server and write it
        getLogoFile(f.name)
        f.close()
        print("Successfully saved")
        plugin.status = 'SequenceLogo saved'
        cmd.refresh_wizard()

    def getLogoFile(self, filepath):
        plugin.status = 'vector graphic requested'
        cmd.refresh_wizard()

        ext = filepath.split(".")[-1]

        logoThread = LogoThread(
            rmsd_cutoff,
            query,
            int(flag),
            LOGOurl,
            cmd,
            filepath,
            ext)
        logoThread.start()
        logoThread.join()

        plugin.status = 'vector graphic received'
        cmd.refresh_wizard()

        '''
        This is the code for the Sequence Logo UI
        '''
    
    def display_menu_logo(self, app, query, residues, rmsd_cutoff, LOGOurl, flag, plugin):
        """
        This method handles creating a SequenceLogo UI with Tkinter
        author = Nick
        """
        print 80
        
        if flag == 1:
            logo_filepath = LOGO_CACHE + str(query)+"s.gif"
        elif flag == 2:
            logo_filepath = LOGO_CACHE + str(query)+"f.gif"
        print 82
        print logo_filepath
        self.img = tk.PhotoImage(file = logo_filepath)
        print self.img
        print 83
        self.logo = tk.Label(self, image=self.img)
        print 84
        self.logo.photo = self.img
        print 85
        self.logo.grid(row=0, column=3, rowspan=10, columnspan=4)
        print 89

        # parse query, add residues to a list for later reference
        residues_str = residues.split()
        self.residue_list = []

        # selected list lets us check if the residue is selected or not
        self.selected_list = []

        for residue_str in residues_str:
            residue = residue_str.split(',')
            self.residue_list.append(residue)
            self.selected_list.append(False)

        # some temporary values to play around with
        total_width = 1.5*(len(self.residue_list)) + 1.905
        left_margin = 53
        right_margin = 14

        self.total_num_residues = len(self.residue_list)

        # set up empty initial selection object used by PyMol to group selections
        cmd.select("curPos", "none")
        
        # Create a scrollbar
        self.sb = tk.Scrollbar(self, orient=HORIZONTAL).grid(row=12, column=3, rowspan=2, columnspan=4, sticky=N+E+S+W)

        # create the textbox with the residue names
        self.textview = tk.Text(self, height = 1, width = int(total_width), font=("Courier", 15))
        self.textview.config(highlightthickness = 0, bd = 0,) # remove border
        self.textview.config(cursor = 'left_ptr') # stylistic options
        self.textview.config(background = 'black')
        self.textview.config(foreground = 'green2')
        self.textview.config(selectbackground = 'black')
        self.textview.grid(row=10, column=3, rowspan=2, columnspan=4, sticky=N+E+S+W)
        
        # Link the scrollbar and Text widgets
        print 100
        #self.textview.config(xscrollcommand=self.sb.set)
        print 101
        #self.sb.config(command=self.textview.xview)
        print 102

        # set up the indices that will change on click down and up, respectively
        self.start = -1

        for i in range(0, self.total_num_residues):

            # add the residue character into the string, with the associated tag
            self.textview.tag_configure(str(i))
            self.textview.insert(END, self.residue_list[i][0], str(i))

        self.textview.config(state=DISABLED)
        
        # this should bind the highlight event to the test event
        self.textview.bind("<Button-1>", mouse_down)
        self.textview.bind("<B1-Motion>", mouse_drag)
        print 45

    def mouse_down(self, event):
        #global start

        # try to get the index based on the click coordinates
        i = int(math.ceil((event.x-3)/9))

        # make sure you are in the window
        if(event.y>20 or event.y<2):
            return

        # must be a valid index
        if(i >= self.total_num_residues):
            return

        # set the start index of the dragging
        self.start = i

        # handle selection/deselection
        if(self.selected_list[i]):
            self.textview.tag_configure(str(i), background ='black')
            self.textview.tag_configure(str(i), foreground = 'green2')
            residue_deselect(i)
            self.selected_list[i] = False
        else:
            self.textview.tag_configure(str(i), background ='green2')
            self.textview.tag_configure(str(i), foreground = 'black')
            residue_select(i)
            self.selected_list[i] = True

    def mouse_drag(self, event):
        # try to get the index of the selected characters, and look up residue for selection
        #global start
        i = int(math.ceil((event.x-3)/9))

        # must be a valid index
        if(i >= self.total_num_residues):
            return

        # don't worry about the one you just selected
        if self.start != i:
            self.start = i

            # handle selection/deselection
            if self.selected_list[i]:
                self.textview.tag_configure(str(i), background ='black')
                self.textview.tag_configure(str(i), foreground = 'green2')
                residue_deselect(i)
                self.selected_list[i] = False

            else:
                self.textview.tag_configure(str(i), background ='green2')
                self.textview.tag_configure(str(i), foreground = 'black')
                residue_select(i)
                self.selected_list[i] = True


    def residue_select(self, i):
        print 'click search chain '+self.residue_list[i][1]+' num '+self.residue_list[i][2]
        cmd.select("curPos", "curPos or (chain " + self.residue_list[i][1] + " and resi " + self.residue_list[i][2] + ")")
        sys.stdout.flush()

    def residue_deselect(self, i):
        cmd.select("curPos", "curPos and not (chain " + self.residue_list[i][1] + " and resi " + self.residue_list[i][2] + ")")




"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

class WindowApp(tk.Tk):
    
    def __init__(self, app, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.title('MASTER Search')
        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        self.frames = {}
        for F in (StartPage, PageOne, PageTwo):
            page_name = F.__name__
            frame = F(container, self)
            self.frames[page_name] = frame
            
            # put all of the pages in the same location;
            # the one on the top of the stacking order
            # will be the one that is visible.
            frame.grid(row=0, column=0, sticky="nsew")
        
        self.show_frame("StartPage", 0, None)
    
    def show_frame(self, page_name, flag, id=None):
        '''Show a frame for the given page name'''
        print str(page_name) + str(flag)
        frame = self.frames[page_name]
        print 40
        frame.tkraise()
        print 41
        print str(id)
        if id != None:
            print "!!!"
            print cmd.get_wizard().set_search(int(search[-1]))
        print 42
        if flag == 1:
            self.frame['PageOne'].show_sequence_logo()
        
        print 43
        
        if flag == 2:
            self.frame['PageTwo'].show_frequency_logo()

        print 50


class StartPage(tk.Frame):
    
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        
        
        # Make a label for RMSD and entry box
        rmsd_label = tk.Label(self, text="RMSD cut").grid(rowspan=2, sticky=N+E+S+W)
        rmsd = tk.DoubleVar(self)
        rmsd.set(0.5)
        rmsd_entry = tk.Entry(self, textvariable = rmsd).grid(row=0, column=1, rowspan=2, sticky=N+E+S+W)

        # Make a label for the Number of Structures value and Entry widget
        num_structs_label = tk.Label(self, text = "# matches").grid(row=2, column=0, rowspan=2, sticky=N+E+S+W)
        num_structs = tk.IntVar(self)
        num_structs.set(10)
        matches_entry = tk.Entry(self, textvariable = num_structs).grid(row=2, column=1, rowspan=2, sticky=N+E+S+W)
        
        # Make Label and menu selection for database type
        database_label = tk.Label(self, text = "Database").grid(row=4, column=0, rowspan=2, sticky=N+E+S+W)
        db = tk.StringVar(self)
        db.set("Test DB")
        database_select = tk.OptionMenu(self, db, "Test DB", "Full DB").grid(row=4, column=1, rowspan=2, sticky=N+E+S+W)
        
        # Make Label and menu selection for match type
        match_label = tk.Label(self, text = "Match type").grid(row=6, column=0, rowspan=2, sticky=N+E+S+W)
        fm = tk.StringVar(self)
        fm.set("Region")
        match_select = tk.OptionMenu(self, fm, "Region", "Full").grid(row=6, column=1, rowspan=2, sticky=N+E+S+W)

        # Add a search button that calls search when clicked
        search_button = tk.Button(self, text="Search", command=lambda: self.set_and_search(float(rmsd.get()), int(num_structs.get()), str(db.get()), str(fm.get()))).grid(row=8, column=0, rowspan=2, columnspan=2, sticky=N+E+S+W)

        # Pick search
        search_id_label = tk.Label(self, text="Search ID").grid(row=10, column=0, rowspan=2, sticky=N+E+S+W)
        self.search_id = tk.StringVar(self)
        self.search_id.set('None')
        search_id_button = tk.OptionMenu(self, self.search_id, 'None').grid(row=10, column=1, rowspan=2, sticky=N+E+S+W)

        # Make Buttons for Logo displays
        show_info = tk.Button(self, text="Show Info", command=lambda: controller.show_frame("PageOne", 1, self.search_id.get())).grid(row=12, column=0, rowspan=2, sticky=N+E+S+W)
        
        show_freq = tk.Button(self, text="Show Freq", command=lambda: controller.show_frame("PageTwo", 2, self.search_id.get())).grid(row=12, column=1, rowspan=2, sticky=N+E+S+W)
        print 31
    
    # Function to set all values for searching
    def set_and_search(self, rmsd_cutoff, number_structs, database, full_matches):
        print 20

        # Set RMSD cutoff
        cmd.get_wizard().set_rmsd(rmsd_cutoff)

        # Set number of structures
        cmd.get_wizard().set_num_structures(number_structs)

        # Set Database
        if database == "Test DB":
            cmd.get_wizard().set_database("Test")
        elif database == "Full DB":
            cmd.get_wizard().set_database("Full")

        # Set Full matches
        if full_matches == "Region":
            cmd.get_wizard().set_full_matches(False)
        elif full_matches == "Full":
            cmd.get_wizard().set_full_matches(True)
    
        # Launch the search
        cmd.get_wizard().launch_search()
        print 21

    # Remake the optionmenu
    def refresh_id_options(self):
        print 10
        searches = cmd.get_wizard().searches
        self.search_id.set(searches[0])
        search_id = tk.OptionMenu(self, self.search_id, *searches).grid(row=10, column=1, rowspan=2, sticky=N+E+S+W)
        print 11


class PageOne(tk.Frame):
    
    def __init__(self, parent, controller):
        print 1
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="No ID Selected", font=TITLE_FONT)
        label.pack(side="top", fill="x", pady=10)
        button = tk.Button(self, text="Home", command=lambda: controller.show_frame("StartPage", 0, None))
        button.pack()
        print 2
        
    def show_sequence_logo(self):
        print 3
        cmd.get_wizard().logo_helper(1)
        print 4


class PageTwo(tk.Frame):
    
    def __init__(self, parent, controller):
        print 5
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="No ID Selected", font=TITLE_FONT)
        label.pack(side="top", fill="x", pady=10)
        button = tk.Button(self, text="Home", command=lambda: controller.show_frame("StartPage", 0, None))
        button.pack()
        print 6
    
    def show_frequency_logo(self):
        print 7
        cmd.get_wizard().logo_helper(2)
        print 8
        
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""




