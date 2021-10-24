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
            'pump_power': [],
            'setpoint': []
        }

        #minimun window size
        self.min_window_size = 10

        self.set_button_color(ui.pushPumpColor, 'blue')
        self.set_button_color(ui.pushHeaterColor, 'red')
        self.set_button_color(ui.pushSensor1Color, 'green')
        self.set_button_color(ui.pushSensor2Color, 'yellow')
        self.set_button_color(ui.pushSetpointColor,'orange')

        self.zoom = 1
        self.window_size = self.min_window_size
        self.window_count = 1
        #ui treatments
        self.ui = ui
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        layout = ui.tabPlotLay
        layout.addWidget(self.canvas)

        ax = self.figure.add_subplot(111)
        self.ax = ax
        ax.set_ylim(0, 110)
        ax.set_xlabel('Tempo (s)')
        ax.set_ylabel(u'Temperatura (º)')
        self.ax.set_xlim(0, self.min_window_size)
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
        ui.pushSensor2Color.clicked.connect(lambda: self.sensor2_line.set_color(self.set_button_color(ui.pushSensor2Color)))
        ui.pushSetpointColor.clicked.connect(lambda: self.sensor2_line.set_color(self.set_button_color(ui.pushSetpointColor)))
        
        ui.chkSensor1Line.clicked.connect(lambda x: self.sensor1_line.set_visible(x))
        ui.chkSensor2Line.clicked.connect(lambda x: self.sensor2_line.set_visible(x))
        ui.chkPumpLine.clicked.connect(lambda x: self.pump_power_line.set_visible(x))
        ui.chkHeaterLine.clicked.connect(lambda x: self.heater_power_line.set_visible(x))
        ui.chkSetpointLine.clicked.connect(lambda x: setpoint_line.set_visible(x))

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

        #sensor 2 line
        color = self.ui.pushSensor2Color.palette().color(QPalette.Background)
        color = rgb_from_qcolor(color)
        self.sensor2_line, = self.ax.plot([], [], color = color)
        self.sensor2_line.set_visible(self.ui.chkSensor2Line.isChecked())

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

        #setpoint line
        color = self.ui.pushSetpointColor.palette().color(QPalette.Background)
        color = rgb_from_qcolor(color)
        self.setpoint_line, = self.ax.plot([], [], color = color)
        self.setpoint_line.set_visible(self.ui.chkSetpointLine.isChecked())


        return self.sensor1_line, self.sensor2_line, self.heater_power_line, self.setpoint_line, self.pump_power_line, 

    def update(self):
        self.sensor1_line.set_data(range(len(self.data['sensor1'])), self.data['sensor1'])
        self.sensor2_line.set_data(range(len(self.data['sensor2'])), self.data['sensor2'])
        self.heater_power_line.set_data(range(len(self.data['heater_power'])), self.data['heater_power'])
        self.pump_power_line.set_data(range(len(self.data['pump_power'])), self.data['pump_power'])
        self.setpoint_line.set_data(range(len(self.data['setpoint'])), self.data['setpoint'])
        return self.sensor1_line, self.sensor2_line, self.heater_power_line,  self.setpoint_line, self.pump_power_line,


    def set_window_size(self):
        sensor1 = self.data['sensor1']
        count = len(sensor1)
        self.window_size = count / self.zoom

        
        
    def set_button_color(self, wich_button, color = None):
        xcolor = QColor(color) if color is not None else QColorDialog.getColor()
        if (not xcolor.isValid()):
            return rgb_from_qcolor(wich_button.palette().button().color())
        wich_button.setStyleSheet("background-color: %s" % (xcolor.name(),))
        return rgb_from_qcolor(QColor(xcolor))


    def plot(self, temp1, temp2, power, p_power, xsetpoint):
        sensor1 = self.data['sensor1']
        sensor2 = self.data['sensor2']
        setpoint = self.data['setpoint']
        heater_power = self.data['heater_power']
        pump_power = self.data['pump_power']
        sensor1.append(temp1)
        sensor2.append(temp2)        
        heater_power.append(power)        
        pump_power.append(int(float(p_power) / 255.0 * 100))
        setpoint.append(xsetpoint)
             
        count = len(sensor1)
        if self.ui.chkAdjToScreen.isChecked():
            self.zoom = 1
            self.set_window_size()

        window_count = int(count / self.window_size) + ( (count % self.window_size) > 0)
        self.ui.plotPosScroll.setMaximum(window_count)
        #print('w_count', window_count)
        if self.ui.chkAutoScroll.isChecked(): 
            self.ui.plotPosScroll.setValue(window_count)

        
        self.ui.zoomSlider.setMaximum(count / self.min_window_size)

        #print('w_size: ', self.window_size, 'pos_scroll', self.ui.plotPosScroll.value())
        wx_1 = self.window_size * self.ui.plotPosScroll.value()
        wx_0 = (wx_1 - self.window_size)
        #print('x0:', wx_0, 'x1:', wx_1)
        self.ax.set_xlim(wx_0, wx_1)

    def zoom_changed(self, value):
        self.zoom = value
        self.set_window_size()

    
