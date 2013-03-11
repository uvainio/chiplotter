"""!/usr/bin/env python2.7

*.chi plotter

Based on code from:
http://carles.lambdafunction.com/blog/python-guiqwt-curveplot-toolbar-legend/#respond
 encoding: utf-8

Created 20.12.2012 Ulla Vainio (ulla.vainio@hzg.de)
"""

import sys
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *
import time
import os
import re

from guiqwt.plot import CurvePlot, PlotManager
from guiqwt.tools import SelectPointTool
from guiqwt.builder import make
import guiqwt
import numpy as np
import matplotlib.mlab as mm
import random
import copy

class GuiQwtPlot( QtGui.QMainWindow ):

    def __init__( self ):
        QtGui.QMainWindow.__init__( self )
        self.__create_layout()
        self.__setup_layout()

    def __create_layout( self ):
        
        self.setWindowTitle( "Live *.Chi plotter, v. 2.0.0 (Jan 2013)" )

        self.plot = CurvePlot( self )
        self.plot.set_antialiasing( True )
        self.plot2 = CurvePlot( self )
        self.plot2.set_antialiasing( True )
        self.button = QtGui.QPushButton( "Search for files" )
        self.button2 = QtGui.QPushButton( "Plot selected files" )
        self.button3 = QtGui.QPushButton( "Select all" )
        self.button4 = QtGui.QPushButton( "Select none" )
        self.button5 = QtGui.QPushButton( "Download and integrate" )
        self.button6 = QtGui.QPushButton( "Integral over ROI (defined by the two vertical cursors)" )
    
        left_hbox0 = QtGui.QVBoxLayout()
        right_hbox0 = QtGui.QVBoxLayout()

    # Main graph
        left_vbox = QtGui.QVBoxLayout()
        left_vbox.addWidget( self.plot, 3)

    # Smaller graph
        left_vbox.addWidget( self.plot2, 1 )
        self.tick_axis_reset = QtGui.QCheckBox("Reset axis when replotting data")
        self.tick_axis_reset.setCheckState(Qt.Checked)
        left_hbox0.addWidget( self.tick_axis_reset )
        # Static text field
        right_hbox0.addWidget( QtGui.QLabel('Directory'), 0, QtCore.Qt.AlignRight )
        hbox0 = QtGui.QHBoxLayout()
        hbox0.addLayout( left_hbox0 )
        hbox0.addLayout( right_hbox0 )

        left_vbox.addLayout( hbox0 )
        # Add buttons to the left side
        left_vbox.addWidget( self.button )
        left_vbox.addWidget( self.button2 )
        left_vbox.addWidget( self.button6 )
        
        # Data series list view
        log_label = QtGui.QLabel("Data series:")
        self.series_list_model = QtGui.QStandardItemModel()
        self.series_list_view = QtGui.QListView()
        self.series_list_view.setModel(self.series_list_model)
        
        right_vbox = QtGui.QVBoxLayout()
        right_vbox.addWidget( log_label )
        right_vbox.addWidget( self.series_list_view )
        
        # Create editable text box for inputting directory
        self.text1 = QtGui.QTextEdit()
        self.text1.setFixedHeight(22)
        # Put current directory to the text box
        self.text1.setText(os.getcwd())
        right_vbox.addWidget( self.text1 )
        # Add buttons
        right_vbox.addWidget( self.button3 )
        right_vbox.addWidget( self.button4 )
        right_vbox.addWidget( self.button5 )
        
        # Combine left and right box
        hbox = QtGui.QHBoxLayout()
        hbox.addLayout( left_vbox, 2 ) # Second parameter is the stretch factor
        hbox.addLayout( right_vbox, 1 ) # of the widget, letting the figure to stretch more

        w = QtGui.QWidget()
        w.setLayout( hbox )

        self.setCentralWidget( w )

    def __setup_layout( self ):
        
        self.connect( self.button, QtCore.SIGNAL( 'clicked()' ), self.button_Click )
        self.connect( self.button2, QtCore.SIGNAL( 'clicked()' ), self.button_Click2 )
        self.connect( self.button3, QtCore.SIGNAL( 'clicked()' ), self.button_Click3 )
        self.connect( self.button4, QtCore.SIGNAL( 'clicked()' ), self.button_Click4 )
        self.connect( self.button5, QtCore.SIGNAL( 'clicked()' ), self.button_Click5 )
        self.connect( self.button6, QtCore.SIGNAL( 'clicked()' ), self.button_Click6 )
        
        # Vertical cursor
        self.cursorposition = 0.8
        self.cursorposition2 = 1.2
        self.vcursor1 = make.vcursor(self.cursorposition,  label='x = %.2f')
        self.plot.add_item( self.vcursor1 )
        self.vcursor2 = make.vcursor(self.cursorposition2,  label='x = %.2f')
        self.plot.add_item( self.vcursor2 )

        # Define the y label, x might change depending on user definition
        CurvePlot.set_axis_title(self.plot,CurvePlot.Y_LEFT,"Intensity (counts)")

        # Crate the PlotManager
        self.manager = PlotManager( self )
        self.manager.add_plot( self.plot )
        self.manager.add_plot( self.plot2 )

        # Create Toolbar
        toolbar = self.addToolBar( 'tools' )
        self.manager.add_toolbar( toolbar, id( toolbar ) )

        # Register the ToolBar's type
        self.manager.register_all_curve_tools( )
