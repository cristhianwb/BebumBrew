# -*- coding: utf-8 -*-
from PyQt5.QtCore import QTime


class TimerControl(object):
    def __init__(self, ui, model):
        self.ui = ui
        self.model = model
        self.row = -1
        ui.cbTimerStartCond.currentIndexChanged.connect(lambda index, id='': self.indexChanged(index, id))
        ui.cbTimerStartCond2.currentIndexChanged.connect(lambda index, id='2': self.indexChanged(index, id))
        ui.timerTempField.valueChanged.connect(lambda value, id='':self.timerTempChanged(value, id))
        ui.timerTempField2.valueChanged.connect(lambda value, id='2':self.timerTempChanged(value, id))
        ui.timerTimeField.timeChanged.connect(self.timerTimeChanged)
        ui.cbSensorSelect.currentIndexChanged.connect(self.sensorSlectChanged)

    
    def set_row(self, row):
        self.row = row
        if row != -1:
            self.fromDict(self.model.row_data(row).get(u'ProcessTimer'))

    def fromDict(self, data):
        if data == None:
            data = {}
        startCond = data.get(u'startCond')
        startCond2 = data.get(u'startCond')
        self.ui.cbTimerStartCond.setCurrentIndex(startCond if startCond != None else 0)
        self.ui.cbTimerStartCond2.setCurrentIndex(startCond2 if startCond2 != None else 0)
        temp = data.get(u'temp')
        temp2 = data.get(u'temp2')
        self.ui.timerTempField.setValue(temp if temp != None else 0)
        self.ui.timerTempField2.setValue(temp2 if temp2 != None else 0)
        time = data.get(u'time')
        time = time if time != None else 0
        time = QTime(0,0,0).addSecs(time)
        self.ui.timerTimeField.setTime(time)
        sensorSelect = data.get(u'sensorSelect')
        self.ui.cbSensorSelect.setCurrentIndex(sensorSelect if sensorSelect != None else 0)



    def indexChanged(self, index, id):
        self.valueChanged('startCond'+id, index)

    def timerTempChanged(self, value, id):
        self.valueChanged('temp'+id, value)

    def timerTimeChanged(self, value):
        #convert time to seconds to save on the structure
        self.valueChanged('time', QTime(0,0,0).secsTo(value))

    def sensorSlectChanged(self, index):
        self.valueChanged('sensorSelect', index)

    def valueChanged(self, pr_name, pr_value):
        if self.row != -1:
            row_data = self.model.row_data(self.row).get(u'ProcessTimer')
            if row_data == None:
                row_data = {}
                self.model.row_data(self.row)[u'ProcessTimer'] = row_data
            row_data[pr_name] = pr_value
