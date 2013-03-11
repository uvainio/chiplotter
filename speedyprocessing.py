# -*- coding: utf-8 -*-
"""
Created on Tue Jan 08 15:35:43 2013

Pipeline class for P07 automated data processing

Author: Ulla Vainio (ulla.vainio@hzg.de)
"""

import os
import numpy as np
import subprocess
import re
import errno

def automatedcakes(parameterfilename,localdir1):
    """
    Created on Tue Nov 27 09:28:38 2012

    Script creating automated cake integrations from all files in the directory and
    in all subdirectories, as defined by files myfit2dparams.txt and mycakeparams.txt

    Use "Run number" to separate runs with different angle ranges
    so that the different runs are saved in different subdirectories.

    Note:
    
    When saving more than one azimuthal bin, the data is saved as 2-D ASCII.
    This works only if the path and file name are not too long,
    so use short paths and filenames, in total less than 80 caharacters!    

    When using this script on Windows 7, make sure the UAC (User account control)
    is disabled! Otherwise the script cannot start Fit2d.

    @author: Ulla Vainio (ulla.vainio@hzg.de)
    """
    os.chdir(localdir1)
    fit2dversion = "fit2d_12_077_i686_WXP.exe"
    print ""
    # First look for the parameter file in the directories
    # Note, we take the first file we find!
    counter = 0
    parameterfilefound = 0
    for dirpath, dirnames, filenames in os.walk(os.getcwd()):
        for file1 in filenames:
            if file1 == parameterfilename and counter == 0:
                paramfile = "%s/%s" % (dirpath,file1)
                print "Parameter file %s" % paramfile
                counter = counter + 1
                with open(paramfile,'r') as f:
                    parameters = f.readlines()
                f.close()
                parameterfilefound = 1
    print ""
    if parameterfilefound == 0:
        print "Parameter file %s was NOT FOUND anywhere in the directory! Program will exit." % parameterfilename
        os.system("pause")
        exit(0)
    
    errorsfound = 0
    # Write the parameters into variables which are easier to identify
    # and more importantly, transform them to the format required by Fit2d
    cake_azimuth_start   = float(parameters[1])
    cake_azimuth_end     = float(parameters[3])
    cake_inner_radius    = float(parameters[5])
    cake_outer_radius    = float(parameters[7])
    cake_radial_bins     = int(np.min([cake_outer_radius-cake_inner_radius,float(parameters[9])]))
    cake_azimuthal_bins  = int(parameters[11])
    if parameters[13][:2] == "NO":
        maskfile = 'mask.msk'
        maskyesno = 'NO'
        print "NO mask."
    else:
        maskfile = parameters[13][:len(parameters[13])-1]
        maskyesno = 'YES'
        print "Mask file: %s" % maskfile
    if parameters[15][:2] == "NO":
        dcfile = 'darkcurrent.bin'
        dcyesno = 'NO'
        print "NO dark current subtraction."
    else:
        dcfile = parameters[15][:len(parameters[15])-1]
        dcyesno = 'YES'
        print "Dark current file: %s" % dcfile
    beam_center_x       = float(parameters[17])
    beam_center_y       = float(parameters[19])
    wavelength          = float(parameters[21])
    sample_to_detector_distance = float(parameters[23])
    pixel_size_x        = float(parameters[25])
    pixel_size_y        = float(parameters[27])
    detector_tilt_rotation = float(parameters[29])
    detector_tilt_angle = float(parameters[31])
    detector = parameters[33][:len(parameters[33])-1]
    print "Detector: %s" % detector
    if detector == 'mar345':
        pixels1 = 3450
        pixels2 = 3450
        file_extension = ".mar3450"
    elif detector == 'perkinelmer':
        pixels1 = 2048
        pixels2 = 2048
        file_extension = ".tif"
    elif detector == 'pilatus300k':
        pixels1 = 487
        pixels2 = 619
        file_extension = ".tif"
    else:
        errorsfound = 1
        print "Unknown detector %s!" % detector
        print "Cannot proceed with processing."
    fit2dpath           = parameters[35][:len(parameters[35])-1]
    scantype            = parameters[37][:len(parameters[37])-1]
    if parameters[39][:2]=='NO':
        overwriting     = 0 # Integrate only files for which integrated files do not existAlways integrate everything
    else: # Assuming it's YES
        overwriting     = 1 # Always integrate everything
    if parameters[41][:3]=='OFF': # OFF
        pausing         = 0 # Don't pause
    else: # Assuming it's ON
        pausing         = 1 # Always pause
    subdirname = "integ_"+str(parameters[43])


    print " "
    if pausing == True:
        os.system("pause")
    if errorsfound > 0:
        exit(0)

    # Start writing the fit2d macro file for integrating the 2D data
    f = open(fit2dpath+"/fit2d.mac",'w')
    print >>f, '%!*'+'\\'+' BEGINNING OF GUI MACRO FILE'
    print >>f, '%!*'+'\\'
    print >>f, '%!*'+'\\ This is a comment line'
    print >>f, '%!*'+'\\'

    print >> f,'I ACCEPT'
    print >> f,'POWDER DIFFRACTION (2-D)'

    # Counting how many file names exceed 80 characters for *.asc files
    errors = 0
    counterfiles = 0
    for dirpath, dirnames, filenames in os.walk(os.getcwd()):
        if dirpath[len(dirpath)-len(subdirname):] != subdirname:
            for file1 in filenames:
                prefix,postfix = os.path.splitext(file1)
                subdirprefix1 = re.findall("[\S\d]*(?=_|-)",prefix)
                if len(subdirprefix1)>0:
                    subdirprefix = subdirprefix1[0]
                else:
                    subdirprefix = ''
                subpath = dirpath+"/"+subdirprefix+'/'+subdirname+"/"
                # As a default overwrite
                overwritingthisone = 1
                # If files exist, then don't overwrite if not allowed
                if os.path.isfile(subpath+prefix+".chi") and cake_azimuthal_bins==1 and overwriting==True:
                    overwritingthisone = 1
                elif os.path.isfile(subpath+prefix+".chi") and cake_azimuthal_bins==1 and overwriting==False:
                    overwritingthisone = 0
                    print "Did not overwrite: %s" % subpath+prefix+".chi"
                elif os.path.isfile(subpath+prefix+".asc") and cake_azimuthal_bins>1 and overwriting==True:
                    overwritingthisone = 1
                elif os.path.isfile(subpath+prefix+".asc") and cake_azimuthal_bins>1 and overwriting==False:
                    overwritingthisone = 0
                    print "Did not overwrite: %s" % subpath+prefix+".asc"
                # Compare extensions to find only the 2D files
                # Only accept the ones which are allowed to be overwritten
                if postfix == file_extension and overwritingthisone==True:
                    try: # Try creating the subdirectory for integrated files if it does not exist
                        os.makedirs(subpath)
                    except OSError as exc: # Python >2.5
                        if exc.errno == errno.EEXIST and os.path.isdir(subpath):
                            pass
                    if counterfiles == 0:
                        print "Preparing a fit2d.mac for files:"
                    counterfiles = counterfiles + 1
                    fullfile1 = dirpath+"/"+file1
                    print fullfile1
                    # Write to fit2d.mac
                    print >>f, "INPUT"
                    print >>f, fullfile1
                    # For some reason Pilatus 300k seems to require an extra OK
                    if detector == 'pilatus300k' or detector == 'perkinelmer':
                        print >>f, "O.K."
                    # Define common parameters
                    print >>f, "DARK CURRENT"
                    print >>f, dcyesno
                    print >>f, "DC FILE"
                    print >>f, dcfile
                    print >>f, "O.K."
                    print >>f, "CAKE"
                    if counterfiles == 1:
                        print >>f, "NO CHANGE"
                        print >>f, "           1"
                        print >>f, " 3.1346145E+03"
                        print >>f, " 1.7431051E+03"
                        print >>f, "           1"
                        print >>f, " 3.0989375E+03"
                        print >>f, " 1.7074276E+03"
                        print >>f, "           1"
                        print >>f, " 1.8680677E+03"
                        print >>f, " 1.7431051E+03"
                        print >>f, "           1"
                        print >>f, " 3.4200337E+03"
                        print >>f, " 1.7163469E+03"
                    if maskyesno == 'YES':
                        print >>f, "MASK"
                        print >>f, "LOAD MASK"
                        print >>f, maskfile
                        print >>f, "EXIT"
                    print >>f, "INTEGRATE"
                    print >>f, "X-PIXEL SIZE"
                    print >>f, pixel_size_x
                    print >>f, "Y-PIXEL SIZE"
                    print >>f, pixel_size_y
                    print >>f, "DISTANCE"
                    print >>f, sample_to_detector_distance
                    print >>f, "WAVELENGTH"
                    print >>f, wavelength
                    print >>f, "X-BEAM CENTRE"
                    print >>f, beam_center_x
                    print >>f, "Y-BEAM CENTRE"
                    print >>f, beam_center_y
                    print >>f, "TILT ROTATION"
                    print >>f, detector_tilt_rotation
                    print >>f, "ANGLE OF TILT"
                    print >>f, detector_tilt_angle
                    print >>f, "O.K."
                    print >>f, "START AZIMUTH"
                    print >>f, cake_azimuth_start
                    print >>f, "END AZIMUTH"
                    print >>f, cake_azimuth_end
                    print >>f, "INNER RADIUS"
                    print >>f, cake_inner_radius
                    print >>f, "OUTER RADIUS"
                    print >>f, cake_outer_radius
                    print >>f, "SCAN TYPE"
                    if scantype == 'TTH':
                        print >>f, "2-THETA"
                    elif scantype == 'Q':
                        print >>f, "Q-SPACE"
                    elif scantype == 'RADIAL':
                        print >>f, "RADIAL"
                    else:
                        print "SCAN TYPE NOT IDENTIFIED! USE TTH, Q or RADIAL."
                    print >>f, "1 DEGREE AZ"
                    print >>f, "YES"
                    print >>f, "AZIMUTH BINS"
                    print >>f, cake_azimuthal_bins
                    print >>f, "RADIAL BINS"
                    print >>f, cake_radial_bins
                    print >>f, "POLARISATION"
                    print >>f, "NO"
                    print >>f, "CONSERVE INT."
                    print >>f, "NO"
                    print >>f, "GEOMETRY COR."
                    print >>f, "YES"
                    print >>f, "MAX. D-SPACING"
                    print >>f, 1000.00000
                    print >>f, "O.K."
                    print >>f, "EXIT"
                    print >>f, "OUTPUT"
                    if cake_azimuthal_bins>1:
                        print >>f, "2-D ASCII"
                        print >>f, "NO"
                        print >>f, subpath+prefix+".asc"
                        if len(subpath+prefix+".asc") > 79:
                            print "WARNING! Path is too long for saving *.asc files"
                            print subpath+prefix+".asc exceeds limit (80 caharacters). Length %d." % len(subpath+prefix+".asc")
                            errors = errors + 1
                        print >>f, "YES"
                    else:
                        print >>f, "CHIPLOT"
                        print >>f, "FILE NAME"
                        print >>f, subpath+prefix+".chi"
                        print >>f, "OUTPUT ROWS"
                        print >>f, "YES"
                        print >>f, "ROW NUMBER"
                        print >>f, "1"
                        print >>f, "COLUMN NUMBER"
                        print >>f, "1"
                        print >>f, "O.K."
    # Exit Fit2d at the end
    print >>f, "EXIT"
    print >>f, "EXIT"
    print >>f, "YES"
    print >>f, '%!*'+'\\'+' END OF IO MACRO FILE'
    f.close() # Close fit2d macro file

    if pausing == True:
        os.system("pause")            

    # Change directory to Fit2d directory and execute only if macro was filled
    if counterfiles > 0 and errors == 0:
        print ""
        print "Succesfully created fit2d.mac"
        print ""
        os.chdir(fit2dpath)
        print "Executing: %s" % str(fit2dversion+' -dim'+str(pixels1)+'x'+str(pixels2)+' -macfit2d.mac')
        # Execute the created Fit2d macro with Fit2d
        p = subprocess.Popen(str(fit2dversion+' -dim'+str(pixels1)+'x'+str(pixels2)+' -macfit2d.mac'))
        p.wait()
    else:
        print "Did not execute Fit2d because the filenames are too long or"
        print "there were no files that needed to be integrated."

    print ""
    if overwriting == False:
        print "Note! Overwriting of existing .chi and .asc files is disabled"
        print "in the parameter file. To change this, edit the parameter file:"
        print paramfile       

    print ""
    print "End of script."
    # Pause just to give the chance for the user to look at the output before closing the shell.
    if pausing == True:
        os.system("pause")
