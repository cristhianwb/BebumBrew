# -*- coding: utf-8 -*-
import numpy as np

from matplotlib.backends.qt_compat import QtCore, QtWidgets
from matplotlib.backends.backend_qt4agg import (
        FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
import matplotlib.pyplot as plt

import random

class PlotControl(object):
    def __init__(self, ui):        
        #data that will be plotted
        self.data = {
            'sensor1': [],
            'sensor2': [],
            'heater_power': [],
            'pump_power': []
        }
        self.zoom = 1.0
        self.plot_pos = 0.0
        self.window_size = 20
        self.window_count = 1
        #ui treatments
        self.ui = ui
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        layout = ui.tabPlotLay
        layout.insertWidget(0, self.canvas)
        ui.zoomSlider.valueChanged.connect(self.zoom_changed)


    def set_window_size(self):
        sensor1 = self.data['sensor1']
        count = float(len(sensor1))
        window_size = int((count / 100.0) * (100.0 - self.zoom))
        self.window_size = window_size if window_size > 0 else 1
        


    def plot(self, temp1, power, p_power):
        sensor1 = self.data['sensor1']
        sensor1.append(temp1)
        heater_power = self.data['heater_power']
        heater_power.append(power)
        pump_power = self.data['pump_power']
        pump_power.append(int(float(p_power) / 255.0 * 100))
        # instead of ax.hold(False)
        self.figure.clear()
        # create an axis
        ax = self.figure.add_subplot(111)
        # plot data
        ax.plot(sensor1, color = 'green')        
        if self.ui.chkAutoScroll.isChecked() and (self.window_count == 1):
            self.set_window_size()
        count = len(sensor1)
        window_count = int(float(count) / self.window_size)
        self.window_count = window_count if window_count > 0 else 1
        self.ui.plotPosScroll.setMaximum(self.window_count-1)
        if self.ui.chkAutoScroll.isChecked(): 
            self.ui.plotPosScroll.setValue(self.window_count-1)

        wx_0 = (self.ui.plotPosScroll.value() * self.window_size)
        wx_1 = wx_0 + self.window_size
        print "wsize: %f, wcount: %d, w0: %f, w1: %f" % (self.window_size, self.window_count, wx_0, wx_1)
        ax.set_xlim(wx_0, wx_1)
        ax.set_ylim(0, 110)
        ax.set_xlabel('Tempo (s)')
        ax.set_ylabel(u'Temperatura (º)')
        ax.plot(heater_power, color = 'red')
        ax.plot(pump_power, color = 'blue')
        ax2 = ax.twinx()
        ax2.set_ylim(0,100)
        ax2.set_ylabel(u'Potência (%)')       
        # refresh canvas
        self.canvas.draw()

    def zoom_changed(self, value):
        self.zoom = float(value)
        self.set_window_size()

    
