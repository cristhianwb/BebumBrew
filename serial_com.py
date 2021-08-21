import serial
from serial.tools.list_ports import comports
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

        
        
    def connect(self):
        
        possible_ports = []
        for port, pname, pidvid  in comports():
            if pidvid != 'n/a':
                print 'Found port %s desc: %s' % (port, pname)
                possible_ports.append((port, pname))
        

        for port, pname in possible_ports:
            try:
                print 'Trying port - ' + port
                self.conn = serial.Serial(port, self.baud, timeout=0.5)
                if self.conn == None:
                    raise()
                print 'Port openned! Sending handshake'
                self.send(self.SYNC_CODE, 0)
                print 'Receiving handshake'
                time.sleep(1)
                rcv = self.receive()
                if rcv == None:
                    raise Exception()
                a, b, c = rcv
                print 'Finnishing handshake'
                if b == self.SYNC_CODE_RCV:
                    self.send(0, self.SYNC_CODE)
                    self.port = port
                    print 'Handshake complete!'
                    return True
                else:
                    raise Exception('The message is different expected 0x%X but is 0x%X)' % (self.SYNC_CODE_RCV,b) )

            except Exception as e:
                print 'Could not connect to port %s, reason: %s - Trying next port' % (port, e)
        print 'Impossible to connect to any port available, trying next time'
        return False


    def send(self, ht_power, pmp_power):
        try:
            #the -10.10 code indicates to the receiver that everything is ok.
            #if the sender is out of sync it will not send -10.10 and then the receveiver
            #discards the packet end start a new synchronization process

            bytes_to_send = pack('iiff7x',ht_power, pmp_power, 0 if self.is_connected else -1)
            bytes_to_send = bytearray(bytes_to_send)
            check_sum = self.crc.calculate(bytes_to_send)
            bytes_to_send.append(check_sum)
            self.conn.write(bytes_to_send)
            return True
        except Exception as e:
            print ('Problema ao enviar pacote: ', e)
            #self.conn.reset_output_buffer()
            return False
    
    def receive(self):
        try:
            rcv = self.conn.read(16)
            if len(rcv) != 16:
                raise Exception('Eperando receber 16 bytes porem foram recebidos %d' % (len(rcv),))
            a, b, temp, temp2, check_sum =  unpack('iiff3xB', rcv)
            if ( self.crc.calculate(bytearray(rcv[0:-1])) == check_sum ):
                return (a, b, temp, temp2)
            else:
                raise Exception('Erro no CRC, esperado %h encontrado %h' % (self.crc.calculate(bytearray(rcv[0:-1])) , check_sum) )
        except Exception as e:
            print ('Problema ao receber pacote: ', e)
            #self.conn.reset_input_buffer()
            return None
    
    def disconnect(self):
        self.is_connected = False
        self.current_error_count = 0
        self.send(0,0)

    def process(self):
        if (self.state == ST.SEND):
            print '---------'
            print self.current_error_count
            print self.is_connected
            if (self.current_error_count == self.max_error_count) or not self.is_connected:
                
                self.is_connected = self.connect()
                if self.is_connected:
                    print 'Connected!'
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
            if rcv is None:
                self.rcv_status = False
                self.current_error_count += 1
                return False
            else:
                self.rcv_status = True
                a, b , self.temp, self.temp2 = rcv
            
            return True
    
