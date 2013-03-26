"""Chiplotter""" is a GUI designed for easy plotting of Fit2d generated chi files.
The GUI provides also a way to create Fit2d macros for integration.
Edit the "pipeline.py" and "mycakeparameters1.txt" to select the correct
integration parameters, and add more parameter files if you wish to integrate
different sections.

To install this package: 
1. Download Python x,y 2.7 from http://code.google.com/p/pythonxy/wiki/Downloads

2. Download these macros as a zip file (the little button ZIP up there)
and copy them to an empty folder with a nice name. E.g. D:/XRDmacros

If you only want to plot premade *.chi files, you are now ready go, just double
click on "chiplotter.py".

If you wish to integrate data, then follow the instructions below:
-------------------

3. Download Fit2D to some folder from http://ftp.esrf.eu/pub/expg/FIT2D/
Select fit2d_12_077_i686_WXP.exe. If you already use Fit2D and you have it on your computer,
there is no need to download it again.

4. In pipeline.py change the correct path to "localdir1" (where your data is) and "fit2ddir"
(where your fit2d_12_077_i686_WXP.exe is).

5. Double click on chiplotter.py and make sure the directory is the main directory
where you have your "setup" folder. Click "Integrate". The example file LaB6_0003.mar3450
should now be integrated by Fit2D and a new subdirectory with name "integ_1"
should appear with the corresponding LaB6_0003.chi file in it.

6. If everything works fine so far, you may copy the setup directory to where you have your
real files which you want to intergate and change the parameters in the mycakeparameters1.txt,
create more such parameter files and correspondingly change the pipeline.py to integrate
with more parameter files. Don`t forget to change also the "localdir1" directory to the main
directory where your files should be found (either in the main directory or in subdirectories).

Remember, when plotting, you can put the "Directory" in the GUI to any directory,
but for integrating it must always be the directory in which there is a "setup" subfolder.
This is simply to increase safety. The program should only integrate the data with the parameters
that are in the "setup" folder.


-------------------
This program comes without any warranty! Please report all bugs to ulla.vainio@hzg.de
