#!/usr/bin/env python3
import socket
import sys
import struct
from functools import reduce
import threading
import queue

ECM = (6969,6970)
DPA = (6971,6972)

def toSignedChar(num):
    if type(num) is bytes:
        return struct.unpack('b',num)[0]
    else:
        return struct.unpack('b',struct.pack('B',num & 0xFF))[0]

def checksum(msg):
    return toSignedChar(~reduce(lambda x,y: (x + y) & 0xFF, list(msg)) + 1)


class SplitterThread(threading.Thread):
    def __init__(self,read_socket,queue):
        super(SplitterThread,self).__init__()
        self.read_socket = read_socket
        self.queue = queue
        self.source_mid = None

    def run(self):
        while True:
            message = self.read_socket.recv(1024)
            if self.source_mid == None:
                self.source_mid = struct.pack("B",message[0])
            post_transport = self.apply_transport_filter(message)
            messages = []
            for msg in post_transport:
                if not msg[1] in [b'\xc5',b'\xc6']:
                    msgs = self.apply_proprietary_filter(msg)
                    for amsg in msgs:
                        messages.append(amsg)
            
            for msg in messages:
                try:
                    self.queue.put_nowait(msg)
                except queue.Full:
                    self.queue.get()
                    self.queue.put_nowait(msg)

    def apply_proprietary_filter(self,message):
        idx = message.find(self.source_mid+b'\xfe',1)
        if idx > 0:
            thismsg = message[:idx]
            return [thismsg] + self.apply_proprietary_filter(message[idx:])

        else:
            return [message]


    def apply_transport_filter(self,message):
        if self.source_mid+b'\xc6' in message:
            return self.split_transport_data(message)
        elif self.source_mid+b'\xc5' in message:
            return self.split_transport_control(message)
        else:
            return [message]

    def split_transport_data(self,message):
        idx = message.find(self.source_mid+b'\xc6')
        if idx == 0 and len(message) > 4 + message[2]:
            return [message[:4+message[2]]]+self.apply_transport_filter(message[4+message[2]:])
        elif idx == 0:
            return [message]
        else:
            return [message[:idx]]+self.apply_transport_filter(message[idx:])

    def split_transport_control(self,message):
        idx = message.find(self.source_mid+b'\xc5')
        if idx == 0 and len(message) > 4 + message[2]:
            return [message[:4+message[2]]]+self.apply_transport_filter(message[4+message[2]:])
        elif idx == 0:
            return [message]
        else:
            return [message[:idx]]+self.apply_transport_filter(message[idx:])
            

class J1708Driver():
    #serveport: the port the the J1708 Driver. Defaults to the ECM driver, which is on port 6969
    #clientport: the port to listen on. The ECM driver sends to port 6970. Will add a method to register clients for more flexibility.
    def __init__(self,ports=ECM):
        self.serveport,self.clientport = ports
        self.sock = socket.socket(family=socket.AF_INET,type=socket.SOCK_DGRAM)
        self.sock.bind(('localhost',self.clientport))
        self.source_mid = None
        self.read_queue = queue.Queue(maxsize=10000)
        self.read_thread = SplitterThread(self.sock,self.read_queue)
        self.read_thread.start()

    #checksum: Checksum included in return value if True. Defaults to false.
    #returns the message read as bytes type.
    def read_message(self,checksum=False,time_out=5):
        if time_out is None:
            message = self.read_queue.get()
        else:
            try:
                message = self.read_queue.get(block=False,timeout=time_out)
            except queue.Empty:
                return None
        if checksum:
            return message
        else:
            return message[:-1]

    #buf: message to send as type bytes
    #has_check: True if your message includes checksum. Defaults to False.
    def send_message(self,buf,has_check=False):
        msg = buf
        if not has_check:
            check = struct.pack('b',checksum(msg))
            msg += check
        self.sock.sendto(msg,('localhost',self.serveport))



#Test to see if this works. Reads 10 messages, sends a CAT ATA SecuritySetup message.
#You should see a reply of the form \x80\xfe\xac\xf0\x?? if it works
if __name__ == '__main__':
    driver = J1708Driver(ECM)
    for i in range(0,10):
        print(repr(driver.read_message()))
    
    driver.send_message(b'\xAC\xFE\x80\xF0\x17')
    for i in range(0,10):
        print(repr(driver.read_message()))
