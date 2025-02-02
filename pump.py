# -*- coding: utf-8 -*-
from PyQt5.QtCore import QTime


class PumpControl(object):
    def __init__(self, ui, model):
        self.old_power = 0
        self.ui = ui
        self.model = model
        self.row = -1
        self.fromDict(self.get_defaults())
        ui.sliderPumpPower.valueChanged.connect(self.set_power)
        ui.chkPumpEnabled.clicked.connect(self.set_enabled)
        ui.chkLevelControl.clicked.connect(self.set_level_control)
        ui.sliderPumpPowerHigh.valueChanged.connect(self.set_power_level_reached)
        ui.spinMaxPwrTime.valueChanged.connect(self.set_burst_time)
        ui.chkBurst.clicked.connect(self.set_burst_enabled)
        ui.cbSensorType.currentIndexChanged.connect(self.indexChanged)


    def get_defaults(self):
        return {
            'enabled': False,
            'level_switch_nf': False,
            'power': 0,
            'burst': False,
            'burst_time': 1,
            'level_control': True,
            'power_level_reached': 0
        }

    def indexChanged(self, index):
        self.sensor_nf = True if index == 0 else False
        self.valueChanged('level_switch_nf', self.sensor_nf)      


    def set_burst_time(self, val):
        self.burst_time = val
        self.valueChanged('burst_time', val)
    
    def set_burst_enabled(self, val):
        self.burst_enabled = val
        self.valueChanged('burst', val)

    def set_enabled(self, val):
        self.enabled = val
        if val:
            self.power = self.old_power
        else:
            self.old_power = self.power
            self.power = 0
        self.valueChanged('power', self.power)

        self.update_component_values()

    def set_level_control(self, val):
        self.level_control_enabled = val
        self.valueChanged('level_control', val)

    def set_power(self, val):
        self.power = val
        self.enabled = (self.power > 0)
        if self.power < self.power_level_reached:
            self.power_level_reached = self.power
        self.valueChanged('power', self.power)
        self.update_component_values()
        

    def set_power_level_reached(self, val):
        self.power_level_reached = val
        if self.power < self.power_level_reached:
            self.power_level_reached = self.power
            self.update_component_values()
        self.valueChanged('power_level_reached', self.power_level_reached)

    def valueChanged(self, pr_name, pr_value):
        if self.model != None and self.row != -1:
            self.model.row_data(self.row)[u'Pump'][pr_name] = pr_value

            if self.model.row_data(self.row)[u'Pump'].get(u'changed') is None:
                self.model.row_data(self.row)[u'Pump'][u'changed'] = []
            
            if not pr_name in self.model.row_data(self.row)[u'Pump'][u'changed']:
              self.model.row_data(self.row)[u'Pump'][u'changed'].append(pr_name)

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
        self.level_control_enabled = data.get('level_control') if data != None and data.get('level_control') != None else False
        self.power_level_reached = data.get('power_level_reached') if data != None and data.get('power_level_reached') != None else 0
        self.burst_enabled = data.get('burst_enabled') if data != None and data.get('burst_enabled') != None else False
        self.burst_time = data.get('burst_time') if data != None and data.get('burst_time') != None else False
        self.sensor_nf = data.get('sensor_nf') if data != None and data.get('sensor_nf') != None else False
        

        self.update_component_values()

    def update_component_values(self):
        if self.row >= 0:
            self.ui.chkPumpEnabled.setChecked(self.enabled)
            self.ui.sliderPumpPower.setValue(self.power)
            self.ui.chkLevelControl.setChecked(self.level_control_enabled)
            self.ui.sliderPumpPowerHigh.setValue(self.power_level_reached)
            self.ui.spinMaxPwrTime.setValue(self.burst_time)
            self.ui.chkBurst.setChecked(self.burst_enabled)
            self.ui.cbSensorType.setCurrentIndex(0 if self.sensor_nf else 1)


