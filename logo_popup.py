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

class WindowApp():
    
    def __init__(self, app):

        # Widget Parents
        self.win = tk.Toplevel(app.root)
        self.win.protocol("WM_DELETE_WINDOW", self.callback)
        self.win.title('MASTER Search')
        
        # Instance variables to be used in logos
        self.win.start = None
        self.win.textview = None
        self.win.sb = None
        self.win.total_num_residues = None
        self.win.selected_list = None
        self.win.residue_list = None
        self.win.img = None
        self.win.logo = None
        self.win.textbox = None
        self.win.width = None
        self.win.height = None
        self.win.coords = None

        # Make a label for RMSD and entry box
        rmsd_label = tk.Label(self.win, text = "RMSD cut").grid(rowspan=2, sticky=N+E+S+W)
        rmsd = tk.DoubleVar(self.win)
        rmsd.set(0.5)
        rmsd_entry = tk.Entry(self.win, textvariable = rmsd).grid(row=0, column=1, rowspan=2, sticky=N+E+S+W)
        
        # Make a label for the Number of Structures value
        num_structs_label = tk.Label(self.win, text = "# matches").grid(row=2, column=0, rowspan=2, sticky=N+E+S+W)
        
        # Make a number of structures selection menu
        num_structs = tk.IntVar(self.win)
        num_structs.set(10)
        matches_entry = tk.Entry(self.win, textvariable = num_structs).grid(row=2, column=1, rowspan=2, sticky=N+E+S+W)
        

        # Make Label and menu selection for database type
        database_label = tk.Label(self.win, text = "Database").grid(row=4, column=0, rowspan=2, sticky=N+E+S+W)
        db = tk.StringVar(self.win)
        db.set("Test DB")
        database_select = tk.OptionMenu(self.win, db, "Test DB", "Full DB").grid(row=4, column=1, rowspan=2, sticky=N+E+S+W)
        
        # Make Label and menu selection for match type
        match_label = tk.Label(self.win, text = "Match type").grid(row=6, column=0, rowspan=2, sticky=N+E+S+W)
        fm = tk.StringVar(self.win)
        fm.set("Region")
        match_select = tk.OptionMenu(self.win, fm, "Region", "Full").grid(row=6, column=1, rowspan=2, sticky=N+E+S+W)

        # Add a search button that calls search when clicked
        search_button = tk.Button(self.win, text="Search", command=lambda: self.set_and_search(float(rmsd.get()), int(num_structs.get()), str(db.get()), str(fm.get()))).grid(row=8, column=0, rowspan=2, columnspan=2, sticky=N+E+S+W)
        
        # Pick search
        self.win.search_id = tk.StringVar(self.win)
        self.win.search_id.set('Search IDs:')
        search_id_button = tk.OptionMenu(self.win, self.win.search_id, 'Search IDs').grid(row=10, column=0, rowspan=2, sticky=N+E+S+W)

        # Info or freq checkbuttons
        logo_choice = tk.IntVar(self.win)
        logo_choice.set(1)
        info_check = tk.Checkbutton(self.win, text="info", variable=logo_choice, onvalue=1, offvalue=2).grid(row=10, column=1, sticky=N+E+S+W)
        freq_check = tk.Checkbutton(self.win, text="freq", variable=logo_choice, onvalue=2, offvalue=1).grid(row=11, column=1, sticky=N+E+S+W)

        # Make a button to run the Sequence Logo
        show_logo_button = tk.Button(self.win, text="Show Logo", command=lambda: self.set_and_display(int(logo_choice.get()), str(self.win.search_id.get()))).grid(row=12, column=0, rowspan=2, sticky=N+E+S+W)
        
        # Make a button to run Frequency Logo
        save_button = tk.Button(self.win, text="Save Logo", command=self.saveFile).grid(row=12, column=1, rowspan=2, sticky=N+E+S+W)
        
        # Labels placeholding for logo graphic
        placeholder = tk.Label(self.win, background='white', text = "                                                                                                                 ").grid(row=0, column=2, rowspan=10, columnspan=3, sticky=N+E+S+W)

        residue_placeholder = tk.Label(self.win, background='white', text = "                                                                                                                 ").grid(row=10, column=2, rowspan=2, columnspan=3, sticky=N+E+S+W)
       
        scrollbar_placeholder = tk.Label(self.win, text = "                                                                                                                 ").grid(row=12, column=2, rowspan=2, columnspan=3, sticky=N+E+S+W)

        # Start make id list
        self.make_ids()
    
    def callback(self):
        cmd.get_wizard().live_app = False
        self.win.destroy()
    

    # Remake ID menu after it been appended to searches
    def make_ids(self):
        
        if cmd.get_wizard().done_adding == True:

            # Set search options and current search
            searches = cmd.get_wizard().searches[0:]
            searches.insert(0, 'Search IDs: ')
            self.win.search_id.set(searches[0])
            
            # Remake window
            search_id = tk.OptionMenu(self.win, self.win.search_id, *searches).grid(row=10, column=0, rowspan=2, sticky=N+E+S+W)
            
            # Reset flag
            cmd.get_wizard().done_adding = False
        
        # Repeat
        cmd.get_wizard().app.root.after(100, self.make_ids)

    
    # Function to set flag and ID number
    def set_and_display(self, flag, id):

        # Set search
        cmd.get_wizard().set_search(int(id[-1])-1)

        # Show logo
        cmd.get_wizard().launch_logo_search(flag)


    # Function to set all values for searching
    def set_and_search(self, rmsd_cutoff, number_structs, database, full_matches):

        # Set RMSD cutoff
        if self.is_num(str(float(rmsd_cutoff))):
            cmd.get_wizard().set_rmsd(float(rmsd_cutoff))
        else:
            print "RMSD cut must be float"

        # Set number of structures
        if self.is_num(str(number_structs)):
            cmd.get_wizard().set_num_structures(number_structs)
        else:
            print "# matches must be integer"

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
        
        # Labels placeholding for logo graphic
        placeholder = tk.Label(self.win, background='white', text = "                                                                                                                 ").grid(row=0, column=2, rowspan=10, columnspan=3, sticky=N+E+S+W)
        
        residue_placeholder = tk.Label(self.win, background='white', text = "                                                                                                                 ").grid(row=10, column=2, rowspan=2, columnspan=3, sticky=N+E+S+W)
        
        scrollbar_placeholder = tk.Label(self.win, text = "                                                                                                                 ").grid(row=12, column=2, rowspan=2, columnspan=3, sticky=N+E+S+W)
        
        if flag == 1:
            logo_filepath = LOGO_CACHE + str(query)+"s.gif"
        elif flag == 2:
            logo_filepath = LOGO_CACHE + str(query)+"f.gif"
        
        self.win.coords = self.get_image_size(logo_filepath)
        self.win.width = self.win.coords[0]

        self.win.img = tk.PhotoImage(file=logo_filepath)
        self.win.textbox = tk.Canvas(self.win)
        self.win.textbox.create_image(self.win.width/2, 100, image=self.win.img)
        self.win.textbox.photo = self.win.img
        self.win.textbox.config(bg='white')
        self.win.textbox.grid(row=0, column=2, rowspan=12, columnspan=4, sticky=N+E+S+W)

        # parse query, add residues to a list for later reference
        residues_str = residues.split()
        self.win.residue_list = []

        # selected list lets us check if the residue is selected or not
        self.win.selected_list = []

        for residue_str in residues_str:
            residue = residue_str.split(',')
            self.win.residue_list.append(residue)
            self.win.selected_list.append(False)

        # some temporary values to play around with
        total_width = 1.5*(len(self.win.residue_list)) + 1.905
        left_margin = 53
        right_margin = 14

        self.win.total_num_residues = len(self.win.residue_list)
        
