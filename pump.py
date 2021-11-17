# -*- coding: utf-8 -*-
from PyQt4.QtCore import QTime


class PumpControl(object):
    def __init__(self, ui, model):
        self.enabled = False
        self.power = 0.0
        self.ui = ui
        self.model = model
        self.row = -1
        ui.sliderPumpPower.valueChanged.connect(self.set_power)
        ui.chkPumpEnabled.clicked.connect(self.set_enabled)

    def set_enabled(self, val):
        self.enabled = val
        self.valueChanged('enabled', self.enabled)

    def set_power(self, val):
        self.power = val
        self.valueChanged('power', self.power)

    def valueChanged(self, pr_name, pr_value):
        if self.model != None and self.row != -1:
            self.model.row_data(self.row)[u'Pump'][pr_name] = pr_value
            self.model.row_data(self.row)[u'Pump'][u'changed'] = True

    def set_row(self, row):
        self.row = row
        if row == -1:
            self.fromDict({})
            return False
        self.fromDict(self.model.row_data(self.row)[u'Pump'])
        return True
    
    def fromDict(self, data):
        self.enabled = data.get('enabled') if data != None and data.get('enabled') != None else False
        self.power = data.get('power') if data != None and data.get('power') != None else 0.0
        self.update_component_values()

    def update_component_values(self):
        self.ui.chkPumpEnabled.setChecked(self.enabled)
        self.ui.sliderPumpPower.setValue(self.power)