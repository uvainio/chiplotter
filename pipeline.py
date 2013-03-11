# -*- coding: utf-8 -*-
"""
Created on Tue Jan 08 15:32:08 2013

Pipeline script to automatically download and to process data with Fit2d.

Author: Ulla Vainio (ulla.vainio@hzg.de)
"""

##################### ------------------

# Which txt file contains the integration parameters
cakefile1 = "mycakeparameters1.txt"
#cakefile2 = "mycakeparameters2.txt"
#cakefile3 = "mycakeparameters3.txt"
#cakefile4 = "mycakeparameters4.txt"

# Local directory in which or in the subdirectories of which
# all the data that needs to be integrated is found
localdir1 = 'D:/data/temp'
# Directory where the Python macros are found, must be a subdirectory
# of 'localdir1'
setupdir = "D:/data/temp/setup"

###################### -----------------

# Append python files to the path and import necessary libraries
import sys
sys.path.append(setupdir)
import speedyprocessing as sp

# Integrate data using the parameters defined in the cakefile
sp.automatedcakes(cakefile1,localdir1)
#sp.automatedcakes(cakefile2,localdir1)
#sp.automatedcakes(cakefile3,localdir1)
#sp.automatedcakes(cakefile4,localdir1)
