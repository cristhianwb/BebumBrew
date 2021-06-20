# -*- coding: utf-8 -*-
import numpy as np
from PyQt4.QtGui import *

from matplotlib.backends.qt_compat import QtCore, QtWidgets
from matplotlib.backends.backend_qt4agg import (
        FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

import random

def rgb_from_qcolor(color):
    return color.red() / 255.0, color.green() / 255.0, color.blue() / 255.0

class PlotControl(object):
    def __init__(self, ui):        
        #data that will be plotted
        self.data = {
            'sensor1': [],
            'sensor2': [],
            'heater_power': [],
            'pump_power': []
        }


        self.set_button_color(ui.pushPumpColor, 'blue')
        self.set_button_color(ui.pushHeaterColor, 'red')
        self.set_button_color(ui.pushSensor1Color, 'green')
        self.set_button_color(ui.pushSensor2Color, 'yellow')

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

        ax = self.figure.add_subplot(111)
        self.ax = ax
        ax.set_ylim(0, 110)
        ax.set_xlabel('Tempo (s)')
        ax.set_ylabel(u'Temperatura (º)')
        ax2 = ax.twinx()
        ax2.set_ylim(0,100)
        ax2.set_ylabel(u'Potência (%)')
        
        self.ani = None

        # self.tab_plot_index = ui.tabWidget.indexOf(self.ui.tabPlot)
        # ui.tabWidget.currentChanged.connect(self.tabChanged)

        ui.zoomSlider.valueChanged.connect(self.zoom_changed)
                

        ui.pushPumpColor.clicked.connect(lambda: self.pump_power_line.set_color(self.set_button_color(ui.pushPumpColor)))
        ui.pushHeaterColor.clicked.connect(lambda: self.heater_power_line.set_color(self.set_button_color(ui.pushHeaterColor)))
        ui.pushSensor1Color.clicked.connect(lambda: self.sensor1_line.set_color(self.set_button_color(ui.pushSensor1Color)))
        ui.pushSensor2Color.clicked.connect(lambda: self.set_button_color(ui.pushSensor2Color))
        
        ui.chkSensor1Line.clicked.connect(lambda x: self.sensor1_line.set_visible(x))
        ui.chkPumpLine.clicked.connect(lambda x: self.pump_power_line.set_visible(x))
        ui.chkHeaterLine.clicked.connect(lambda x: self.heater_power_line.set_visible(x))

    def start(self):
        if self.ani is None:
            self.ani = FuncAnimation(self.figure, lambda x: self.update(),
                    init_func=lambda: self.make_lines(), blit=False, interval = 1000)
            self.canvas.draw()
        else:
            self.ani.event_source.start()

    def stop(self):
        self.ani.event_source.stop()

    def tabChanged(self, pageIndex):
        if pageIndex == self.tab_plot_index:
            self.canvas.draw()

    def make_lines(self):
        #sensor 1 line
        color = self.ui.pushSensor1Color.palette().color(QPalette.Background)
        color = rgb_from_qcolor(color)
        self.sensor1_line, = self.ax.plot([], [], color = color)
        self.sensor1_line.set_visible(self.ui.chkSensor1Line.isChecked())

        #heater power line
        color = self.ui.pushHeaterColor.palette().color(QPalette.Background)
        color = rgb_from_qcolor(color)
        self.heater_power_line, = self.ax.plot([], [], color = color)
        self.heater_power_line.set_visible(self.ui.chkHeaterLine.isChecked())

        #pump power line
        color = self.ui.pushPumpColor.palette().color(QPalette.Background)
        color = rgb_from_qcolor(color)
        self.pump_power_line, = self.ax.plot([], [], color = color)
        self.pump_power_line.set_visible(self.ui.chkPumpLine.isChecked())

        return self.sensor1_line, self.heater_power_line, self.pump_power_line      

    def update(self):
        self.sensor1_line.set_data(range(len(self.data['sensor1'])), self.data['sensor1'])
        self.heater_power_line.set_data(range(len(self.data['heater_power'])), self.data['heater_power'])
        self.pump_power_line.set_data(range(len(self.data['pump_power'])), self.data['pump_power'])
        return self.sensor1_line, self.heater_power_line, self.pump_power_line


    def set_window_size(self):
        sensor1 = self.data['sensor1']
        count = float(len(sensor1))
        window_size = int((count / 100.0) * (100.0 - self.zoom))
        self.window_size = window_size if window_size > 0 else 1
        wx_0 = (self.ui.plotPosScroll.value() * self.window_size)
        wx_1 = wx_0 + self.window_size
        #print "wsize: %f, wcount: %d, w0: %f, w1: %f" % (self.window_size, self.window_count, wx_0, wx_1)
        self.ax.set_xlim(wx_0, wx_1)
        
    def set_button_color(self, wich_button, color = None):
        xcolor = QColor(color) if color is not None else QColorDialog.getColor()
        if (not xcolor.isValid()):
            return rgb_from_qcolor(wich_button.palette().button().color())
        wich_button.setStyleSheet("background-color: %s" % (xcolor.name(),))
        return rgb_from_qcolor(QColor(xcolor))


    def plot(self, temp1, power, p_power):
        sensor1 = self.data['sensor1']
        sensor1.append(temp1)
        heater_power = self.data['heater_power']
        heater_power.append(power)
        pump_power = self.data['pump_power']
        pump_power.append(int(float(p_power) / 255.0 * 100))
        
        if self.ui.chkAutoScroll.isChecked() and (self.window_count == 1):
            self.set_window_size()
        
        count = len(sensor1)
        window_count = int(float(count) / self.window_size)
        self.window_count = window_count if window_count > 0 else 1
        self.ui.plotPosScroll.setMaximum(self.window_count-1)
        if self.ui.chkAutoScroll.isChecked(): 
            self.ui.plotPosScroll.setValue(self.window_count-1)
        

    def zoom_changed(self, value):
        self.zoom = float(value)
        self.set_window_size()

    
