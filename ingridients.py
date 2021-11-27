# -*- coding: utf-8 -*-
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from playsound import playsound

class IngridentsTimer(object):
    def __init__(self, procController):
        self.processController = procController
        self.ingridients_added = {}
        

    def reset(self):
        self.ingridients_added = {}

    def process(self):
        ingridData = self.processController.model.row_data(self.processController.current_stage).get(u'IngridientsData')
        if ingridData is None or not self.processController.timer_started:
            return
        print ingridData
        for row in ingridData:
            if self.ingridients_added.get(row[u'columns'].get(u'ingridient_name')):
                continue

            addTime = QTime.fromString(row[u'columns'][u'ingridient_time_addition'], u'hh:mm:ss')

            if (row[u'columns'][u'ingridient_time_type_addition'] == u'Após'):
                if (self.processController.timer_time_elapsed >= addTime):
                    ingrid = row[u'columns'].get(u'ingridient_name')
                    self.ingridients_added[ingrid] = True
                    playsound('notification.wav', False)
                    QMessageBox.information(None, 'Adicionar insumo', 'Hora de adicionar o ' + ingrid)
                    #self.sound.stop()
            else:
                if (self.processController.timer_time_remaining <= addTime):
                    ingrid = row[u'columns'].get(u'ingridient_name')
                    self.ingridients_added[ingrid] = True
                    playsound('notification.wav', False)
                    QMessageBox.information(None, 'Adicionar insumo', 'Hora de adicionar o ' + ingrid)
                    #self.sound.stop()




class IngridientsDictTableModel(QAbstractTableModel):
    def __init__(self, fields, parent=None, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        self.fields = fields
        self.header = dict(zip(fields,fields))
        row = self.newRow()
        self.rows = [row]

    def rowCount(self, parent):
        return len(self.rows)
    
    def setFieldDesc(self):
        pass
        
    def setIngridientsData(self, data):
        self.rows = data
        if len(data) == 0:
            self.rows.append(self.newRow)

    def newRow(self):
        row = {}
        for l in self.fields:
            row[l] = u''
        return {u'columns': row}
    
    def columnCount(self, parent):
        return len(self.fields)
        
    def setData(self, index, value, role):
        if role == Qt.EditRole:
            self.rows[index.row()][u'columns'][self.fields[index.column()]] = unicode(value.toString().toUtf8(), encoding="UTF-8")
            self.dataChanged.emit(index, index)
            self.table.resizeColumnsToContents()
            return True
        return False
            
    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        elif role != Qt.DisplayRole and role != Qt.EditRole:
            return QVariant()

        if (not self.rows[index.row()][u'columns']):
          self.rows[index.row()][u'columns'] = self.newRow()

        value = self.rows[index.row()][u'columns'].get(self.fields[index.column()])            
        return QVariant(value)

    
    def flags(self, index):
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
    
    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return QVariant()
        if orientation==Qt.Horizontal:        
            return QVariant(self.header[self.fields[section]])
        if orientation==Qt.Vertical:
            return QVariant(section+1)
    
    def removeRows(self, row, count=1):
        self.beginRemoveRows(QModelIndex(), row, row+count-1)
        del(self.rows[row:row+count])
        self.endRemoveRows()
    
    def insertRows(self, row, count=1):
        self.beginInsertRows(QModelIndex(), row, row+count-1)
        for r in range(row, row+count):
            self.rows.insert(r,self.newRow())
        self.endInsertRows()
    
    def add(self):
        self.beginInsertRows(QModelIndex(), len(self.rows), len(self.rows))
        self.rows.append(self.newRow())
        self.endInsertRows()
    
    def set_field(self, row, fname, val):
        col = self.fields.index(fname)
        self.rows[row][u'columns'][fname] = val
        self.dataChanged.emit(self.index(row,col), self.index(row,col))      
    
    def get_field(self, row, fname):
        col = col = self.fields.index(fname)
        return self.rows[row][u'columns'].get(fname)

    def set_field_by_column(self, row, col, val):
        self.rows[row][u'columns'][self.fields[col]] = val
        self.dataChanged.emit(self.index(row,col), self.index(row,col))      


    def load(self, data):
        self.beginResetModel()
        self.rows = data
        self.endResetModel()
        self.table.resizeColumnsToContents()

    def count(self):
        return len(self.rows)


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

    def setEditorData(self, editor, index):
        editor.blockSignals(True)
        editor.setTime(QTime.fromString(index.model().data(index, Qt.DisplayRole).toString(), u'hh:mm:ss'))
        editor.blockSignals(False)
    
    def setModelData(self, editor, model, index):
      model.setData(index, editor.time(), Qt.EditRole)


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

    def set_row_data(self, row, data):
        self.model.load(data)


