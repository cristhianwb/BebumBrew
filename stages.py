# -*- coding: utf-8 -*-
from model import DictTableModel
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import io
import json

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
        self.ui.tabWidget.setTabText(1, u'Selecione uma Etapa...')
        self.ui.tabWidget.setTabEnabled(1, False)
        self.ui.tableView_Stages.resizeColumnsToContents()

    def bt_add_clicked(self):
        self.tbmodel_Stages.add()
    
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
        fname = unicode(QFileDialog.getSaveFileName(caption='Salvar arquivo de processo',filter='Arquivo de processo (*.prc)'))
        if (fname == u''): return
        fname, ext = os.path.splitext(fname)
        if (ext == ''): ext = 'prc'
        f = io.open(fname + '.' + '.prc', "w", encoding="utf-8")
        f.write(json.dumps(self.tbmodel_Stages.rows, ensure_ascii=False,indent=2))
        f.close()
        
    def bt_load_clicked(self):
        fname = unicode(QFileDialog.getOpenFileName(caption='Abrir arquivo de processo',filter='Arquivo de processo (*.prc)'))
        if (fname == u''): return
        f = io.open(fname, "r",encoding="utf-8")
        self.tbmodel_Stages.load(json.loads(f.read()))
        f.close()
        self.ui.tableView_Stages.resizeColumnsToContents();
    
    def set_PIDControl(self, p_control):
        self.p_control = p_control

    def set_PumpControl(self, pump_control):
        self.pump_control = pump_control

    def set_TimerControl(self, timer_control):
        self.timer_control = timer_control

    def selectionChanged(self, selected, deselected):
        selected = selected.indexes()
        selected = selected[0].row() if len(selected) >= 1 else -1
        deselected = deselected.indexes()
        deselected = deselected[0].row() if len(deselected) >= 1 else -1
        self.p_control.set_row(selected)
        self.pump_control.set_row(selected)
        self.timer_control.set_row(selected)
        if selected != -1:    
            self.ui.tabWidget.setTabText(1, u'Etapa %d - ' % (selected+1,) + self.tbmodel_Stages.get_field(selected, u'stage_name'))
            self.ui.tabWidget.setTabEnabled(1, True)
        else:
            self.ui.tabWidget.setTabText(1, u'Selecione uma Etapa...')
            self.ui.tabWidget.setTabEnabled(1, False)