#        self.manager.register_other_tools()

        # Register a custom tool
        self.manager.add_tool( SelectPointTool, title = 'Position', on_active_item = True, mode = 'create' )
                
    def fill_series_list(self, names):
        self.series_list_model.clear()
        
        counterlist = 0
        for name in reversed(names):
            item = QtGui.QStandardItem(name)
            if counterlist == 0: # Check only the first one
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            item.setCheckable(True)
            self.series_list_model.appendRow(item)
            counterlist = counterlist + 1

# Load data to the list
    def button_Click( self ):
        # Find the newest files in the directory and subdirectories
        # and populate the list of files
        self.y = {}
        self.x = {}
        self.timestamp = {}
        self.names = []
        self.fullfilename = {}

    # Clear the list in case used another directory before
        self.series_list_model.clear()
    # Go to the directory specified in the field or if none, give error message
        curdir = str(self.text1.toPlainText())
        if os.path.isdir(curdir):
            os.chdir(curdir)
        else:
            print curdir+" is not a valid directory!"
            
    # Find the files in the directory
        counterfiles = 0
        for dirpath, dirnames, filenames in os.walk(os.getcwd()):
            filenames.sort(key=lambda x: os.path.getmtime(dirpath+'/'+x))
            for file1 in filenames:
                prefix,postfix = os.path.splitext(file1)
                # Only *.chi files ending with a number are accepted
                if len(re.findall("[\d]"+".chi",file1))>0:
                    fullfilename1 = dirpath+'/'+file1
                    time1 = os.path.getmtime(fullfilename1)
                    tmp,subpath = os.path.split(dirpath)
                    tmp,subpath2 = os.path.split(tmp)
                    seriesname1 = os.path.basename(str(subpath2+'_'+subpath+'_'+file1))
                    self.names.append(seriesname1)
                    # Load data
                    tmp = np.genfromtxt(str(fullfilename1),dtype=None,skip_header=4)
                    self.y[seriesname1] = map(float, np.transpose(tmp[:,1]))
                    self.x[seriesname1] = map(float, np.transpose(tmp[:,0]))
                    self.datalen = len(self.x[seriesname1])
                    self.timestamp[seriesname1] = time1
                    self.fullfilename[seriesname1] = fullfilename1
                    counterfiles = counterfiles + 1
                        
        # Populate the checkbox list
        self.fill_series_list(self.names)
        
#Refresh the figure
    def button_Click2( self ):
#        has_series = False
        
        # Seed for random generator of colors, so that they are always in the same order
        random.seed(654321)
        colorlistred = [220, 255, 155, 24, 0, 0, 48, 205, 255, 255, 0, 142]
        colorlistgreen = [20, 105, 48, 116, 229, 238, 128, 205, 193, 97, 0, 142]
        colorlistblue = [60, 180, 255, 205, 238, 118, 20, 0, 37, 3, 0, 142]
        
        # Clear the plot first
        self.plot.del_all_items()
        # Add back the vertical cursor to the plot in the same position as before
        self.plot.add_item( self.vcursor1 )
        self.plot.add_item( self.vcursor2 )
        
        # For axes take max of 2theta and max of intensity
        maxtth = 0
        maxintensity = 0
        mintth = 100
        minintensity = 100
        # Use first predefined colours, then random
        colorcounter = 0
        # Two simple markers to test if mixed x ranges exist
        foundq = 0
        foundtth = 0
        for row in range(self.series_list_model.rowCount()):
            model_index = self.series_list_model.index(row, 0)
            checked = self.series_list_model.data(model_index,
                Qt.CheckStateRole) == QVariant(Qt.Checked)
            name = str(self.series_list_model.data(model_index).toString())
            
            if checked:
