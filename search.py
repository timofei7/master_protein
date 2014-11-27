#!/usr/bin/env python

import re, os

MasterAppPath = 'external/master/master'


class masterapp(object):

    def __init__(self):
        # -----  init ------
        #
        self.foo = 'bar'

    def process(self, query_file, arguments):
        try:
            LhaPickleFile = open(AszFile,'rb')

            self.dcSyllableCount =  pickle.load(LhaPickleFile)
            #print "LOADED SYLLABLES"
        except:
            return( False )

        return( True )

    def preparefile(self, queryfile):
        try:
            pass
        except:
            pass


def main():

    MasterApp = masterapp()

# if run standalone

if __name__ == '__main__':
    main()
