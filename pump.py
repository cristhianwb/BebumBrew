# -*- coding: utf-8 -*-
from PyQt5.QtCore import QTime


class PumpControl(object):
    def __init__(self, ui, model):
        self.enabled = False
        self.power = 0
        self.power_high = 0
        self.level_control_enabled = False
        self.ui = ui
        self.model = model
        self.row = -1
        self.burst_enabled = False
        self.burst_time = 1
        self.sensor_nf = False
        ui.sliderPumpPower.valueChanged.connect(self.set_power)
        ui.chkPumpEnabled.clicked.connect(self.set_enabled)
        ui.chkLevelControl.clicked.connect(self.set_level_control)
        ui.sliderPumpPowerHigh.valueChanged.connect(self.set_power_high)
        ui.spinMaxPwrTime.valueChanged.connect(self.set_burst_time)
        ui.chkBurst.clicked.connect(self.set_burst_enabled)
        ui.cbSensorType.currentIndexChanged.connect(self.indexChanged)


    def indexChanged(self, index):
        self.sensor_nf = True if index == 1 else False
        self.valueChanged('sensor_nf', self.sensor_nf)      


    def set_burst_time(self, val):
        self.burst_time = val
        self.valueChanged('burst_time', val)
    
    def set_burst_enabled(self, val):
        self.burst_enabled = val
        self.valueChanged('burst_enabled', val)

    def set_enabled(self, val):
        self.enabled = val
        self.valueChanged('enabled', val)

    def set_level_control(self, val):
        self.level_control_enabled = val
        self.valueChanged('level_control_enabled', val)

    def set_power(self, val):
        self.power = val
        self.valueChanged('power', self.power)

    def set_power_high(self, val):
        self.power_high = val
        self.valueChanged('power_high', self.power_high)

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
        self.power = data.get('power') if data != None and data.get('power') != None else 0
        self.level_control_enabled = data.get('level_control_enabled') if data != None and data.get('level_control_enabled') != None else False
        self.power_high = data.get('power_high') if data != None and data.get('power_high') != None else 0
        self.burst_enabled = data.get('burst_enabled') if data != None and data.get('burst_enabled') != None else False
        self.burst_time = data.get('burst_time') if data != None and data.get('burst_time') != None else False
        self.sensor_nf = data.get('sensor_nf') if data != None and data.get('sensor_nf') != None else False
        

        self.update_component_values()

    def update_component_values(self):
        self.ui.chkPumpEnabled.setChecked(self.enabled)
        self.ui.sliderPumpPower.setValue(self.power)
        self.ui.chkLevelControl.setChecked(self.level_control_enabled)
        self.ui.sliderPumpPowerHigh.setValue(self.power_high)
        self.ui.spinMaxPwrTime.setValue(self.burst_time)
        self.ui.chkBurst.setChecked(self.burst_enabled)
        self.ui.cbSensorType.setCurrentIndex(1 if self.sensor_nf else 0)