#                has_series = True
                self.curveAlabel = name
                if len(colorlistred) > colorcounter:
                    self.curveA = make.curve( [ ], [ ], self.curveAlabel, QtGui.QColor( colorlistred[colorcounter], colorlistgreen[colorcounter], colorlistblue[colorcounter] ), linewidth=3.0)
                    colorcounter = colorcounter + 1
                else:                    
                    self.curveA = make.curve( [ ], [ ], self.curveAlabel, QtGui.QColor( random.randint(0,255), random.randint(0,255), random.randint(0,255) ), linewidth=3.0)
                self.plot.add_item( self.curveA )

                self.curveA.set_data( self.x[name], self.y[name])
                if max(self.x[name])>maxtth:
                    maxtth = max(self.x[name])
                if max(self.y[name])>maxintensity:
                    maxintensity = max(self.y[name])
                if min(self.x[name])<mintth:
                    mintth = min(self.x[name])
                if min(self.y[name])<minintensity and min(self.y[name]) > 0:
                    minintensity = min(self.y[name])
                # Check if TTH or Q range, redefine x label if Q
                f = open(str(self.fullfilename[name]))
                text1 = f.read()
                f.close()
                if 'Q' in text1:
                    foundq = 1
                    CurvePlot.set_axis_title(self.plot,CurvePlot.X_BOTTOM,"q (1/nm)")
                elif '2-Theta Angle (Degrees)' in text1:
                    foundtth = 1
                    CurvePlot.set_axis_title(self.plot,CurvePlot.X_BOTTOM,"2-theta (degrees)")
                if foundq == 1 and foundtth == 1:
                    CurvePlot.set_axis_title(self.plot,CurvePlot.X_BOTTOM,"Mixed! q (1/nm) and 2-theta (degrees)")                    

        self.legend = make.legend( 'TR' ) # Top Right
        self.plot.add_item( self.legend )
        
        # Reset axis if checkbox is checked, otherwise ignore
        if self.tick_axis_reset.isChecked()==True:
            CurvePlot.set_axis_limits(self.plot,CurvePlot.X_BOTTOM,mintth*0.9,maxtth*1.1)
            CurvePlot.set_axis_limits(self.plot,CurvePlot.Y_LEFT,minintensity*0.9,maxintensity*1.1)

        # Plot everything
        self.plot.replot( )
        
        # Refresh also the integral plot
        self.button_Click6( )

# Select all
    def button_Click3( self ):
        for k in range(0,len(self.names)):
            self.series_list_model.item(k).setCheckState( Qt.Checked )

# Select none
    def button_Click4( self ):
        for k in range(0,len(self.names)):
            self.series_list_model.item(k).setCheckState( Qt.Unchecked )

# Download and integrate button
    def button_Click5( self ):
        curdir = str(self.text1.toPlainText())
        execfile(curdir+"/setup/pipeline.py") 
        # Update file list after integrating
        self.button_Click( )

