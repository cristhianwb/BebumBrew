#!/usr/bin/python
# -*- coding: utf-8 -*-

from mainwindow import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
#from PyQt4.QtWidgets import QMessageBox
from pid import PIDControl
from timer import TimerControl
from pump import PumpControl
from model import DictTableModel
from simple_pid import PID
#from serial_com import * #for functioning with device use this
from network_com import *
#from serial_emulator import * #and for testing use this
from plot import *
import time
import os
from ingridients import *
from stages import *

#from enum import Enum

class TimerState():
    STOPPED = 0
    RUNNING = 1
    PAUSED  = 2


class ProcessController(object):
    def __init__(self, ui, model, tableControlStages, sampling_interval=1.0):
        self.ui = ui
        self.ui.btStart.clicked.connect(self.start)
        self.ui.btStop.clicked.connect(self.stop)
        self.ui.btPause.clicked.connect(self.pause)
        self.ui.btPrev.clicked.connect(self.goto_prev_stage)
        self.ui.btNext.clicked.connect(self.goto_next_stage)
        self.ui.tabWidget.currentChanged.connect(self.tabChanged)
        self.ui.actionExportar_Dados.triggered.connect(self.action_export_session_data)
        self.timer = QTimer()
        self.timer_state = TimerState.STOPPED        
        self.current_stage = 0
        self.next_stage = None
        self.timer.timeout.connect(self.process)
        self.output = 0
        self.pump_power = 0
        self.f_switch_on = False
        self.setpoint = 0
        self.temp = 0
        self.temp2 = 0
        self.pid_sensor_selected = 0
        self.model = model
        self.interval = sampling_interval
        self.pid = PID(0.0, 0.0, 0.0, setpoint=0.0, sample_time=sampling_interval, output_limits=(0, 100), auto_mode=False, proportional_on_measurement=False)
        self.ser = NetworkCom()
        self.unit_connected = False
        self.status = False
        self.process_start_time = None
        self.stage_start_time = None
        self.timer_start_time = None
        self.timer_started = False
        self.plot_control = PlotControl(ui)
        self.IngridTimer = IngridentsTimer(self)
        self.tableControlStages = tableControlStages


    def process(self):

        reconnected = False

        if self.unit_connected and not self.ser.connected:
            self.unit_connected = False

        if not self.unit_connected and self.ser.connected:
            self.unit_connected = True
            reconnected = True

                
        self.ser.heater_power = self.output
        
        self.pump_power = self.ser.pump_power
        
        
        if ((self.ser.temp != -127) and (self.ser.temp != 0)):
            self.temp = self.ser.temp

        if ((self.ser.temp2 != -127) and (self.ser.temp2 != 0)):
            self.temp2 = self.ser.temp2

        self.f_switch_on = self.ser.f_switch

        

        next_stage = self.get_next_stage()
        state_changed = (next_stage != self.current_stage)
        
        if (state_changed):
            self.set_current_stage_status(u'Concluído')
            self.current_stage = next_stage
            self.set_current_stage_status(u'Em execução')
            self.reset_timers(False)
            self.load_pump_params(False)
            if self.current_stage == -1:
                self.stop()
                return
            self.update_stage_status_to_ui()


        #print self.temp
        #if pid parameters has changed, they should affect here
        if (self.get_pid_control_changed() or state_changed or reconnected):
            self.load_pid_params()

        self.load_pump_params(load_only_changed=not reconnected)
        
        if self.pid_enabled:
            cur_temp = self.temp if (self.pid_sensor_selected == 0) else self.temp2
            print(self.pid_sensor_selected, ' - ', cur_temp)
            self.output = self.pid(cur_temp)
        
        self.update_outputs_to_ui()
        self.plot_control.plot(self.temp, self.temp2, self.output, self.pump_power, self.setpoint)
    
    def reset_timers(self, process_start):
        self.stage_start_time = QTime.currentTime()
        if process_start:
            self.process_start_time = self.stage_start_time 
        self.stage_time_elapsed = QTime(0,0,0)
        self.timer_time_elapsed = QTime(0,0,0)
        self.timer_time_remaining = QTime(0,0,0)
        self.timer_start_time = QTime(0,0,0)
        self.timer_cond_1 = False
        self.timer_cond_2 = False
        self.timer_started = False
        self.pid_reached = False
        self.IngridTimer.reset()

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
            startCond2 = timer_data.get(u'startCond2')
            temp = timer_data.get(u'temp')
            temp2 = timer_data.get(u'temp2')
            sens = timer_data.get(u'sensorSelect') if timer_data.get(u'sensorSelect') != None else 0
            cur_temp = self.temp if (sens == 0) else self.temp2
        
            if not self.timer_cond_1:
                if startCond == 1:
                    self.timer_cond_1 = True
                elif (startCond == 2) and (temp != None):
                    self.timer_cond_1 = (cur_temp > temp)
                elif (startCond == 3) and (temp != None):
                    self.timer_cond_1 = (cur_temp < temp)

            if self.timer_cond_1:
                if startCond2 == 0:
                    self.timer_cond_2 = True
                elif (startCond2 == 1) and (temp2 != None):
                    self.timer_cond_2 = (cur_temp > temp2)
                elif (startCond2 == 2) and (temp2 != None):
                    self.timer_cond_2 = (cur_temp < temp2)
            
            self.timer_started = self.timer_cond_2

            #print ('Cur temp: %.2f, temp1: %.2f, temp2: %.2f' % (cur_temp, temp, temp2) )
            #print('st: %r, cd1: %r, cd2: %r' % (self.timer_started, self.timer_cond_1, self.timer_cond_2))

            if self.timer_started:
                self.timer_start_time = QTime().currentTime()

        if self.timer_started:
            #convert the time in secconds to QTime
            time = QTime(0,0,0).addSecs(timer_data.get(u'time'))
            self.timer_time_elapsed = QTime(0,0,0).addSecs(self.timer_start_time.secsTo(QTime.currentTime()))
            self.timer_time_remaining = QTime(0,0,0).addSecs(self.timer_time_elapsed.secsTo(time))
            self.IngridTimer.process()
            if (self.timer_time_elapsed) >= time:
                next_stage = self.current_stage + 1
                if self.model.count() == next_stage:
                    return -1
                return next_stage

        return self.current_stage


    def clear_stage_status(self):
        for i in range(0, self.model.count()):
            self.model.set_field(i, u'stage_status', u'Aguardando execução...')

    def set_current_stage_status(self, status):
        self.model.set_field(self.current_stage, u'stage_status', status)

    def get_current_stage_status(self):
        return self.model.get_field(self.current_stage, u'stage_status')

    def update_stage_status_to_ui(self):
        self.ui.lbStatus.setText(self.get_current_stage_status())
        self.ui.lbStage.setText(self.model.get_field(self.current_stage, u'stage_name'))
        self.ui.lbNextStage.setText(self.model.get_field(self.current_stage+1, u'stage_name') if (self.current_stage+1 < self.model.count()) and (self.current_stage >= 0) else u'Fim do processo' )
        self.plot_control.add_mark(self.model.get_field(self.current_stage, u'stage_name'))
        self.tableControlStages.setPagesTitles(self.current_stage)


    def update_outputs_to_ui(self):
        if self.pid_enabled:
            self.ui.sliderOutPower.setValue(int(self.output))
        powerStr = u'%.0f %%' % (self.output,)
        self.ui.labelOutPower.setText(powerStr)
        self.ui.lbHeaterPower.setText(powerStr)
        self.ui.lbPumpPower.setText(u'%.0f%%' % (self.pump_power,))
        tempStr = u'%.2f º' % (self.temp,)
        self.ui.labelTemp.setText(tempStr)
        self.ui.lbTemp.setText(tempStr)
        tempStr = u'%.2f º' % (self.temp2,)
        self.ui.labelTemp2.setText(tempStr)
        self.ui.lbTemp2.setText(tempStr)
        setpointStr = u'%.1f º' % (self.setpoint,)
        self.ui.lbSetPoint.setText(setpointStr)
        self.ui.lbStageTimeElapsed.setText(self.stage_time_elapsed.toString())
        self.ui.lbTimerTimeElapsed.setText(self.timer_time_elapsed.toString())
        self.ui.lbTimerTimeRemaining.setText(self.timer_time_remaining.toString())
        self.model.set_field(self.current_stage, u'stage_time_elapsed', str(self.stage_time_elapsed.toString()))
        self.model.set_field(self.current_stage, u'timer_time_elapsed', str(self.timer_time_elapsed.toString()))
        self.model.set_field(self.current_stage, u'timer_time_remaining', str(self.timer_time_remaining.toString()))
        self.ui.lbFloatState.setText('Alto' if self.f_switch_on else 'Normal')
        self.ui.lbFloatState2.setText('Alto' if self.f_switch_on else 'Normal')
        self.ui.lbFloatState.setStyleSheet('color: red;font-weight: bold' if self.f_switch_on else 'color: green;font-weight: bold')
        self.ui.lbFloatState2.setStyleSheet('color: red;font-weight: bold' if self.f_switch_on else 'color: green;font-weight: bold')


    def get_pid_control_changed(self):
        changed = self.model.row_data(self.current_stage)[u'PID'].get(u'changed')
        if changed:
            self.model.row_data(self.current_stage)[u'PID'][u'changed'] = False
            return True
        return False

    
    def load_pid_params(self):
        p = self.model.row_data(self.current_stage)[u'PID'].get('p_value')
        p = p if p != None else 0.0
        i = self.model.row_data(self.current_stage)[u'PID'].get('i_value')
        i = i if i != None else 0.0
        d = self.model.row_data(self.current_stage)[u'PID'].get('d_value')
        d = d if d != None else 0.0

        self.pid_sensor_selected = self.model.row_data(self.current_stage)[u'PID'].get('sen_select')
        self.pid_sensor_selected = self.pid_sensor_selected if self.pid_sensor_selected != None else 0
        
        
        setpoint = self.model.row_data(self.current_stage)[u'PID'].get('set_point')
        setpoint = setpoint if setpoint != None else 0.0
        self.setpoint = setpoint
        enabled = self.model.row_data(self.current_stage)[u'PID'].get('enabled')
        self.pid_enabled = enabled if enabled != None else False
        if not self.pid_enabled:
            output = self.model.row_data(self.current_stage)[u'PID'].get('out_power')
            self.output = output if output != None else 0.0
        self.pid.tunings = (p, i, d)
        self.pid.setpoint = setpoint
        self.pid.auto_mode = self.pid_enabled

    def load_pump_params(self, load_only_changed=True):

        if load_only_changed:
            change_list = self.model.row_data(self.current_stage)[u'Pump'].get(u'changed')
        else:
            change_list = [x for x in self.model.row_data(self.current_stage)[u'Pump'].keys() if x not in ['changed','enabled'] ]
        
        if change_list:
            print(change_list)
            for p in change_list:
                self.ser.pump_parameters[p] = self.model.row_data(self.current_stage)[u'Pump'].get(p)
            change_list.clear()
        
    def start(self):
        if self.timer_state == TimerState.RUNNING:
            return

        if self.timer_state == TimerState.STOPPED:
            self.load_pump_params(False)
            self.load_pid_params()
            self.reset_timers(True)
            self.clear_stage_status()
        self.set_current_stage_status(u'Em execução')
        self.update_stage_status_to_ui()
        self.timer.start( int((self.interval) * 1000))
        self.timer_state = TimerState.RUNNING
        self.plot_control.start()
        self.ser.start()
        
    
    def stop(self):
        if self.timer_state == TimerState.STOPPED: return
        reply = QMessageBox.question(None, 'Parar o processo', 'Tem certeza que deseja parar o processo?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No: return
        self.timer.stop()
        self.plot_control.stop()
        self.ser.stop()
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
        self.ser.stop()


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

    def tabChanged(self, index):
        pass

    def action_export_session_data(self):
        fname = QFileDialog.getSaveFileName(caption='Exportar dados da Sessão',filter='Arquivo json (*.json)')[0]
        if (fname == ''): return
        fname, ext = os.path.splitext(fname)
        if (ext == ''): ext = '.json'
        self.plot_control.export_data(fname + ext)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    tbmodel_Stages = DictTableModel([u'stage_name',u'stage_status',u'stage_time_elapsed',u'timer_time_elapsed',u'timer_time_remaining'], defaults={'stage_name':'Novo Estágio'})
    tbmodel_Ingridients = IngridientsDictTableModel([u"ingridient_name", u"ingridient_time_type_addition", u"ingridient_time_addition"])
    pidControl = PIDControl(ui, tbmodel_Stages)
    pumpControl = PumpControl(ui, tbmodel_Stages)
    tableControlStages = TableControlStages(ui, tbmodel_Stages)
    tableControlStages.set_PIDControl(pidControl)
    tableControlStages.set_PumpControl(pumpControl)
    tableControlStages.set_TimerControl(TimerControl(ui, tbmodel_Stages))
    tableControlIngridients = TableControlIngridients(ui, tbmodel_Ingridients)
    tableControlStages.set_IngridientsControl(tableControlIngridients)
    processController = ProcessController(ui, tbmodel_Stages, tableControlStages)
    tableControlStages.set_ProcessController(processController)
    #MainWindow.setWindowFlags(QtCore.Qt.CustomizeWindowHint)
    #MainWindow.setWindowState(QtCore.Qt.WindowMaximized) 
    MainWindow.show()
        
    res = app.exec_()
    processController.ser.exit()
    if processController.ser.running: 
        processController.ser.thread.join()
    print("exiting")
    sys.exit(res)


    
    
