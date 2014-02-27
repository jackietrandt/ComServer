'''
Created on 14/10/2013

@author: user
'''
import os
import time
from threading import Thread
import rpyc
from rpyc.utils.server import ThreadedServer
#---------------------------------------------------------------------------# 
# modbus serial com 
#---------------------------------------------------------------------------# 
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
#for scanning com port
import serial


# Class - Modbus class and object
#_____________________________________________________________________________
class Com_Modbus:
    def __init__(self):
        #logging.basicConfig()
        #log = logging.getLogger()
        #log.setLevel(logging.DEBUG)

        #scan all available com port
        port_list = self.scan()
        s = None
        print "Found ports:"
        for n,s in port_list: print "____(%d) %s" % (n,s)
        if s <> None:
            self.client = ModbusClient(method='ascii', port=s, stopbits = 1, parity = 'E', bytesize = 7, baudrate='9600', timeout=1)
            connect = self.client.connect()
            print "Com is connected =",connect
            print "Init Modbus Comm = ",self.client    
            
            
    #Scan all available com port on this machine - return list of connected usb com port
    def scan(self):
        # scan for available ports. return a list of tuples (num, name)
        available = []
        for i in range(256):
            try:
                s = serial.Serial(i)
                available.append( (i, s.portstr))
                s.close()
            except serial.SerialException:
                pass

        return available

    def D_AddressRef(self,d_Address):
    #---------------------------------------------------------------------------# 
    # D_AddressRef
    #---------------------------------------------------------------------------# 
    #Input address in decimal - then function would convert it to PLC address
    #Address 0x1000 stand for D register in PLC
    #Address 0x0258 stand for 600 in decimal
    #So to write to D600 register in the PLC
    #The reference address is 0x1258
        d_Working = 4096
        d_Working = d_Working + d_Address
        return d_Working
    #_____________________________________________________________________________#
    # Usage example
    #_____________________________________________________________________________#
    #client.write_register(D_AddressRef(600), 123, unit=2 ) #unit=2 : mean PLC server address = 2
    #    def write_register(self, address, value, **kwargs): // Extracted from pymodbus\client\common.py
    #        '''
    #        :param address: The starting address to write to
    #        :param value: The value to write to the specified address
    #        :param unit: The slave unit this request is targeting
    #        :returns: A deferred response handle
    
    def Send_register(self,address,data):
        
        self.client.write_register(self.D_AddressRef(address), data, unit = 1 )
        print 'sent'
        pass
    #read back single register
    def Read_register(self,address):
        #read_coils(address, count=1, unit=0)
        register_read = self.client.read_holding_registers(self.D_AddressRef(address),1, unit = 1)
        
        if register_read <> None:
            return register_read.registers[0]
        else:
            return None
        pass
    #read back multiple register
    def Read_register_multi(self,address,length):
        #read_coils(address, count=1, unit=0)
        register_read = self.client.read_holding_registers(self.D_AddressRef(address),length, unit = 1)
        print register_read.registers[0]
        
        return register_read
        pass

class ComServerService(rpyc.Service):
    ModbusClient = Com_Modbus()
    _sharevalue = 10
    class exposed_ComServer(object):   # exposing names is not limited to methods :)
        def __init__(self, interval = 1):
            self.interval = interval
            self.alive = 1
            self.active = True
            self.thread = Thread(target = self.work)
            self.thread.start()
            self.share_stuff = 0
            self.share_read_data = 0
            
        def exposed_get_answer(self,x): # this is an exposed method - when client first connect verify connection on client side
            return x + 10
        def exposed_test(self):
            ComServerService._sharevalue = ComServerService._sharevalue + 3
            self.share_stuff = ComServerService._sharevalue
            return self.share_stuff
        #___Wrapper function for modbus client ________________________
        #
        #
        def exposed_Send_register(self,address,data):
            print 'CMD = Client Send ',address
            ComServerService.ModbusClient.Send_register(address, data)
        def exposed_Read_register(self,address):
            print 'CMD = Client Read ',address
            self.share_read_data = ComServerService.ModbusClient.Read_register(address)
            return self.share_read_data
        #______________________________________________________________        
        def exposed_stop(self):   # this method has to be exposed too
            self.active = False
            self.thread.join()
            print 'ComServer Thread Stopped'
        
        def work(self):
            print 'ComServer Thread Started'
            while self.active:
                #this might cause crash
                #self.alive = self.alive + 1

                #if (self.alive % 10) == 0:
                #    ComServerService.ModbusClient.Send_register(616, self.alive)
                #    readback = ComServerService.ModbusClient.Read_register(616)
                #    if readback != self.alive:
                #        print 'PLC Com is down - please check wiring / PLC address / PLC power'
                #if self.alive >= 100:
                #    self.alive = 0
                time.sleep(self.interval)


if __name__ == "__main__":
    print '___________Waiting for client connection...'
    #Start comServer thread
    #ThreadedServer(ComServerService, port = 18861).start()
    ThreadedServer(ComServerService, port = 18861).start()
        
        