# Sum over ROI and update the lower graph
    def button_Click6( self ):
        # Clear the plot first
        self.plot2.del_all_items()
        
        # Seed for random generator of colors, so that they are always in the same order
        random.seed(654321)
        colorlistred = [220, 255, 155, 24, 0, 0, 48, 205, 255, 255, 0, 142]
        colorlistgreen = [20, 105, 48, 116, 229, 238, 128, 205, 193, 97, 0, 142]
        colorlistblue = [60, 180, 255, 205, 238, 118, 20, 0, 37, 3, 0, 142]
        markerlist = ['Rect','Diamond', 'UTriangle', 'DTriangle', 'RTriangle','Cross', 'Ellipse', 'Star1', 'XCross', 'LTriangle', 'Star2']

        # Get cursor positions to define ROI
        x1 = guiqwt.shapes.Marker.xValue(self.vcursor1)
        x2 = guiqwt.shapes.Marker.xValue(self.vcursor2)
        if x2 < x1:
            x3 = copy.deepcopy(x1)
            x1 = copy.deepcopy(x2)
            x2 = x3
        indices = []
        
        self.sumy = {}
        self.sumx = {}
        # Use first predefined colours, then random
        colorcounter = 0

        maxsumx = 0
        minsumx = 10000
        maxsumy = 0
        minsumy = 10000000
        self.sumxall = {}
        self.sumyall = {}
        seriesnames = []

        for row in range(self.series_list_model.rowCount()):
            model_index = self.series_list_model.index(row, 0)
            checked = self.series_list_model.data(model_index,
                Qt.CheckStateRole) == QVariant(Qt.Checked)
            name = str(self.series_list_model.data(model_index).toString())

            if checked:
                # Find x values over which to sum
                indices = []
                for index,value in enumerate(self.x[name]):
                    if value > x1 and value < x2:
                        indices.append(index)
                xx = np.array(self.x[name])
                yy = np.array(self.y[name])
                sumy1 = np.trapz(yy[indices],xx[indices])
                self.sumy[name] = [float(sumy1)]
                number1 = re.findall("(?<=_|-)[\d]*(?=.chi)",name)
                sumx1 = int(number1[0])
                self.sumx[name] = [float(sumx1)]
                if max(self.sumx[name])>maxsumx:
                    maxsumx = max(self.sumx[name])
                if max(self.sumy[name])>maxsumy:
                    maxsumy = max(self.sumy[name])
                if min(self.sumx[name])<minsumx:
                    minsumx = min(self.sumx[name])
                if min(self.sumy[name])<minsumy and min(self.sumy[name]) > 0:
                    minsumy = min(self.sumy[name])
                #if len(colorlistred) > colorcounter:
                #    self.curveB = make.curve( [ ], [ ], '', (0,0,0), linewidth=3.0, marker='Rect', markersize=10, markerfacecolor = QtGui.QColor( colorlistred[colorcounter], colorlistgreen[colorcounter], colorlistblue[colorcounter] ))
                #    colorcounter = colorcounter + 1
                #else:
                #    self.curveB = make.curve( [ ], [ ], '', (0,0,0), linewidth=3.0, marker='Rect', markersize=10, markerfacecolor = QtGui.QColor( random.randint(0,255), random.randint(0,255), random.randint(0,255)) )
                #self.plot2.add_item( self.curveB )
                #self.curveB.set_data( self.sumx[name],self.sumy[name] )
                # Check which series names we have
                name1 = re.findall("[\W\S\d]*(?=-[\d]{5}.chi)",name)
                # Try different versions of writing the names if first one does not succeed
                if name1 == []:
                    name1 = re.findall("[\W\S\d]*(?=_[\d]{4}.chi)",name)
                if name1 == []:
                    name1 = re.findall("[\W\S\d]*(?=_[\d]{5}.chi)",name)
                seriesname1 = str(name1[0])
                if seriesname1 not in seriesnames:
                    seriesnames.append(seriesname1)
                    self.sumxall[seriesname1] = []
                    self.sumyall[seriesname1] = []
                self.sumxall[seriesname1].append(sumx1)
                self.sumyall[seriesname1].append(sumy1)

        # Make lines and legends to separate different sample series
        colorcounter = 0
        random.seed(654321)
        markercounter = 0
        for seriesname1 in seriesnames:
                if len(colorlistred) > colorcounter:
                    self.curveB = make.curve( [ ], [ ], seriesname1, QtGui.QColor( colorlistred[colorcounter], colorlistgreen[colorcounter], colorlistblue[colorcounter] ), linewidth=3.0, marker=markerlist[markercounter], markerfacecolor = QtGui.QColor( colorlistred[colorcounter], colorlistgreen[colorcounter], colorlistblue[colorcounter] ), markeredgecolor= QtGui.QColor( colorlistred[colorcounter], colorlistgreen[colorcounter], colorlistblue[colorcounter] ))
                    colorcounter = colorcounter + 1
                    markercounter = markercounter + 1
                else:
                    newcolor = QtGui.QColor( random.randint(0,255), random.randint(0,255), random.randint(0,255))
                    self.curveB = make.curve( [ ], [ ], seriesname1, newcolor, linewidth=3.0, marker=markerlist[markercounter], markerfacecolor = newcolor, markeredgecolor = newcolor )
                    markercounter = markercounter + 1
                if markercounter > len(markerlist):
                    markercounter = 0
                self.plot2.add_item( self.curveB )
                self.curveB.set_data( self.sumxall[seriesname1],self.sumyall[seriesname1] )                
        

        CurvePlot.set_axis_title(self.plot2,CurvePlot.X_BOTTOM,"File number")
        CurvePlot.set_axis_title(self.plot2,CurvePlot.Y_LEFT,"ROI sum")
        
        self.legend2 = make.legend( 'TR' ) # Top Right
        self.plot2.add_item( self.legend2 )

        # Reset axis if ticked
        if self.tick_axis_reset.isChecked()==True:
            CurvePlot.set_axis_limits(self.plot2,CurvePlot.X_BOTTOM,minsumx*0.9,maxsumx*1.1)
            CurvePlot.set_axis_limits(self.plot2,CurvePlot.Y_LEFT,minsumy*0.9,maxsumy*1.1)

        # Plot everything
        self.plot2.replot( )


def main():
    app = QtGui.QApplication( sys.argv )
    prog = GuiQwtPlot( )
    prog.show( )
    sys.exit( app.exec_( ) )


if __name__ == '__main__':
    main()
