import sys, time, os
import numpy as np
import pandas as pd
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.uic import loadUi

from InstrumentControl import SR530, SR530demo, ArduinoStageController, ArduinoStageControllerDemo

#Stuff for plotting
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib
import matplotlib.pyplot as plt


class thzWindow(QDialog):
    def __init__(self):
        super(thzWindow, self).__init__()
        loadUi('thzScan.ui', self)
        self.setWindowTitle('THz Scan GUI')

        # A hack is needed to start the drop down menus in a sane place.
        self.ddSens.setCurrentIndex(18)
        self.ddTc.setCurrentIndex(7)

        ########################################################################
        ##           Load InstrumentControl classes and initiate              ##
        ########################################################################
        #Check for os:
        if os.name == 'nt': #Respond to windows platform
            print('Identified Windows OS')
            portLIA = 'com3' #Prolific driver
            portStage = 'com4' #Arduino Uno ID
        elif os.name == 'posix':
            print('Identified Mac OS')
            portLIA = '/dev/tty.usbserial'
            portStage = '/dev/tty.usbmodem1421'
        else:
            print('CRITICAL: Unidentified OS.')

        '''Change this line to SR530demo, for the demo-mode'''
        #self.lia = SR530(portLIA, 19200)
        self.lia = SR530demo(portLIA, 19200)
        self.lia.connect()
        time.sleep(0.25)
        self.lia.standard_setup()

        #Run basic sanity checks for the LIA connection
        response = self.lia.query('W')
        if response != [b'0\r']:
            print('Error: Connection to LIA unsuccesful. Files will not be saved')
            self.update_statusbar('CRITICAL: LIA connection not available!')
            self.save_files = False
        else:
            self.save_files = True



        #self.stage = ArduinoStageController(portStage, 9600)
        self.stage = ArduinoStageControllerDemo(portStage, 9600)
        self.stage.connect()
        self.stage.initialize()


        ########################################################################
        ##           Define execution control variables                       ##
        ########################################################################
        self.StopRunFlag = False
        self.IsHomedFlag = False
        self.SaveAllFlag = False
        self.SaveOnStop = False

        self.dataX = np.array([])
        self.dataY = np.array([])
        self.dataStep = np.array([])
        garbage = self.estimate_scan_time()

        ########################################################################
        ##           Set up windows and figures for plotting                  ##
        ########################################################################
        # a figure instance to plot on
        self.figure = Figure()
        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.canvas = FigureCanvas(self.figure)
        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar = NavigationToolbar(self.canvas, self)
        #Scale any fonts accordingly.
        if os.name == 'posix':
            matplotlib.rcParams.update({'font.size': 5})

        # Insert the widgets at appropriate places, and replace the placeholder widget.
        self.verticalLayout.insertWidget(0, self.toolbar)
        self.verticalLayout.replaceWidget(self.wplot, self.canvas)


        ########################################################################
        ##           Define signals and slots for buttons                     ##
        ########################################################################
        self.btnStart.clicked.connect(self.btnStart_clicked)
        self.btnStop.clicked.connect(self.btnStop_clicked)
        self.btnRealtime.clicked.connect(self.btnRealtime_clicked)
        self.btnGoto.clicked.connect(self.btnGoto_clicked)
        self.btnUpdate.clicked.connect(self.btnUpdate_clicked)
        self.cbSaveall.stateChanged.connect(self.update_savestate)

    #@pyqtSlot()

    ############################################################################
    ##           Define button functions                                      ##
    ############################################################################

    def btnStart_clicked(self):
        try:
            self.lia.demo_measure_reset() #should be removed when out of dev
        except AttributeError:
            pass
        self.update_statusbar('Starting scan')
        self.reset_data_array()
        self.StopRunFlag = False
        self.SaveOnStop = False #It defaults to the end of the loop where it saves, anyway.

        self.generate_plot()
        # update step point
        self.PresentPosition = self.nStart.value()
        # goto start of scan range

        #self.stage.move(self.PresentPosition)
        # wait for stage controller to arrive


        #loop through n steps:
        length_of_scan = int((self.nStop.value() - self.nStart.value()) / self.nStepsize.value())
        for i in range(length_of_scan):

            #Check for stop flag
            if self.StopRunFlag == True:
                break

            # Measure data
            measurement = self.high_level_measure()

            #append data to dataarray
            self.dataX = np.append(self.dataX, measurement[0])
            self.dataY = np.append(self.dataY, measurement[1])
            self.dataStep = np.append(self.dataStep, self.PresentPosition)

            #Increment the PresentPosition controller variable
            self.PresentPosition = self.PresentPosition + self.nStepsize.value()

            #Execute move start
            self.stage.move(self.PresentPosition)

            #Execute post move wait
            self.interruptable_sleep(self.post_move_wait_time)

            #Update plot
            self.update_plot()

            #every n datapoints save the data
        #plt.pause(0.0001)

        self.save_data_array()

    def btnStop_clicked(self):
        self.update_statusbar('Stopping scan')
        self.StopRunFlag = True
        if self.SaveOnStop:
            self.save_data_array()
        self.lia.send('I0')

    def btnRealtime_clicked(self):
        self.update_statusbar('Realtime display started')
        self.StopRunFlag = False
        self.SaveOnStop = False #This measurement is made for alignment only, and will not be saved.
        self.lia.send('I 1')

        #Initialize the data set to zeros and sweet nothings.
        self.dataX = np.zeros(200)
        self.dataY = np.copy(self.dataX)
        self.dataStep = np.arange(200)

        #Generate plot
        self.generate_plot()
        self.PresentPosition = 200

        #Loop until stop button is clicked:
        while not self.StopRunFlag:
            #measure
            measurement = self.high_level_measure()
            #append data to dataarray
            self.dataX = np.append(self.dataX, measurement[0])
            self.dataY = np.append(self.dataY, measurement[1])
            self.dataStep = np.append(self.dataStep, self.PresentPosition)
            # Remove the first entry of the datafiles:
            self.dataX = np.delete(self.dataX, 0)
            self.dataY = np.delete(self.dataY, 0)
            self.dataStep = np.delete(self.dataStep, 0)
            #plot
            self.ax.set_xlim([self.dataStep.min(),self.dataStep.max()])
            self.update_plot()

            self.PresentPosition = self.PresentPosition+1

        self.lia.send('I 0')


    def btnGoto_clicked(self):
        self.update_statusbar('Starting Goto')
        self.stage.move(self.nPosition.value())
        self.update_statusbar('Goto value reached')

    def btnUpdate_clicked(self):
        self.update_statusbar('Updating LIA')
        #Update sensitivity
        selected_sens = self.ddSens.currentIndex()
        #print('Sensitivity: '+str(selected_sens))
        self.lia.set_sens(selected_sens)
        #Update filter Tcs
        selected_tc = 10-self.ddTc.currentIndex()
        #print('Time constant: '+str(selected_tc))
        self.lia.set_tc(selected_tc)


    ############################################################################
    ##           Define update, save and time calc functions                  ##
    ############################################################################

    def high_level_measure(self):
        #print(self.nAvg.value())
        dataX = []
        dataY = []
        for i in range(int(self.nAvg.value())):
            single_measurement = self.lia.measure()
            dataX.append(single_measurement[0]) #the x value
            dataY.append(single_measurement[1]) # append the y value

        return (np.mean(dataX), np.mean(dataY))

    def update_statusbar(self, new_update):
        self.statusBar.setText('Status: '+new_update)

        #As this is an often used function, I will piggy-back on this to ensure
        # the scan time estimate is regularly updated and shown.
        estimated_scan_time = self.estimate_scan_time()
        m, s = divmod(estimated_scan_time, 60)
        h, m = divmod(m, 60)
        self.lblEstduration.setText( "%dhrs, %02dmins, %02dsecs" % (h, m, s) )

    def update_savestate(self):
        if self.cbSaveall.checkState() == 2:
            self.SaveAllFlag = True
        else:
            self.SaveAllFlag = False
        self.update_statusbar('Saves all: '+str(self.SaveAllFlag))

    def estimate_scan_time(self):
        nStart = self.nStart.value()
        nStop = self.nStop.value()
        nStepsize = self.nStepsize.value()
        nPostmove = self.nPostmove.value()
        nAvg = self.nAvg.value()

        #The integers were easy, now the slightly trickier part;
        # Decoding the time constant from the Tc drop down menu.
        textTc = self.ddTc.currentText()
        multiplier, unit = textTc.split(' ')
        if unit == 's':
            Tc = float(multiplier)
        elif unit == 'ms':
            Tc = float(multiplier) * 1e-3

        self.post_move_wait_time = Tc * (1+nPostmove)

        # Sum and multiply the time for the scan: The factor 120 is the velocity in steps/second. This should be tuned.
        time = (Tc * (1+nPostmove) * nAvg + nStepsize * 1/120.0) * (nStop-nStart)/nStepsize

        return time

    def interruptable_sleep(self, wait_time):
        i = 0
        while not self.StopRunFlag and i<int(wait_time*100):
            time.sleep(0.01)
            i += 1

    def reset_data_array(self):
        self.dataX = np.array([])
        self.dataY = np.array([])
        self.dataStep = np.array([])

    def save_data_array(self):
        #The filename expression will be yyyymmdd-hr-mn-ss.dat
        prefix_string = self.fileprefix.text()
        working_directory = os.getcwd()+'/'
        datetime_string = time.strftime('%Y%m%d-%H-%M-%S_')
        fname_string = working_directory+datetime_string+prefix_string+'.dat'
        if self.save_files:
            print('Saving file to '+fname_string)
        else:
            print('Files not saved, as no proper instrument is connected.')

        #Leverage pandas to do the heavy lifting.
        if self.save_files:
            pd.DataFrame(np.array([self.dataX, self.dataY, self.dataStep]).T,
             columns=['X', 'Y', 'step']  ).to_csv(fname_string)


    ############################################################################
    ##           Define plotting and plot update functions                    ##
    ############################################################################

    def generate_plot(self):
        plt.ion()
        # create an axis
        self.ax = self.figure.add_subplot(111)

        # discards the old graph
        self.ax.clear()

        self.lineX, = self.ax.plot(self.dataStep, self.dataX)
        self.lineY, = self.ax.plot(self.dataStep, self.dataY)

        self.ax.set_xlim([self.nStart.value(), self.nStop.value()])

        # refresh canvas
        #self.canvas.draw()

    def update_plot(self):
        self.lineX.set_xdata(self.dataStep)
        self.lineY.set_xdata(self.dataStep)

        self.lineX.set_ydata(self.dataX)
        self.lineY.set_ydata(self.dataY)

        #Crop the axis
        y_min = np.min([self.dataX, self.dataY])
        y_max = np.max([self.dataX, self.dataY])
        diff = y_max - y_min
        self.ax.set_ylim([y_min-diff*0.1, y_max+diff*0.1])

        self.canvas.draw()
        self.canvas.flush_events()
        if os.name == 'posix':
            plt.pause(0.000001)





app = QApplication(sys.argv)
widget = thzWindow()

widget.show()

sys.exit(app.exec_())
