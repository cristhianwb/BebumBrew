# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

#from matplotlib.backends.qt_compat import QtCore, QtWidgets
#from matplotlib.backends.backend_qt5agg import (
#        FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
#import matplotlib.pyplot as plt
#from matplotlib.animation import FuncAnimation
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg

import random
import io
import json


def rgb_from_qcolor(color):
    return color.red(), color.green(), color.blue()

class PlotControl(object):
    def __init__(self, ui):        
        #data that will be plotted
        self.data = {
            'sensor1': [],
            'sensor2': [],
            'heater_power': [],
            'pump_power': [],
            'setpoint': [],
            'marks': [],
            'sample_count': 0
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
        self.graphWidget = pg.PlotWidget()
        layout = ui.tabPlotLay
        layout.addWidget(self.graphWidget)

        self.graphWidget.setBackground('w')

        
        self.graphWidget.setTitle("Mosturação", color="b", size="30pt")
        # Add Axis Labels
        styles = {"color": "#f00", "font-size": "20px"}
        self.graphWidget.setLabel("left", "Temperature (°C)", **styles)
        self.graphWidget.setLabel("bottom", "Hour (H)", **styles)
        #Add legend
        self.graphWidget.addLegend()
        #Add grid
        self.graphWidget.showGrid(x=True, y=True)
        #Set Range
        #self.graphWidget.setXRange(0, 10, padding=0)
        #self.graphWidget.setYRange(20, 55, padding=0)

        #pen = pg.mkPen(color=(255, 0, 0))
        #self.data_line =  self.graphWidget.plot(self.x, self.y, pen=pen)
        self.make_lines()

               

        # self.tab_plot_index = ui.tabWidget.indexOf(self.ui.tabPlot)
        # ui.tabWidget.currentChanged.connect(self.tabChanged)

        ui.zoomSlider.valueChanged.connect(self.zoom_changed)
                

        ui.pushPumpColor.clicked.connect(lambda: self.pump_power_line.set_color(self.set_button_color(ui.pushPumpColor)))
        ui.pushHeaterColor.clicked.connect(lambda: self.heater_power_line.set_color(self.set_button_color(ui.pushHeaterColor)))
        ui.pushSensor1Color.clicked.connect(lambda: self.sensor1_line.set_color(self.set_button_color(ui.pushSensor1Color)))
        ui.pushSensor2Color.clicked.connect(lambda: self.sensor2_line.set_color(self.set_button_color(ui.pushSensor2Color)))
        ui.pushSetpointColor.clicked.connect(lambda: self.sensor2_line.set_color(self.set_button_color(ui.pushSetpointColor)))
        
        ui.chkSensor1Line.clicked.connect(lambda x: self.sensor1_line.setVisible(x))
        ui.chkSensor2Line.clicked.connect(lambda x: self.sensor2_line.setVisible(x))
        ui.chkPumpLine.clicked.connect(lambda x: self.pump_power_line.setVisible(x))
        ui.chkHeaterLine.clicked.connect(lambda x: self.heater_power_line.setVisible(x))
        ui.chkSetpointLine.clicked.connect(lambda x: self.setpoint_line.setVisible(x))

    def start(self):
        pass

    def stop(self):
        pass

    def tabChanged(self, pageIndex):
        if pageIndex == self.tab_plot_index:
            self.canvas.draw()

    def make_lines(self):
        #sensor 1 line
        width = 2
        color = self.ui.pushSensor1Color.palette().color(QPalette.Background)
        color = rgb_from_qcolor(color)
        print(color)
        self.sensor1_line = self.graphWidget.plot([], [], pen=pg.mkPen(color=color, width=width))
        self.sensor1_line.setVisible(self.ui.chkSensor1Line.isChecked())

        #sensor 2 line
        color = self.ui.pushSensor2Color.palette().color(QPalette.Background)
        color = rgb_from_qcolor(color)
        self.sensor2_line = self.graphWidget.plot([], [], pen=pg.mkPen(color=color, width=width))
        self.sensor2_line.setVisible(self.ui.chkSensor2Line.isChecked())

        #heater power line
        color = self.ui.pushHeaterColor.palette().color(QPalette.Background)
        color = rgb_from_qcolor(color)
        self.heater_power_line = self.graphWidget.plot([], [], pen=pg.mkPen(color=color, width=width))
        self.heater_power_line.setVisible(self.ui.chkHeaterLine.isChecked())

        #pump power line
        color = self.ui.pushPumpColor.palette().color(QPalette.Background)
        color = rgb_from_qcolor(color)
        self.pump_power_line = self.graphWidget.plot([], [], pen=pg.mkPen(color=color, width=width))
        self.pump_power_line.setVisible(self.ui.chkPumpLine.isChecked())

        #setpoint line
        color = self.ui.pushSetpointColor.palette().color(QPalette.Background)
        color = rgb_from_qcolor(color)
        self.setpoint_line = self.graphWidget.plot([], [], pen=pg.mkPen(color=color, width=width))
        self.setpoint_line.setVisible(self.ui.chkSetpointLine.isChecked())


        return self.sensor1_line, self.sensor2_line, self.heater_power_line, self.setpoint_line, self.pump_power_line, 

    def update(self):
        self.sensor1_line.setData(list(range(len(self.data['sensor1']))), self.data['sensor1'])
        self.sensor2_line.setData(list(range(len(self.data['sensor2']))), self.data['sensor2'])
        self.heater_power_line.setData(list(range(len(self.data['heater_power']))), self.data['heater_power'])
        self.pump_power_line.setData(list(range(len(self.data['pump_power']))), self.data['pump_power'])
        self.setpoint_line.setData(list(range(len(self.data['setpoint']))), self.data['setpoint'])

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
        sample_count = self.data['sample_count']
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
        sample_count += 1
        self.data['sample_count'] = sample_count
             
        count = sample_count
        if self.ui.chkAdjToScreen.isChecked():
            self.zoom = 1
            self.set_window_size()

        window_count = int(int(count / self.window_size) + ( (count % self.window_size) > 0))
        self.ui.plotPosScroll.setMaximum(window_count)
        #print('w_count', window_count)
        if self.ui.chkAutoScroll.isChecked(): 
            self.ui.plotPosScroll.setValue(window_count)

        
        self.ui.zoomSlider.setMaximum(int(count / self.min_window_size))

        #print('w_size: ', self.window_size, 'pos_scroll', self.ui.plotPosScroll.value())
        wx_1 = self.window_size * self.ui.plotPosScroll.value()
        wx_0 = (wx_1 - self.window_size)
        #print('x0:', wx_0, 'x1:', wx_1)
        self.graphWidget.setXRange(wx_0, wx_1, padding=0)
        self.update()
        #self.ax.set_xlim(wx_0, wx_1)
        

    def add_mark(self, text):
        pass
        # mark_position = self.data['sample_count']# - 1 if (self.data['sample_count'] > 0) else 0
        # mark = (mark_position, text)
        # self.data['marks'].append(mark)
        # self.ax.axvline(mark_position, color ="black", alpha = 0.8, lw = 1.5)
        # plt.text(mark_position, 30, text, rotation=90)
        # print(self.data['marks'])



    def zoom_changed(self, value):
        if value == 0:
            self.zoom = 1
        else:
            self.zoom = value
        self.set_window_size()

    def export_data(self, file_name):
        f = io.open(file_name, "w", encoding="utf-8")
        f.write(json.dumps(self.data, ensure_ascii=False, indent=2))
        f.close()


    
