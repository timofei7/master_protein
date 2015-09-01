from constants import *
from Tkinter import *
import random
import os
from PIL import Image
import math
import operator


class LetterLabel(Label):
    def __init__(self, master, letter, width, height):
        Label.__init__(self, master)
        self.letter = letter
        self.width = width
        self.height = height
        self.config(text = str(self.letter))
        self.config(height = self.height, width = self.width)
        self.config(bg = 'blue')



class ResidueLabel(Label):
    '''
    Label with action listeners implemented
    '''
    def __init__(self, master, residue, position, textSize, search_id):
        Label.__init__(self, master)
        self.position = position
        self.residue = residue
        self.textSize = textSize
        self.search_id = search_id
        self.config(width = LOGO_BAR_WIDTH)

        # bind events
        def enter_event(event):
            self.config(bg = "green")
        def leave_event(event):
            self.config(bg = "white")
        def click_one_event(event):
            print 'click search '+self.search_id+' chain '+self.residue[1]+' num '+self.residue[2]
            sys.stdout.flush()

        self.config(text = str(self.residue[0]))
        self.config(bg="white")
        self.bind("<Enter>", enter_event)
        self.bind("<Leave>", leave_event)
        self.bind("<Button-1>", click_one_event)


class LogoGUI(Frame):
    '''
    create a logo GUI frame
    '''
    def __init__(self, search_id, query, seqs, textSize, flag, master = None):
        Frame.__init__(self, master)
        self.search_id = search_id
        self.seqs = seqs
        self.query = query

        # parse query
        residues_str = query.split()
        residues = []
        for residue_str in residues_str:
        	residue = residue_str.split(',')
        	residues.append(residue)

        self.textSize = textSize
        self.pack()
        # init widgets
        header = Frame(self)
        header.pack(side = 'top', fill = X)
        # canvas
        line_frame_cvs = Canvas(self)

        # inner frame
        line_frame = Frame(line_frame_cvs)

        # y-axis
        def create_Y_Axis(numOfBits):
        	# create y axis
	        left_panel = Frame(self)
	        left_panel.pack(side='left', fill = Y, expand = True)
	        yaxis_canvas = Canvas(left_panel, height = LOGO_BAR_HEIGHT, width = 30)
	        yaxis_canvas.pack(side='top', fill=X)
	        yaxis_canvas.create_line(10, 0, 10, LOGO_BAR_HEIGHT) # y axis
	        yaxis_canvas.create_line(0, 1, 10, 1) # top
	        yaxis_canvas.create_line(0, LOGO_BAR_HEIGHT-1, 10, LOGO_BAR_HEIGHT-1) # bottom

	        yaxis_canvas.create_text(0, LOGO_BAR_HEIGHT-15,anchor=NW, text='0')
	        yaxis_canvas.create_text(0, 2,anchor=NW, text=str(int(numOfBits)))

	        if numOfBits > 1:
	        	ht_unit = LOGO_BAR_HEIGHT / numOfBits
	        	base = ht_unit
	        	while numOfBits > 1:
	        		yaxis_canvas.create_line(0, base, 10, base)
	        		yaxis_canvas.create_text(0, base+2,anchor=NW, text=str(numOfBits-1))
	        		base = base + ht_unit
	        		numOfBits -= 1

        # scroll bar
        hbar=Scrollbar(self,orient=HORIZONTAL, command = line_frame_cvs.xview)
        line_frame_cvs.configure(xscrollcommand=hbar.set)
        # pack
        hbar.pack(side=BOTTOM,fill=X)
        line_frame_cvs.pack(side="right", fill=BOTH, expand = True)
        def OnFrameConfigure(event):
            line_frame_cvs.configure(scrollregion=line_frame_cvs.bbox("all"))
        # self.line_frame.pack(side="bottom")
        line_frame_cvs.create_window((0, 0), window = line_frame, anchor="nw")

        line_frame.bind("<Configure>", OnFrameConfigure)

        query_frame = Frame(line_frame)
        query_frame.pack(side='bottom')
        maxRi = 2
        if flag == '1':
            # create sequence logo canvas
            logo_cvs = Logo(self.search_id, self.seqs, isFreq = False, master = line_frame)
            maxRi = logo_cvs.getMaxRi()
            create_Y_Axis(maxRi)
            logo_cvs.pack(side='top', fill = X)
            logo_cvs.pack_propagate(0)
            for i in range(0, len(residues)):
                label_frame = Frame(line_frame, width = LOGO_BAR_WIDTH, height = 20, bd = 1)
                label = Label(label_frame, text = str(i+1))
                label_frame.pack(side = 'left')
                label_frame.pack_propagate(0)
                label.pack(fill = X, side='bottom')
            for i in range(0, len(residues)):
                label_frame = Frame(query_frame, width = LOGO_BAR_WIDTH, height = 20, bd = 1)
                label = ResidueLabel(label_frame, residue = residues[i], position = i, textSize = 20, search_id = self.search_id)
                # self.positions.append(label)
                label_frame.pack(side = 'left')
                label_frame.pack_propagate(0)
                label.pack(fill = X, side='bottom')

        elif flag == '2':
            # create frequency logo canvas
            freq_cvs = Logo(self.search_id, self.seqs, isFreq = True, master = line_frame)
            maxRi = freq_cvs.getMaxRi()
            create_Y_Axis(maxRi)
            freq_cvs.pack(side='top', fill = X)
            freq_cvs.pack_propagate(0)
            for i in range(0, len(residues)):
                label_frame = Frame(line_frame, width = LOGO_BAR_WIDTH, height = 20, bd = 1)
                label = Label(label_frame, text = str(i+1))
                label_frame.pack(side = 'left')
                label_frame.pack_propagate(0)
                label.pack(fill = X, side='bottom')
            for i in range(0, len(residues)):
                label_frame = Frame(query_frame, width = LOGO_BAR_WIDTH, height = 20, bd = 1)
                label = ResidueLabel(label_frame, residue = residues[i], position = i, textSize = 20, search_id = self.search_id)
                label_frame.pack(side = 'left')
                label_frame.pack_propagate(0)
                label.pack(fill = X, side='bottom')



