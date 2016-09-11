#!/usr/bin/env python
"""
some utility functions
author:   Gevorg Grigoryan, 09/2016
"""


import os
import re
import sys


def logMessage(file, message):
    """
    appends the message to the end of the file
    """
    with open(file, "a") as myfile:
      myfile.write(message + "\n")
