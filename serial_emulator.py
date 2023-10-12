#import serial
#from serial.tools.list_ports import comports
from struct import *
import sys, time

class CRC(object):
    def __init__(self, polynomial=0xD8, crc_len=8):
        self.poly      = polynomial & 0xFF
        self.crc_len   = crc_len
        self.table_len = pow(2, crc_len)
        self.cs_table  = [' ' for x in range(self.table_len)]
        
        self.generate_table()
    
    def generate_table(self):
        for i in range(len(self.cs_table)):
            curr = i
            
            for j in range(8):
                if (curr & 0x80) != 0:
                    curr = ((curr << 1) & 0xFF) ^ self.poly
                else:
                    curr <<= 1
            
            self.cs_table[i] = curr
    
    def print_table(self):
        for i in range(len(self.cs_table)):
            sys.stdout.write(hex(self.cs_table[i]).upper().replace('X', 'x'))
            
            if (i + 1) % 16:
                sys.stdout.write(' ')
            else:
                sys.stdout.write('\n')
    
    def calculate(self, arr, dist=None):
        crc = 0
        
        try:
            if dist:
                indicies = dist
            else:
                indicies = len(arr)
            
            for i in range(indicies):
                try:
                    nex_el = int(arr[i])
                except ValueError:
                    nex_el = ord(arr[i])
                
                crc = self.cs_table[crc ^ nex_el]
                
        except TypeError:
            crc = self.cs_table[arr]
            
        return crc

class ST(object):
    SEND = 0
    RECEIVE = 1

class SerialInterface(object):

    def __init__(self, port='/dev/ttyUSB0', baud=9600, timeout=0.5):
        self.heater_power = 0
        self.pump_power = 0
        self.temp = 0
        self.temp2 = 0
        self.f_switch = False
        self.port = port
        self.baud = baud
        self.conn = None
        self.crc = CRC()
        self.state = ST.SEND
        self.current_error_count = 0
        self.total_error_count = 0
        self.max_error_count = 5 #number of attempts to recover
        self.SYNC_CODE = 0xDDEE
        self.SYNC_CODE_RCV = 0x2211
        self.is_connected = False
        self.connect_attemps = 100
        self.x = 20.0
        self.inc = .4
        self.timer = 0
        self.switch = False

        
        
    def connect(self):
        return True


    def send(self, ht_power, pmp_power):
        return True
    
    def receive(self):
        if (self.timer % 20) == 0:
            self.switch = not self.switch
        v = (0, 0, self.x, self.x + 40, self.switch)
        self.timer += 1
        self.x += self.inc
        if (self.x >= 30.0) and (self.inc > 0): self.inc = -self.inc
        if (self.x <= 20.0) and (self.inc < 0): self.inc = -self.inc
        return v

    
    def disconnect(self):
        self.is_connected = False
        self.current_error_count = 0

    def process(self):
        if (self.state == ST.SEND):
            #print '---------'
            #print self.current_error_count
            #print self.is_connected
            if (self.current_error_count == self.max_error_count) or not self.is_connected:
                
                self.is_connected = self.connect()
                if self.is_connected:
                    print('Connected!')
                self.current_error_count = 0
                return False

            if not self.send(self.heater_power, self.pump_power):
                self.current_error_count += 1
                return False
            self.state = ST.RECEIVE
            return False
        else:
            self.state = ST.SEND
            rcv = self.receive()
            #print '#####', rcv
            if rcv is None:
                self.rcv_status = False
                self.current_error_count += 1
                return False
            else:
                self.rcv_status = True
                a, b , self.temp, self.temp2, self.f_switch = rcv
            
            return True
    
