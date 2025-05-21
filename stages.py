# -*- coding: utf-8 -*-
from model import DictTableModel
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import io
import json
import os

class TableControlStages(object):
    def __init__(self, ui, model):
        self.tbmodel_Stages = model
        model.table = ui.tableView_Stages
        self.tbmodel_Stages.header[u'stage_name'] = u'Estágio'
        self.tbmodel_Stages.header[u'stage_status'] = u'Estado de exec.'

        self.tbmodel_Stages.header[u'stage_time_elapsed'] = u'Tempo decorrido'
        self.tbmodel_Stages.header[u'timer_time_elapsed'] = u'Tempo dec. timer'
        self.tbmodel_Stages.header[u'timer_time_remaining'] = u'Tempo rest. timer'
        self.ui = ui
        self.ui.tableView_Stages.setModel(self.tbmodel_Stages)
        self.ui.tableView_Stages.selectionModel().selectionChanged.connect(self.selectionChanged)
        self.ui.btAdd.clicked.connect(self.bt_add_clicked)
        self.ui.btRemove.clicked.connect(self.bt_remove_clicked)
        self.ui.btSave.clicked.connect(self.bt_save_clicked)
        self.ui.btLoad.clicked.connect(self.bt_load_clicked)
        #self.ui.tabWidget.setTabText(1, u'Selecione uma Etapa...')
        #self.ui.tabWidget.setTabEnabled(1, False)
        self.ui.tableView_Stages.resizeColumnsToContents()
        self.processController = None


    def bt_add_clicked(self):
        data = {u'PID': self.p_control.get_defaults(), u'Pump': self.pump_control.get_defaults(), u'ProcessTimer': {}, u'IngridientsData':[]}
        self.tbmodel_Stages.add(data)
    
    def bt_remove_clicked(self):
        selected = self.ui.tableView_Stages.selectedIndexes()
        if len(selected) == 0:
            return
        first_row = selected[0].row()
        rows = selected[-1].row() - first_row + 1
        self.tbmodel_Stages.removeRows(first_row, rows)
    
    def get_model(self):
        return self.tbmodel_Stages

    def bt_save_clicked(self):
        fname = QFileDialog.getSaveFileName(caption='Salvar arquivo de processo',filter='Arquivo de processo (*.prc)')[0]
        if (fname == u''): return
        fname, ext = os.path.splitext(fname)
        if (ext == ''): ext = '.prc'
        f = io.open(fname + ext, "w", encoding="utf-8")
        f.write(json.dumps(self.tbmodel_Stages.rows, ensure_ascii=False,indent=2))
        f.close()
        
    def bt_load_clicked(self):
        fname = QFileDialog.getOpenFileName(caption='Abrir arquivo de processo',filter='Arquivo de processo (*.prc)')[0]
        if (fname == u''): return
        f = io.open(fname, "r",encoding="utf-8")
        self.tbmodel_Stages.load(json.loads(f.read()))
        f.close()
    
    def set_PIDControl(self, p_control):
        self.p_control = p_control

    def set_PumpControl(self, pump_control):
        self.pump_control = pump_control

    def set_TimerControl(self, timer_control):
        self.timer_control = timer_control

    def set_IngridientsControl(self, ingrid_control):
        self.ingrid_control = ingrid_control

    def set_ProcessController(self, processController):
        self.processController = processController

    def setPagesTitles(self, stage):
        self.ui.toolBox.setItemText(self.ui.toolBox.indexOf(self.ui.pagePower), 'Potência (Etapa {} - {})'.format(stage+1, self.tbmodel_Stages.get_field(stage, 'stage_name')))
        self.ui.toolBox.setItemText(self.ui.toolBox.indexOf(self.ui.pagePump), 'Bomba de recirculação (Etapa {} - {}) '.format(stage+1, self.tbmodel_Stages.get_field(stage, 'stage_name')))
        self.ui.toolBox.setItemText(self.ui.toolBox.indexOf(self.ui.pageTimer), 'Temporizador de Etapa (Etapa {} - {}) '.format(stage+1, self.tbmodel_Stages.get_field(stage, 'stage_name')))


    def selectionChanged(self, selected, deselected):
        selected = selected.indexes()
        selected = selected[0].row() if len(selected) >= 1 else -1
        deselected = deselected.indexes()
        deselected = deselected[0].row() if len(deselected) >= 1 else -1


        if selected != -1:                        

            if self.tbmodel_Stages.row_data(selected).get(u'IngridientsData') is None:
                self.tbmodel_Stages.row_data(selected)[u'IngridientsData'] = []
            self.ingrid_control.model.load(self.tbmodel_Stages.row_data(selected)[u'IngridientsData'])
            self.p_control.set_row(selected)
            self.pump_control.set_row(selected)
            self.timer_control.set_row(selected)
            stage = selected
        else:
            self.p_control.set_row(self.processController.current_stage)
            self.pump_control.set_row(self.processController.current_stage)
            self.timer_control.set_row(self.processController.current_stage)
            stage = self.processController.current_stage
        
        self.setPagesTitles(stage)
