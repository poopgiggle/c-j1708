import threading
import J1708Driver



def PassThread(threading.Thread):
    def __init__(self,inport,outport):
        super(PassThread,self).__init__()
        self.inport = inport
        self.outport = outport

    def run(self):
        msg = inport.read_message(checksum=True)
        outport.send_message(has_check=True)

if __name__ == '__main__':
    ecmdriver = J1708Driver.J1708Driver(J1708Driver.ECM)
    dpadriver = J1708Driver.J1708Driver(J1708Driver.DPA)
    threads = []
    threads.append(PassThread(ecmdriver,dpadriver))
    threads.append(PassThread(dpadriver,ecmdriver))
    list(map(lambda x: x.start(),threads))
    list(map(lambda x: x.join(), threads))

    
