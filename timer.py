# -*- coding: utf-8 -*-
from PyQt4.QtCore import QTime


class TimerControl(object):
    def __init__(self, ui, model):
        self.ui = ui
        self.model = model
        self.row = -1
        ui.cbTimerStartCond.currentIndexChanged.connect(self.indexChanged)
        ui.timerTempField.valueChanged.connect(self.timerTempChanged)
        ui.timerTimeField.timeChanged.connect(self.timerTimeChanged)
    
    def set_row(self, row):
        self.row = row
        if row != -1:
            self.fromDict(self.model.row_data(row).get(u'ProcessTimer'))

    def fromDict(self, data):
        if data == None:
            data = {}
        startCond = data.get(u'startCond')
        self.ui.cbTimerStartCond.setCurrentIndex(startCond if startCond != None else 0)
        temp = data.get(u'temp')
        self.ui.timerTempField.setValue(temp if temp != None else 0)
        time = data.get(u'time')
        time = time if time != None else 0
        time = QTime(0,0,0).addSecs(time)
        self.ui.timerTimeField.setTime(time)



    def indexChanged(self, index):
        self.valueChanged('startCond', index)

    def timerTempChanged(self, value):
        self.valueChanged('temp', value)

    def timerTimeChanged(self, value):
        #convert time to seconds to save on the structure
        self.valueChanged('time', QTime(0,0,0).secsTo(value))

    def valueChanged(self, pr_name, pr_value):
        if self.row != -1:
            row_data = self.model.row_data(self.row).get(u'ProcessTimer')
            if row_data == None:
                row_data = {}
                self.model.row_data(self.row)[u'ProcessTimer'] = row_data
            row_data[pr_name] = pr_value