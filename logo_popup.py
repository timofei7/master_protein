__author__ = 'Nick'


from Tkinter import *
from constants import *
from logo_thread import *
from pymol import cmd
import math
import tkFileDialog


'''
This is the code for the Sequence Logo UI
'''
def display_logo(app, query, residues, rmsd_cutoff, LOGOurl, flag, plugin):
    """
    This method handles creating a SequenceLogo UI with Tkinter
    """
    window = Toplevel(app.root)
    window.configure(background='black', relief = 'raised', bd = 2)

    if flag == 1:
        logo_filepath = LOGO_CACHE + str(query)+"s.gif"
    elif flag == 2:
        logo_filepath = LOGO_CACHE + str(query)+"f.gif"

    img = PhotoImage(file = logo_filepath)

    logo = Label(window, image=img)
    logo.photo = img;
    logo.pack(fill = BOTH, expand = 1, side = TOP)

    window.update()

    # parse query, add residues to a list for later reference
    residues_str = residues.split()
    residue_list = []

    # selected list lets us check if the residue is selected or not
    selected_list = []

    for residue_str in residues_str:
        residue = residue_str.split(',')
        residue_list.append(residue)
        selected_list.append(False)

    # some temporary values to play around with
    total_width = 1.5*(len(residue_list)) + 1.905
    left_margin = 53
    right_margin = 14

    total_num_residues = len(residue_list)

    # set up empty initial selection object used by PyMol to group selections
    cmd.select("curPos", "none")

    # create the textbox with the residue names
    textview = Text(window, height = 1, width = int(total_width), font=("Courier", 15))
    textview.config(highlightthickness = 0, bd = 0,) # remove border
    textview.config(cursor = 'left_ptr') # stylistic options
    textview.config(background = 'black')
    textview.config(foreground = 'green2')
    textview.config(selectbackground = 'black')
    textview.pack(side = BOTTOM, fill = BOTH, expand = 1, padx = (left_margin, right_margin))

    # set up the indices that will change on click down and up, respectively
    start = -1

    for i in range(0, total_num_residues):

        # add the residue character into the string, with the associated tag
        textview.tag_configure(str(i))
        textview.insert(END, residue_list[i][0], str(i))

    textview.config(state=DISABLED)

    def mouse_down(event):
        global start

        # try to get the index based on the click coordinates
        i = int(math.ceil((event.x-3)/9))

        # make sure you are in the window
        if(event.y>20 or event.y<2):
            return

        # must be a valid index
        if(i >= total_num_residues):
            return

        # set the start index of the dragging
        start = i

        # handle selection/deselection
        if(selected_list[i]):
            textview.tag_configure(str(i), background ='black')
            textview.tag_configure(str(i), foreground = 'green2')
            residue_deselect(i)
            selected_list[i] = False
        else:
            textview.tag_configure(str(i), background ='green2')
            textview.tag_configure(str(i), foreground = 'black')
            residue_select(i)
            selected_list[i] = True

    def mouse_drag(event):
        # try to get the index of the selected characters, and look up residue for selection
        global start
        i = int(math.ceil((event.x-3)/9))

        # must be a valid index
        if(i >= total_num_residues):
            return

        # don't worry about the one you just selected
        if start != i:
            start = i

            # handle selection/deselection
            if selected_list[i]:
                textview.tag_configure(str(i), background ='black')
                textview.tag_configure(str(i), foreground = 'green2')
                residue_deselect(i)
                selected_list[i] = False

            else:
                textview.tag_configure(str(i), background ='green2')
                textview.tag_configure(str(i), foreground = 'black')
                residue_select(i)
                selected_list[i] = True


    def residue_select(i):
        print 'click search chain '+residue_list[i][1]+' num '+residue_list[i][2]
        cmd.select("curPos", "curPos or (chain " + residue_list[i][1] + " and resi " + residue_list[i][2] + ")")
        sys.stdout.flush()

    def residue_deselect(i):
        cmd.select("curPos", "curPos and not (chain " + residue_list[i][1] + " and resi " + residue_list[i][2] + ")")

    # this should bind the highlight event to the test event
    textview.bind("<Button-1>", mouse_down)
    textview.bind("<B1-Motion>", mouse_drag)

    def saveFile():

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

    def getLogoFile(filepath):
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

    # create menu and dropdowns
    menubar = Menu(window)

    filemenu= Menu(menubar,tearoff=0)
    filemenu.add_separator()
    filemenu.add_command(label="Save", command=saveFile)
    filemenu.add_separator()
    filemenu.add_command(label="Close", command=window.destroy)
    menubar.add_cascade(label="File", menu=filemenu, underline = 0)

    helpmenu=Menu(menubar,tearoff=0)
    helpmenu.add_separator()
    helpmenu.add_command(label="Help")
    menubar.add_cascade(label="Help",menu=helpmenu, underline = 0)

    window.config(menu=menubar)

    window.after(100, cmd.get_wizard().update())
    window.mainloop()