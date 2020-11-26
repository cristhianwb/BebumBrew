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
        self.zoom = 0.0
        #ui treatments
        self.ui = ui
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        layout = ui.tabPlotLay
        layout.insertWidget(0, self.canvas)
        ui.zoomSlider.valueChanged.connect(self.zoom_changed)


    def plot(self, temp1, power):
        sensor1 = self.data['sensor1']
        sensor1.append(temp1)
        heater_power = self.data['heater_power']
        heater_power.append(power)
        # instead of ax.hold(False)
        self.figure.clear()
        # create an axis
        ax = self.figure.add_subplot(111)
        # plot data
        ax.plot(sensor1, color = 'green')
        
        count = len(sensor1)
        print 'max:', count
        min = float(count) * (100.0 - self.zoom) * 0.01
        min = int(min)
        min = count - min
        print 'min', min
        print 'count', count - min
        ax.set_xlim(min, count)
        ax.set_ylim(0, 110)
        ax.set_xlabel('Tempo (s)')
        ax.set_ylabel(u'Temperatura (º)')
        ax.plot(heater_power, color = 'red')
        ax2 = ax.twinx()
        ax2.set_ylim(0,100)
        ax2.set_ylabel(u'Potência (%)')       
        # refresh canvas
        self.canvas.draw()

    def zoom_changed(self, value):
        self.zoom = float(value)
        print self.zoom

    def adjust_controls(self):
        pass

    
