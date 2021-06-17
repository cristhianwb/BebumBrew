from PyQt5.QtCore import *


class DictTableModel(QAbstractTableModel):
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
        
    
    def newRow(self):
        row = {}
        for l in self.fields:
            row[l] = u''
        return {u'columns':row, u'data': {u'PID': {}, u'Pump': {}, u'ProcessTimer': {}} }
    
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

        value = self.rows[index.row()][u'columns'].get(self.fields[index.column()])

        if value is None:
            value = u''
            self.rows[index.row()][u'columns'][self.fields[index.column()]] = value
            
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
    
    #the data field is not showed in the grid
    def row_data(self, row):
        return self.rows[row][u'data']

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

    def count(self):
        return len(self.rows)


