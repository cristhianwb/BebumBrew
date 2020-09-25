# -*- coding: utf-8 -*-
from mainwindow import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from pid import PIDControl, PumpControl, TimerControl
from model import DictTableModel
import json
import io
from simple_pid import PID
from serial_com import *
import time

class TableControlStages(object):
    def __init__(self, ui, model):
        self.tbmodel_Stages = model
        model.table = ui.tableView_Stages
        self.tbmodel_Stages.header[u'stage_name'] = u'Estágio'
        self.tbmodel_Stages.header[u'stage_time_elapsed'] = u'Tempo decorrido'
        self.tbmodel_Stages.header[u'timer_time_remaining'] = u'Tempo restante'
        self.ui = ui
        self.ui.tableView_Stages.setModel(self.tbmodel_Stages)
        self.ui.tableView_Stages.selectionModel().selectionChanged.connect(self.selectionChanged)
        self.ui.btAdd.clicked.connect(self.bt_add_clicked)
        self.ui.btRemove.clicked.connect(self.bt_remove_clicked)
        self.ui.btSave.clicked.connect(self.bt_save_clicked)
        self.ui.btLoad.clicked.connect(self.bt_load_clicked)
        ui.tableView_Stages.resizeColumnsToContents()

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
        fname = unicode(QFileDialog.getSaveFileName(caption='Abrir arquivo de processo',filter='Arquivo de processo (*.prc)'))
        if (fname == u''): return
        f = io.open(fname + u'.prc', "w",encoding="utf-8")
        f.write(json.dumps(self.tbmodel_Stages.rows, ensure_ascii=False,indent=2))
        f.close()
        
    def bt_load_clicked(self):
        fname = unicode(QFileDialog.getOpenFileName(caption='Abrir arquivo de processo',filter='Arquivo de processo (*.prc)'))
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

    def selectionChanged(self, selected, deselected):
        selected = selected.indexes()
        selected = selected[0].row() if len(selected) >= 1 else -1
        deselected = deselected.indexes()
        deselected = deselected[0].row() if len(deselected) >= 1 else -1
        self.p_control.set_row(selected)
        self.pump_control.set_row(selected)
        self.timer_control.set_row(selected)
        
class TableControlIngridients(object):
    def __init__(self, ui):
        self.tbmodel_Ingridients = DictTableModel([u"stage_name"])
        self.tbmodel_Ingridients.header[u"stage_name"] = u'Estágio'
        self.ui = ui
        self.ui.tableView_Ingridients.setModel(self.tbmodel_Ingridients)
        self.ui.btAdd_2.clicked.connect(self.bt_add_clicked)
        self.ui.btRemove_2.clicked.connect(self.bt_remove_clicked)
        
    def bt_add_clicked(self):
        self.tbmodel_Ingridients.add()
        
    def bt_remove_clicked(self):
        selected = self.ui.tableView_Ingridients.selectedIndexes()
        if len(selected) == 0:
            return
        first_row = selected[0].row()
        rows = selected[-1].row() - first_row + 1
        self.tbmodel_Ingridients.removeRows(first_row, rows)


