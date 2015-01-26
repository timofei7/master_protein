#!/bin/sh
#
#  just a script to mount a ramdisk on osx and copy over the datafiles to it
#  author:  Tim Tregubov,  12/2014

diskutil erasevolume HFS+ 'RamDisk' `hdiutil attach -nomount ram://10526720`
echo "copying to ramdisk"
rsync -ar ../bc-30-sc-correct-20141022/ /Volumes/RamDisk/
echo "done!"

