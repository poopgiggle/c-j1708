import threading
import J1708Driver
import struct


class PassThread(threading.Thread):
    def __init__(self,inport,outport):
        super(PassThread,self).__init__()
        self.inport = inport
        self.outport = outport

    def apply_filter(self,message):
        return [message]
    

    def run(self):
        while True:
            message = self.inport.read_message(checksum=True)
            #subclass PassThread to get a different apply_filter function.
            msgs = self.apply_filter(message)
            if len(msgs) > 0:
                for msg in msgs:
                    self.outport.send_message(msg,has_check=True)

    


class CatECMThread(PassThread):
    def apply_filter(self,message):
        idx = message.find(b'\x80\xfe\xac',1)
        if idx > 0:
            thismsg = message[:idx]
            check = struct.pack('b',J1708Driver.checksum(thismsg))
            thismsg += check
            return [thismsg] + apply_filter(message[idx:])

        else:
            return [message]

class DDECECMThread(PassThread):
    def apply_filter(self,message):
        if message.find(b'\xfe\x80\xc7\x06') == 1:
            return []
        else:
            return [message]


if __name__ == '__main__':
    ecmdriver = J1708Driver.J1708Driver(J1708Driver.ECM)
    dpadriver = J1708Driver.J1708Driver(J1708Driver.DPA)
    threads = []
    threads.append(CatECMThread(ecmdriver,dpadriver))
    threads.append(PassThread(dpadriver,ecmdriver))
    list(map(lambda x: x.start(),threads))
    list(map(lambda x: x.join(), threads))

    
