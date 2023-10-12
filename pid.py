# -*- coding: utf-8 -*-
from PyQt5.QtCore import QTime


class PIDControl(object):
    def __init__(self, ui, model):
        self.p_value = 0.0
        self.i_value = 0.0
        self.d_value = 0.0
        self.set_point = 0.0
        self.enabled = False
        self.ui = ui
        self.model = model
        self.row = -1
        self.sen_select = 0
        ui.PField.valueChanged.connect(self.set_p)
        ui.IField.valueChanged.connect(self.set_i)
        ui.DField.valueChanged.connect(self.set_d)
        ui.SPField.valueChanged.connect(self.set_set_point)    
        ui.ChkPidEnabled.clicked.connect(self.set_enabled)
        self.ui.sliderOutPower.valueChanged.connect(self.set_out_power)
        ui.cbPidSenSelect.currentIndexChanged.connect(self.set_sen_select)

    def set_out_power(self, val):
        if not self.enabled:
            self.valueChanged('out_power', val)

    def set_p(self, val):
        self.p_value = val
        self.valueChanged('p_value', val)
     
    def set_i(self, val):
        self.i_value = val
        self.valueChanged('i_value', val)

    def set_d(self, val):
        self.d_value = val
        self.valueChanged('d_value', val)

    def set_set_point(self, val):
        self.set_point = val
        self.valueChanged('set_point', val)

    def set_enabled(self, val):
        self.enabled = val
        self.ui.sliderOutPower.setEnabled(not val)
        self.valueChanged('enabled', val)

    def set_sen_select(self, index):
        self.sen_select = index
        self.valueChanged('sen_select', index)

    def update_component_values(self):
        self.ui.PField.setValue(self.p_value)
        self.ui.IField.setValue(self.i_value)
        self.ui.DField.setValue(self.d_value)
        self.ui.SPField.setValue(self.set_point)
        self.ui.ChkPidEnabled.setChecked(self.enabled)
        self.ui.cbPidSenSelect.setCurrentIndex(self.sen_select)

    def fromDict(self, data):
        self.p_value = data.get('p_value') if data != None and data.get('p_value') != None else 0
        self.i_value = data.get('i_value') if data != None and data.get('i_value') != None else 0
        self.d_value = data.get('d_value') if data != None and data.get('d_value') != None else 0
        self.set_point = data.get('set_point') if data != None and data.get('set_point') != None else 0
        self.enabled = data.get('enabled') if data != None and data.get('enabled') != None else False
        self.sen_select = data.get('sen_select') if data != None and data.get('sen_select') != None else 0
        self.update_component_values()

    def valueChanged(self, pr_name, pr_value):
        if self.model != None and self.row != -1:
            self.model.row_data(self.row)[u'PID'][pr_name] = pr_value
            self.model.row_data(self.row)[u'PID'][u'changed'] = True

    def set_row(self, row):
        self.row = row
        if row == -1:
            self.fromDict({})
            return False
        self.fromDict(self.model.row_data(self.row)[u'PID'])
        return True

    def toDict(self):
        data = {}
        data['p_value'] = self.p_value
        data['i_value'] = self.i_value
        data['d_value'] = self.d_value
        data['set_point'] = self.set_point 
        data['enabled'] = self.enabled
        data['sen_select'] = self.sen_select
        return data


