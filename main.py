# -*- coding: utf-8 -*-
from mainwindow import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
#from PyQt4.QtWidgets import QMessageBox
from pid import PIDControl, PumpControl, TimerControl
from model import DictTableModel
import json
import io
from simple_pid import PID
#from serial_com import * #for functioning with device use this
from serial_emulator import * #and for testing use this
from plot import *
import time
#from enum import Enum

class TimerState():
    STOPPED = 0
    RUNNING = 1
    PAUSED  = 2

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
        self.ui.tabWidget.setTabText(2, u'Selecione uma Etapa...')
        self.ui.tabWidget.setTabEnabled(2, False)
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
        if selected != -1:    
            self.ui.tabWidget.setTabText(2, u'Etapa %d - ' % (selected+1,) + self.tbmodel_Stages.get_field(selected, u'stage_name'))
            self.ui.tabWidget.setTabEnabled(2, True)
        else:
            self.ui.tabWidget.setTabText(2, u'Selecione uma Etapa...')
            self.ui.tabWidget.setTabEnabled(2, False)
        
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
        self.ui.btPause.clicked.connect(self.pause)
        self.ui.btPrev.clicked.connect(self.goto_prev_stage)
        self.ui.btNext.clicked.connect(self.goto_next_stage)
        self.timer = QTimer()
        self.timer_state = TimerState.STOPPED        
        self.current_stage = 0
        self.next_stage = None
        self.timer.timeout.connect(self.process)
        self.output = 0
        self.pump_power = 0
        self.setpoint = 0
        self.temp = 60
        self.model = model
        self.interval = sampling_interval
        self.pid = PID(0.0, 0.0, 0.0, setpoint=0.0, sample_time=sampling_interval, output_limits=(0, 100), auto_mode=False, proportional_on_measurement=False)
        self.ser = SerialInterface()
        self.status = False
        self.process_start_time = None
        self.stage_start_time = None
        self.timer_start_time = None
        self.timer_started = False
        self.plot_control = PlotControl(ui)


    #a funcao process ehh chamada a cada metade da taxa de amostragem
    #pois metade do tempo ehh para envio da potencia dos atuadores
    #e metade do tempo ehh para receber dados do sensor de temperatura
    #a funcao de calculo de pid ehh chamada apenas quando ehh recebida
    #a temperatura, fechando assim o 1 intervalo de amostragem completo
    #exemplo se a taxa de amostragem for de 1 segundo, 1/2 segunda envia
    # 1/2 segundo recebe, calculo do pid a cada 1 segundo
    def process(self):
        #se o proximo estado do serial a ser processado ehh o de envio, setar variaveis de envio
        if self.ser.state == ST.SEND:
            self.ser.heater_power = self.output
            self.ser.pump_power = self.pump_power
        
        #processar pacote apenas quando recebe-lo
        if not self.ser.process():
            return
        
        if self.ser.temp != -127:
            self.temp = self.ser.temp
        
        print 'temp:', self.temp


        next_stage = self.get_next_stage()
        state_changed = (next_stage != self.current_stage)
        
        if (state_changed):
            self.set_current_stage_status(u'Concluído')
            self.current_stage = next_stage
            self.set_current_stage_status(u'Em execução')
            self.reset_timers(False)
            if self.current_stage == -1:
                self.stop()
                return
            self.update_stage_status_to_ui()


        #print self.temp
        #if pid parameters has changed, they should affect here
        if (self.get_pid_control_changed() or self.get_pump_control_changed() or state_changed):
            self.load_pid_params()
        
        if self.pid_enabled:
            self.output = self.pid(self.temp)
        
        self.update_outputs_to_ui()
        self.plot_control.plot(self.temp, self.output, self.pump_power)
    
    def reset_timers(self, process_start):
        self.stage_start_time = QTime.currentTime()
        if process_start:
            self.process_start_time = self.stage_start_time 
        self.stage_time_elapsed = QTime(0,0,0)
        self.timer_time_elapsed = QTime(0,0,0)
        self.timer_time_remaining = QTime(0,0,0)
        self.timer_start_time = QTime(0,0,0)
        self.timer_started = False

    def get_next_stage(self):
        #This is used when the user forces the change of the stage
        if self.next_stage is not None:
            nxt_stage = self.next_stage
            self.next_stage = None
            return nxt_stage

        timer_data = self.model.row_data(self.current_stage).get(u'ProcessTimer')

        if timer_data == None:
            return self.current_stage

        self.stage_time_elapsed = QTime(0,0,0).addSecs(self.stage_start_time.secsTo(QTime.currentTime()))

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
                self.timer_start_time = QTime().currentTime()

        if self.timer_started:
            #convert the time in secconds to QTime
            time = QTime(0,0,0).addSecs(timer_data.get(u'time'))
            self.timer_time_elapsed = QTime(0,0,0).addSecs(self.timer_start_time.secsTo(QTime.currentTime()))
            self.timer_time_remaining = QTime(0,0,0).addSecs(self.timer_time_elapsed.secsTo(time))
            if (self.timer_time_elapsed) >= time:
                next_stage = self.current_stage + 1
                if self.model.count() == next_stage:
                    return -1
                return next_stage

        return self.current_stage


    def clear_stage_status(self):
        for i in xrange(0, self.model.count()):
            self.model.set_field(i, u'stage_status', u'Aguardando execução...')

    def set_current_stage_status(self, status):
        self.model.set_field(self.current_stage, u'stage_status', status)

    def get_current_stage_status(self):
        return self.model.get_field(self.current_stage, u'stage_status')

    def update_stage_status_to_ui(self):
        self.ui.lbStatus.setText(self.get_current_stage_status())
        self.ui.lbStage.setText(self.model.get_field(self.current_stage, u'stage_name'))
        self.ui.lbNextStage.setText(self.model.get_field(self.current_stage+1, u'stage_name') if (self.current_stage+1 < self.model.count()) and (self.current_stage >= 0) else u'Fim do processo' )

    def update_outputs_to_ui(self):
        if self.pid_enabled:
            self.ui.sliderOutPower.setValue(self.output)
        powerStr = u'%.0f %%' % (self.output,)
        self.ui.labelOutPower.setText(powerStr)
        self.ui.lbHeaterPower.setText(powerStr)
        self.ui.lbPumpPower.setText(u'%.0f%%' % (self.pump_power / 255.0 * 100.0,))
        tempStr = u'%.2f º' % (self.temp,)
        self.ui.labelTemp.setText(tempStr)
        self.ui.lbTemp.setText(tempStr)
        setpointStr = u'%.1f º' % (self.setpoint,)
        self.ui.lbSetPoint.setText(setpointStr)
        self.ui.lbStageTimeElapsed.setText(self.stage_time_elapsed.toString())
        self.ui.lbTimerTimeElapsed.setText(self.timer_time_elapsed.toString())
        self.ui.lbTimerTimeRemaining.setText(self.timer_time_remaining.toString())
        self.model.set_field(self.current_stage, u'stage_time_elapsed',self.stage_time_elapsed.toString())
        self.model.set_field(self.current_stage, u'timer_time_elapsed',self.timer_time_elapsed.toString())
        self.model.set_field(self.current_stage, u'timer_time_remaining',self.timer_time_remaining.toString())


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
        if self.model.row_data(self.current_stage)[u'Pump'].get('enabled'):
            self.pump_power = self.model.row_data(self.current_stage)[u'Pump'].get('power')
        else:
            self.pump_power = 0
        
        if self.pump_power == None:
            self.pump_power = 0
        self.output = output if output != None else 0.0
        setpoint = self.model.row_data(self.current_stage)[u'PID'].get('set_point')
        setpoint = setpoint if setpoint != None else 0.0
        self.setpoint = setpoint
        enabled = self.model.row_data(self.current_stage)[u'PID'].get('enabled')
        self.pid_enabled = enabled if enabled != None else False
        self.pid.tunings = (p, i, d)
        self.pid.setpoint = setpoint
        self.pid.auto_mode = self.pid_enabled
        
    def start(self):
        if self.timer_state == TimerState.RUNNING:
            return

        if self.timer_state == TimerState.STOPPED:
            self.load_pid_params()
            self.ser.status = ST.SEND
            self.reset_timers(True)
            self.clear_stage_status()
        self.set_current_stage_status(u'Em execução')
        self.update_stage_status_to_ui()
        self.timer.start( (self.interval / 2) * 1000)
        self.timer_state = TimerState.RUNNING
        self.plot_control.start()
        
    
    def stop(self):
        if self.timer_state == TimerState.STOPPED: return
        reply = QMessageBox.question(None, 'Parar o processo', 'Tem certeza que deseja parar o processo?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No: return
        self.timer.stop()
        self.plot_control.stop()
        self.ser.disconnect()
        self.set_current_stage_status(u'Processo concluído')
        self.update_stage_status_to_ui()
        self.current_stage = 0
        self.timer_state = TimerState.STOPPED
    
    def pause(self):
        if self.timer_state != TimerState.RUNNING: return
        self.timer_state = TimerState.PAUSED
        self.set_current_stage_status(u'Processo pausado')
        self.update_stage_status_to_ui()
        self.timer.stop()
        self.plot_control.stop()


    def goto_prev_stage(self):
        if self.current_stage == 0: return
        reply = QMessageBox.question(None, u'Pular estágio', u'Tem certeza que deseja pular para o estágio anterior?' + 
                    u' Todas informações do estágio atual serão perdidas', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes: 
            self.next_stage = self.current_stage - 1 

    def goto_next_stage(self):
        if (self.current_stage + 1) == self.model.count(): return
        reply = QMessageBox.question(None, u'Pular estágio', u'Tem certeza que deseja pular para o proximo estágio?' + 
                    u'Todas informações do estágio atual serão perdidas', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes: 
            self.next_stage = self.current_stage + 1    


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    tbmodel_Stages = DictTableModel([u'stage_name',u'stage_status',u'stage_time_elapsed',u'timer_time_elapsed',u'timer_time_remaining'])
    pidControl = PIDControl(ui, tbmodel_Stages)
    pumpControl = PumpControl(ui, tbmodel_Stages)
    tableControlStages = TableControlStages(ui, tbmodel_Stages)
    tableControlStages.set_PIDControl(pidControl)
    tableControlStages.set_PumpControl(pumpControl)
    tableControlStages.set_TimerControl(TimerControl(ui, tbmodel_Stages))
    tableControlIngridients = TableControlIngridients(ui)
    processController = ProcessController(ui, tbmodel_Stages)
    MainWindow.setWindowFlags(QtCore.Qt.CustomizeWindowHint)
    MainWindow.setWindowState(QtCore.Qt.WindowFullScreen) 
    MainWindow.show()
    sys.exit(app.exec_())
    
    
