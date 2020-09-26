import serial
from struct import *
import sys

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
        self.port = port
        self.baud = baud
        self.conn = None
        self.crc = CRC()
        self.state = ST.SEND
        
    
    def get_avail_ports(self):
        pass
    
    def connect(self):
        try:
            self.conn = serial.Serial(self.port, self.baud, timeout=0.5)
            return True
        except:
            return False
            
    def send(self):
        bytes_to_send = pack('iif3x', self.heater_power, self.pump_power, 0.0)
        bytes_to_send = bytearray(bytes_to_send)
        check_sum = self.crc.calculate(bytes_to_send)
        bytes_to_send.append(check_sum)
        self.conn.write(bytes_to_send)
    
    def receive(self):
        try:
            rcv = self.conn.read(16)
            a, b, self.temp, check_sum =  unpack('iif3xB', rcv)
            if ( self.crc.calculate(bytearray(rcv[0:-1])) == check_sum ):
                return True
            else:
                raise Exception('Erro no CRC, esperado %h encontrado %h' % (self.crc.calculate(bytearray(rcv[0:-1])) , check_sum) )
        except Exception as e:
            print ('Problema ao receber pacote: ', e)
            return False
    
    def process(self):
        if (self.state == ST.SEND):
            self.send()
            self.state = ST.RECEIVE
        else:
            self.rcv_status = self.receive()
            self.state = ST.SEND
    
