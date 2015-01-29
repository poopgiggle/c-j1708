#!/usr/bin/env python3.5
import threading
import J1708Driver
import struct
import time
import socket

dpa_mid = None
ecm_mid = None

logging_socket = socket.socket(family=socket.AF_INET,type=socket.SOCK_DGRAM)
logging_socket.bind(('localhost',13373))

class PassThread(threading.Thread):
    def __init__(self,inport,outport,name,filelock):#name is either "ECM" or "DPA"
        super(PassThread,self).__init__()
        self.inport = inport
        self.outport = outport
        self.name = name
        self.filelock = filelock

    def apply_filter(self,message):
        return [message]

    

    def run(self):
        while True:
            msg = self.inport.read_message(checksum=True)
            #subclass PassThread to get a different apply_filter function.


            if msg is not None and len(msg) > 0:
                self.outport.send_message(msg,has_check=True)
                

    



if __name__ == '__main__':
    ecmdriver = J1708Driver.J1708Driver(J1708Driver.ECM)
    dpadriver = J1708Driver.J1708Driver(J1708Driver.DPA)
    writelock = threading.Lock()
    threads = []
    threads.append(PassThread(ecmdriver,dpadriver,"ECM",writelock))
    threads.append(PassThread(dpadriver,ecmdriver,"DPA",writelock))
    list(map(lambda x: x.start(),threads))
    list(map(lambda x: x.join(), threads))

    