#        self.win.textbox.create_text(68, 200, text=str(self.win.residue_list[0][0]))
        x = 68
        for each_char in range(len(self.win.residue_list)):
            self.win.textbox.create_text(x, 180, text=str(self.win.residue_list[each_char][0]))
            x += 18.8

        # set up empty initial selection object used by PyMol to group selections
        cmd.select("curPos", "none")
        
        # Create a scrollbar
        self.win.sb = tk.Scrollbar(self.win, orient=tk.HORIZONTAL)
        self.win.sb.grid(row=12, column=2, rowspan=2, columnspan=4, sticky=N+E+S+W)

        # create the textbox with the residue names
        self.win.textview = tk.Text(self.win, height = 1, width = int(total_width), font=("Courier", 15))
        self.win.textview.config(highlightthickness = 0, bd = 0,) # remove border
        self.win.textview.config(cursor = 'left_ptr') # stylistic options
        self.win.textview.config(background = 'white') #black
        self.win.textview.config(foreground = 'black') #green2
        self.win.textview.config(selectbackground = 'white') #black

#        self.win.textview.config(padx=64) #black

#        self.win.textview.grid(row=10, column=2, rowspan=2, columnspan=4, sticky=N+E+S+W)

        # Link the scrollbar and Text widgets
        self.win.sb.config(command=self.scroll_cmd)
        self.win.textview.config(xscrollcommand=self.win.sb.set)
        self.win.textbox.config(xscrollcommand=self.win.sb.set)


        # set up the indices that will change on click down and up, respectively
        self.win.start = -1

        for i in range(0, self.win.total_num_residues):

            # add the residue character into the string, with the associated tag
            self.win.textview.tag_configure(str(i))
            self.win.textview.insert(tk.END, self.win.residue_list[i][0], str(i))
        
        self.win.textview.config(state=DISABLED)
        
        # this should bind the highlight event to the test event
        self.win.textview.bind("<Button-1>", self.mouse_down)
        self.win.textview.bind("<B1-Motion>", self.mouse_drag)

    def scroll_cmd(self, *args):
        self.win.textview.xview(*args)
        self.win.textbox.xview(*args)

    def mouse_down(self, event):
        #global start

        # try to get the index based on the click coordinates
        i = int(math.ceil((event.x-3)/9))

        # make sure you are in the window
        if(event.y>20 or event.y<2):
            return

        # must be a valid index
        if(i >= self.win.total_num_residues):
            return

        # set the start index of the dragging
        self.win.start = i

        # handle selection/deselection
        if(self.win.selected_list[i]):
            self.win.textview.tag_configure(str(i), background ='white') # black