class Logo(Canvas):
	def __init__(self, search_id, seqs, isFreq, master = None):
		Canvas.__init__(self, master)
		self.config(height=LOGO_CANVAS_HEIGHT)
		self.config(bg='grey')
		# self.config(bd=6)
		self.seqs = seqs
		self.search_id = search_id
		# at each position, create a logobar object
		length = len(self.seqs[0])
		PSFM = [] # PSFM matrix
		for i in range(0, length):
			# compute each letter's weight
			components = {}
			for seq in self.seqs:
				residue = seq[i]
				if residue not in components:
					components[residue] = 1
				else:
					components[residue] += 1
			# normalize
			for key in components:
				components[key] /= float(len(self.seqs))
			PSFM.append(components)
			if isFreq:
				bar = LogoBar(self.search_id, components, 2, 2, self)
				bar.pack(side = 'left', fill = Y)
		R, self.maxRi = self.computeRi(seqs, PSFM)
		# plot each position
		if not isFreq:
			for i in range(0, length):
				bar = LogoBar(self.search_id, PSFM[i], R[i], self.maxRi, self)
				bar.pack(side = 'left', fill = Y)

	def computeRi(self, seqs, components):
		e_n = (1 / math.log(2)) * (20 - 1)*1.0/(2*len(seqs))
		R = []
		maxRi = -1
		for i in range(len(seqs[0])):
			# print 'compute ',i
			# compute y-axis for each position i
			# compute entropy of i
			H_i = 0
			for key in components[i]:
				# print 'p', components[i][key]
				H_i += components[i][key] * math.log(components[i][key], 2)
			# print H_i
			H_i = H_i * (-1)
			# print H_i
			Ri = math.log(20, 2) - H_i - e_n
			maxRi = max(maxRi, Ri)
			R.append(Ri)
		# print R
		print R
		sys.stdout.flush
		return R, math.ceil(maxRi)

	def getMaxRi(self):
		return self.maxRi

class LogoBar(Canvas):
	def __init__(self, search_id, components, Ri, maxRi, master = None):
		Canvas.__init__(self, master)
		self.components = components
		self.search_id = search_id
		self.config(bg='white')
		self.config(bd = -1)
		self.config(width = LOGO_BAR_WIDTH, height = LOGO_BAR_HEIGHT)
		# print Ri
		if Ri > 0:
			if Ri > 2:
				Ri = 2
			sorted_c = sorted(components.items(), key=operator.itemgetter(1))
			unit_height = LOGO_BAR_HEIGHT / maxRi
			total_ht = math.floor(unit_height * Ri)
			# for each component, stretch image based on proportion
			for comp in sorted_c:
				# print comp
				# desired height
				height = math.floor(total_ht * self.components[comp[0]])
				# width
				width = LOGO_BAR_WIDTH
				if int(height) != 0:
					# resizeImage
					newFilePath = self.resizeImage(comp[0], height, width)
					rcvs = ResidueCVS(self, newFilePath, height, width)
					rcvs.pack(side = 'bottom')

	def resizeImage(self, residue, height, width):
		# residue = random.choice('ACGT')
		origin = Image.open(IMAGE_PATH+residue+'.png')
		# print width, height
		origin = origin.resize((int(width), int(height)), Image.ANTIALIAS)
		filepath = self.randomFileName()
		# print 'filepath ',filepath
		origin.save(filepath, "png")
		return filepath

	def randomFileName(self):
		# 12-length random file name in cache
		name = []
		up_letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
		digits = '0123456789'
		for i in range(0, RDM_FILE_NAME_LEN):
			l = random.choice(up_letters)
			d = random.choice(digits)
			choice = random.choice((l, d))
			name.append(choice)
		path = ''.join(name)
		return CACHE_PATH+self.search_id+'/'+path + '.png'




class ResidueCVS(Canvas):
    def __init__(self, master, path, height, width):
        Canvas.__init__(self, master)
        self.config(width = width, height = height, highlightthickness=0)
        self.config(bg = 'white')
        self.config(bd = 0)
        self.image = PhotoImage(file=path)
        self.create_image(0, 0, image=self.image,anchor=NW)
        self.pack(side='top')




