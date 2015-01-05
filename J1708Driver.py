import socket
import sys
import struct
from functools import reduce
import select

ECM = (6969,6970)
DPA = (6971,6972)

def toSignedChar(num):
        if type(num) is bytes:
                return struct.unpack('b',num)[0]
        else:
                return struct.unpack('b',struct.pack('B',num & 0xFF))[0]

def checksum(msg):
#        msg = list(map(ord,msg))
        return toSignedChar(~reduce(lambda x,y: (x + y) & 0xFF, list(msg)) + 1)


class J1708Driver():
    #serveport: the port the the J1708 Driver. Defaults to the ECM driver, which is on port 6969
    #clientport: the port to listen on. The ECM driver sends to port 6970. Will add a method to register clients for more flexibility.
    def __init__(self,ports=ECM):
        self.serveport,self.clientport = ports
        self.sock = socket.socket(family=socket.AF_INET,type=socket.SOCK_DGRAM)
        self.sock.bind(('localhost',self.clientport))

    #checksum: Checksum included in return value if True. Defaults to false.
    #returns the message read as bytes type.
    def read_message(self,checksum=False,timeout=0.5):
        ready = select.select([self.sock],[],[],timeout)[0]
        if ready == []:
                return None
        else:
                message = self.sock.recv(256)
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

    def close(self):
        self.sock.close()

    def reBind(self):
        print("binding to %d" % self.clientport)
        self.sock.bind(('localhost',self.clientport))

#Test to see if this works. Reads 10 messages, sends a CAT ATA SecuritySetup message.
#You should see a reply of the form \x80\xfe\xac\xf0\x?? if it works
if __name__ == '__main__':
    driver = J1708Driver(ECM)
    for i in range(0,10):
        print(repr(driver.read_message()))
    
    driver.send_message(b'\xAC\xFE\x80\xF0\x17')
    for i in range(0,10):
        print(repr(driver.read_message()))
