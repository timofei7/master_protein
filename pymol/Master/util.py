import prody

class PDBParser():
		def __init__(self, pdbFile):
				self.pdbFile = pdbFile
				self.initthreeToOne()
				self.res = []

		def getSequence(self):
				if self.res:
						return self.res
				pdb = prody.parsePDB(self.pdbFile)
				hv = pdb.getHierView()
				res = list(hv.iterResidues())
				for residue in res:
						info = []
						threeLetter = residue.getResname()
						info.append(self.map3to1(threeLetter))
						info.append(residue.getChid())
						info.append(str(residue.getResnum()))
						self.res.append(info)
				return self.res


		def map3to1(self, ThreeletterRep):
				return self.pmap[ThreeletterRep]	
		
		def __printSeq(self):
				if not self.res:
						print 'empty sequence'
				else:
						for s in self.res:
								print s+' ',
				print '\n'


		def initthreeToOne(self):
				# 3-letter to 1-letter mapping
				threeToOne = {}
				threeToOne['ALA'] = 'A'
				threeToOne['ARG'] = 'R'
				threeToOne['ASN'] = 'N'
				threeToOne['ASP'] = 'D'
				threeToOne['CYS'] = 'C'
				threeToOne['GLN'] = 'Q'
				threeToOne['GLU'] = 'E'
				threeToOne['GLY'] = 'G'
				threeToOne['HIS'] = 'H'
				threeToOne['HSC'] = 'H'
				threeToOne['HSD'] = 'H'
				threeToOne['HSE'] = 'H'
				threeToOne['HSP'] = 'H'
				threeToOne['ILE'] = 'I'
				threeToOne['LEU'] = 'L'
				threeToOne['LYS'] = 'K'
				threeToOne['MET'] = 'M'
				threeToOne['MSE'] = 'M'
				threeToOne['PHE'] = 'F'
				threeToOne['PRO'] = 'P'
				threeToOne['SER'] = 'S'
				threeToOne['THR'] = 'T'
				threeToOne['TRP'] = 'W'
				threeToOne['TYR'] = 'Y'
				threeToOne['VAL'] = 'V'
				self.pmap = threeToOne;



				