#            self.win.textview.tag_configure(str(i), foreground = 'green2')
            self.residue_deselect(i)
            self.win.selected_list[i] = False
        else:
            self.win.textview.tag_configure(str(i), background ='SteelBlue1') #green2
#            self.win.textview.tag_configure(str(i), foreground = 'black')
            self.residue_select(i)
            self.win.selected_list[i] = True

    def mouse_drag(self, event):
        # try to get the index of the selected characters, and look up residue for selection
        #global start
        i = int(math.ceil((event.x-3)/9))

        # must be a valid index
        if(i >= self.win.total_num_residues):
            return

        # don't worry about the one you just selected
        if self.win.start != i:
            self.win.start = i

            # handle selection/deselection
            if self.win.selected_list[i]:
                self.win.textview.tag_configure(str(i), background ='white')
#                self.win.textview.tag_configure(str(i), foreground = 'green2')
                self.residue_deselect(i)
                self.win.selected_list[i] = False

            else:
                self.win.textview.tag_configure(str(i), background ='SteelBlue1')
#                self.win.textview.tag_configure(str(i), foreground = 'black')
                self.residue_select(i)
                self.win.selected_list[i] = True


    def residue_select(self, i):
        print 'click search chain '+self.win.residue_list[i][1]+' num '+self.win.residue_list[i][2]
        cmd.select("curPos", "curPos or (chain " + self.win.residue_list[i][1] + " and resi " + self.win.residue_list[i][2] + ")")
        sys.stdout.flush()

    def residue_deselect(self, i):
        cmd.select("curPos", "curPos and not (chain " + self.win.residue_list[i][1] + " and resi " + self.win.residue_list[i][2] + ")")

    def get_image_size(self, fname):
#    Determine the image type of fhandle and return its size.
#    http://stackoverflow.com/questions/8032642/how-to-obtain-image-size-using-standard-python-class-without-using-external-lib

        with open(fname, 'rb') as fhandle:
            head = fhandle.read(24)
            if len(head) != 24:
                return
            width, height = struct.unpack('<HH', head[6:10])
            return width, height

    def is_num(self, num):
        for i in range(len(num)):
            if 48 <= ord(num[i]) <= 57 or ord(num[i]) == 46:
                pass
            else:
                return False
        return True

