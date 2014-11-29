#!/bin/sh


diskutil erasevolume HFS+ 'RamDisk' `hdiutil attach -nomount ram://10526720`
rsync -ar --progress /Users/tim/Dropbox/Development/master_protein/bc-30-sc-correct-20141022/ /Volumes/RamDisk/