class ProcessController(object):
    def __init__(self, ui, model, sampling_interval=1.0):
        self.ui = ui
        self.ui.btStart.clicked.connect(self.start)
        self.ui.btStop.clicked.connect(self.stop)
        self.timer = QTimer()
        self.current_stage = 0
        self.timer.timeout.connect(self.process)
        self.output = 0
        self.pump_power = 0
        self.temp = 60
        self.model = model
        self.interval = sampling_interval
        self.pid = PID(0.0, 0.0, 0.0, setpoint=0.0, sample_time=sampling_interval, output_limits=(0, 147), auto_mode=False, proportional_on_measurement=False)
        self.ser = SerialInterface()
        self.status = False
        self.process_start_time = None
        self.stage_start_time = None
        self.timer_started = False


    #a funcao process ehh chamada a cada metade da taxa de amostragem
    #pois metade do tempo ehh para envio da potencia dos atuadores
    #e metade do tempo ehh para receber dados do sensor de temperatura
    #a funcao de calculo de pid ehh chamada apenas quando ehh recebida
    #a temperatura, fechando assim o 1 intervalo de amostragem completo
    #exemplo se a taxa de amostragem for de 1 segundo, 1/2 segunda envia
    # 1/2 segundo recebe, calculo do pid a cada 1 segundo
    def process(self):
        #se o proximo estado do serial a ser processado ehh o de envio, setar variaveis de envio
        #if self.ser.state == ST.SEND:
        #    self.ser.heater_power = self.output
        #    self.ser.pump_power = self.pump_power
        #self.ser.process()
        #processar pacote apenas quando recebe-lo
        #if self.ser.state == ST.RECEIVE:
        #    return
        #if self.ser.temp != -127:
        #    self.temp = self.ser.temp
        
        self.temp -= 1

        print 'temp:', self.temp


        next_stage = self.get_next_stage()
        state_changed = (next_stage != self.current_stage)
        
        if (state_changed):
            self.current_stage = next_stage
            self.stage_start_time = QTime().currentTime()

        #print self.temp
        #if pid parameters has changed, they should affect here
        #if (self.get_pid_control_changed() or self.get_pump_control_changed() or state_changed):
        #    self.load_pid_params()
        
        #if self.pid_enabled:
        #    self.output = self.pid(self.temp)
        
        self.update_outputs_to_ui()

    def update_outputs_to_ui(self):
        if self.pid_enabled:
            self.ui.sliderOutPower.setValue(self.output)
        self.ui.labelOutPower.setText("%.0f %%" % (self.output / 147.0 * 100.0,))
        self.ui.labelTemp.setText("%.2f" % (self.temp,) )


    def get_pid_control_changed(self):
        changed = self.model.row_data(self.current_stage)[u'PID'].get(u'changed')
        if changed:
            self.model.row_data(self.current_stage)[u'PID'][u'changed'] = False
            return True
        return False

    def get_pump_control_changed(self):
        changed = self.model.row_data(self.current_stage)[u'Pump'].get(u'changed')
        if changed:
            self.model.row_data(self.current_stage)[u'Pump'][u'changed'] = False
            return True
        return False


    
    def load_pid_params(self):
        p = self.model.row_data(self.current_stage)[u'PID'].get('p_value')
        p = p if p != None else 0.0
        i = self.model.row_data(self.current_stage)[u'PID'].get('i_value')
        i = i if i != None else 0.0
        d = self.model.row_data(self.current_stage)[u'PID'].get('d_value')
        d = d if d != None else 0.0
        output = self.model.row_data(self.current_stage)[u'PID'].get('out_power')
        self.pump_power = self.model.row_data(self.current_stage)[u'Pump'].get('power')
        self.output = output if output != None else 0.0
        setpoint = self.model.row_data(self.current_stage)[u'PID'].get('set_point')
        setpoint = setpoint if setpoint != None else 0.0
        enabled = self.model.row_data(self.current_stage)[u'PID'].get('enabled')
        self.pid_enabled = enabled if enabled != None else False
        self.pid.tunings = (p, i, d)
        self.pid.setpoint = setpoint
        self.pid.auto_mode = self.pid_enabled
        
    def start(self):
        self.ser.connect()
        time.sleep(2)
        self.load_pid_params()
        self.ser.status = ST.SEND
        self.start_time = QTime.currentTime()
        self.stage_start_time = self.start_time
        self.timer.start( (self.interval / 2) * 1000)
        
    
    def stop(self):
        self.timer.stop()

    def get_next_stage(self):
        timer_data = self.model.row_data(self.current_stage).get(u'ProcessTimer')
        if timer_data == None:
            return self.current_stage

        if not self.timer_started:
            startCond = timer_data.get(u'startCond')
            temp = timer_data.get(u'temp')
        
            if startCond == 1:
                self.timer_started = True
            elif (startCond == 2) and (temp != None):
                self.timer_started = (self.temp >= temp)
            elif (startCond == 3) and (temp != None):
                self.timer_started = (self.temp <= temp)
            
            if self.timer_started:
                self.stage_start_time = QTime().currentTime()

        if self.timer_started:
            #convert the time in secconds to QTime
            time = QTime(0,0,0).addSecs(timer_data.get(u'time'))
            time_elapsed = QTime(0,0,0).addSecs(self.stage_start_time.secsTo(QTime.currentTime()))
            self.model.set_field(self.current_stage, u'stage_time_elapsed',time_elapsed.toString())
            if (time_elapsed) >= time:
                next_stage = self.current_stage + 1
                if self.model.count() == next_stage:
                    self.stop()
                    return 0
                print 'in process, next stage', next_stage
                return next_stage

        return self.current_stage



if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    tbmodel_Stages = DictTableModel([u'stage_name',u'stage_time_elapsed',u'timer_time_remaining'])
    pidControl = PIDControl(ui, tbmodel_Stages)
    pumpControl = PumpControl(ui, tbmodel_Stages)
    tableControlStages = TableControlStages(ui, tbmodel_Stages)
    tableControlStages.set_PIDControl(pidControl)
    tableControlStages.set_PumpControl(pumpControl)
    tableControlStages.set_TimerControl(TimerControl(ui, tbmodel_Stages))
    tableControlIngridients = TableControlIngridients(ui)
    processController = ProcessController(ui, tbmodel_Stages)
    MainWindow.show()
    sys.exit(app.exec_())
    
    
