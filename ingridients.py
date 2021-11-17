# -*- coding: utf-8 -*-
from model import DictTableModel
from PyQt4.QtGui import *


class IngridientAddTypeDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.addItems([u'Após',u'Faltando'])
        return combo

class TimeEditDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        timeedt = QTimeEdit(parent)
        timeedt.setDisplayFormat(u'hh:mm:ss')
        return timeedt

    # def setEditorData(self, editor, index):
    #     editor.blockSignals(True)
    #     try: idxConversion = self.averageChoices.index(index.model().data(index,Qt.DisplayRole))
    #     except ValueError: idxConversion = 0
    #     editor.setCurrentIndex(int(idxConversion))
    #     editor.blockSignals(False)
    #     self.setModelData(self,editor,???,index) #<<============================?
    # def setModelData(self, editor, model, index):
    #     model.setData(index, self.averageChoices[editor.currentIndex()],Qt.EditRole)

class TableControlIngridients(object):
    def __init__(self, ui, model):
        self.model = model
        self.model.table = ui.tableView_Ingridients
        self.model.header[u"ingridient_name"] = u'Insumo'
        self.model.header[u"ingridient_time_type_addition"] = u'Adicionar'
        self.model.header[u"ingridient_time_addition"] = u'Tempo da adição'  
        self.ui = ui
        self.IngridientAddTypeDel = IngridientAddTypeDelegate()
        self.TimeEditDel = TimeEditDelegate()
        self.ui.tableView_Ingridients.setModel(self.model)
        self.ui.tableView_Ingridients.setItemDelegateForColumn(1,self.IngridientAddTypeDel)
        self.ui.tableView_Ingridients.setItemDelegateForColumn(2,self.TimeEditDel)

        self.ui.btAdd_2.clicked.connect(self.bt_add_clicked)
        self.ui.btRemove_2.clicked.connect(self.bt_remove_clicked)
        self.ui.tableView_Ingridients.resizeColumnsToContents()
        
    def bt_add_clicked(self):
        self.model.add()
        
    def bt_remove_clicked(self):
        selected = self.ui.tableView_Ingridients.selectedIndexes()
        if len(selected) == 0:
            return
        first_row = selected[0].row()
        rows = selected[-1].row() - first_row + 1
        self.model.removeRows(first_row, rows)

