#!/usr/bin/env python3

import J1708Driver
import struct
import threading
import select
import queue
import time
import multiprocessing
RTS = 1
CTS = 2
EOM = 3
RSD = 4
ABORT = 255

MGMT_PID = 197
DAT_PID = 198
TRANSPORT_PIDS = [MGMT_PID,DAT_PID]
class conn_mgmt_frame():
    def __init__(self,src=None,dst=None,conn_mgmt=None):
        self.src = src
        self.dst = dst
        self.conn_mgmt = conn_mgmt
        
        
class RTS_FRAME(conn_mgmt_frame):
    def __init__(self,src,dst,segments,length):
        super().__init__(src,dst,RTS)
        self.segments = segments
        self.length = length

    def to_buffer(self):
        return bytes([self.src,MGMT_PID,5,self.dst,self.conn_mgmt,self.segments,self.length & 0xFF,(self.length & 0xFF00) >> 8])

class CTS_FRAME(conn_mgmt_frame):
    def __init__(self,src,dst,num_segments,next_segment):
        super().__init__(src,dst,CTS)
        self.num_segments = num_segments
        self.next_segment = next_segment

    def to_buffer(self):
        return bytes([self.src,MGMT_PID,4,self.dst,self.conn_mgmt,self.num_segments,self.next_segment])

class EOM_FRAME(conn_mgmt_frame):
    def __init__(self,src,dst):
        super().__init__(src,dst,EOM)

    def to_buffer(self):
        return bytes([self.src,MGMT_PID,2,self.dst,self.conn_mgmt])


class RSD_FRAME(conn_mgmt_frame):
    def __init__(self,src,dst,request):
        super().__init__(src,dst,RSD)
        self.request = request

    def to_buffer(self):
        return bytes([self.src,MGMT_PID,4,self.dst,self.conn_mgmt,self.request & 0xFF,(self.request & 0xFF00) >> 8])

class ABORT_FRAME(conn_mgmt_frame):
    def __init__(self,src,dst):
        super().__init__(src,dst,ABORT)

    def to_buffer(self):
        return bytes([self.src,MGMT_PID,2,self.dst,self.conn_mgmt])


def parse_conn_frame(buf):
    src = buf[0]
    frame_bytes = buf[2]
    dst = buf[3]
    conn_mgmt = buf[4]
    if conn_mgmt == RTS:
        num_segments = buf[5]
        total_bytes = (buf[7] << 8) | buf[6]
        return RTS_FRAME(src,dst,num_segments,total_bytes)
    elif conn_mgmt == CTS:
        num_segments = buf[5]
        next_segment = buf[6]
        return CTS_FRAME(src,dst,num_segments,next_segment)
    elif conn_mgmt == EOM:
        return EOM_FRAME(src,dst)
    elif conn_mgmt == RSD:
        request = (buf[6] << 8) | buf[5]
        return RSD_FRAME(src,dst,request)
    elif conn_mgmt == ABORT:
        return ABORT_FRAME(src,dst)
    else:
        raise Exception("unrecognized conn_mgmt command code")

def is_conn_frame(buf):
    return len(buf) >= 5 and buf[1] == MGMT_PID

def is_rts_frame(buf):
    return is_conn_frame(buf) and buf[4] == RTS

def is_abort_frame(buf):
    return is_conn_frame(buf) and buf[4] == ABORT


class conn_mode_transfer_frame():
    def __init__(self,src,dst,segment_id,segment_data):
        self.src = src
        self.dst = dst
        self.segment_id = segment_id
        self.segment_data = segment_data

    def to_buffer(self):
        return bytes([self.src,DAT_PID,2+len(self.segment_data),self.dst,self.segment_id])+self.segment_data

def parse_data_frame(buf):
    
    src = buf[0]
    dst = buf[3]
    segment_id = buf[4]
    segment_data = buf[5:]
    
    return conn_mode_transfer_frame(src,dst,segment_id,segment_data)

def is_data_frame(buf):
    return len(buf) >= 6 and buf[1] == DAT_PID



class J1587ReceiveSession(threading.Thread):
    def __init__(self,rts_raw,out_queue,mailbox):
        super(J1587ReceiveSession,self).__init__()
        self.rts = parse_conn_frame(rts_raw)
        self.my_mid = self.rts.dst
        self.other_mid = self.rts.src
        self.in_queue = queue.Queue()
        self.out_queue = out_queue
        self.mailbox = mailbox

    def run(self):
        segments = self.rts.segments
        length = self.rts.length
        segment_buffer = [None] * segments
        cts = CTS_FRAME(self.my_mid,self.other_mid,segments,1)
        self.out_queue.put(cts.to_buffer())
        start_time = time.time()
        while None in segment_buffer and time.time() - start_time < 60:
            msg = None
            try:
                msg = self.in_queue.get(block=True,timeout=2)
            except queue.Empty:
                for i in range(segments):
                    if segment_buffer[i] is None:
                        cts = CTS_FRAME(self.my_mid,self.other_mid,1,i+1)
                        self.out_queue.put(cts.to_buffer())
                        time.sleep(.1)
            if msg is None:
                continue

            if is_abort_frame(msg):
                break
            elif is_rts_frame(msg):
                continue
            elif is_conn_frame(msg):
                abort = ABORT_FRAME(self.my_mid,self.other_mid)
                for i in range(3):
                    self.out_queue.put(abort.to_buffer())
                    break
            elif is_data_frame(msg):
                dat = parse_data_frame(msg)
                segment_buffer[dat.segment_id-1] = dat
            else:
                raise Exception("J1587 Session Thread shouldn't have received %s" % repr(msg))

        if None in segment_buffer:
            abort = ABORT_FRAME(self.my_mid,self.other_mid)
            for i in range(3):
                self.out_queue.put(abort.to_buffer())
            return #timed out

        eom = EOM_FRAME(self.my_mid,self.other_mid)
        for i in range(3):
            self.out_queue.put(eom.to_buffer())
        data = bytes([self.other_mid])
        for segment in segment_buffer:
            data += segment.segment_data

        self.mailbox.put(data)

    def give(self,msg):
        self.in_queue.put(msg)

class J1587SendSession(threading.Thread):
    def __init__(self,src,dst,msg,out_queue,success):
        super(J1587SendSession,self).__init__()
        self.src = src
        self.dst = dst
        self.msg = msg
        self.out_queue = out_queue
        self.in_queue = queue.Queue()
        self.success = success

    def run(self):
        data_list = []
        data_frames = []
        #chop up data
        msg = self.msg
        data_len = len(msg)
        while len(msg) > 0:
            data_list += [msg[:15]]
            msg = msg[15:]

        #package data into transfer frames
        i = 1
        for el in data_list:
            frame = conn_mode_transfer_frame(self.src,self.dst,i,el)
            data_frames += [frame]
            i += 1

        #send rts
        rts = RTS_FRAME(self.src,self.dst,len(data_frames),data_len)
        self.out_queue.put(rts.to_buffer())

        #begin sending loop
        eom_recvd = False
        start_time = time.time()
        while (not eom_recvd) and time.time() - start_time < 10:
            try:
                msg = self.in_queue.get(block=True,timeout=2)
            except queue.Empty:
                time.sleep(3)
                continue
            if not is_conn_frame(msg):
                raise Exception("J1587SendSession should not receive %s" % repr(msg))

            frame = parse_conn_frame(msg)
            if frame.conn_mgmt == EOM:
                eom_recvd = True
                continue
            elif frame.conn_mgmt == ABORT:
                break
            elif frame.conn_mgmt == CTS:
                base = frame.next_segment - 1
                for i in range(frame.num_segments):
                    self.out_queue.put(data_frames[base+i].to_buffer())
            else:
                pass#Either a RTS or RSD frame...why?
            
        if eom_recvd:
            self.success.set()

    def give(self,msg):
        self.in_queue.put(msg)

        
class J1708WorkerThread(threading.Thread):
    def __init__(self,read_queue):
        super(J1708WorkerThread,self).__init__()
        self.read_queue = read_queue
        self.stopped = threading.Event()
        self.driver = J1708Driver.J1708Driver(J1708Driver.ECM)

    def run(self):
        while not self.stopped.is_set():
            msg = self.driver.read_message(checksum=True,timeout=0.1)
            if msg is not None:
                self.read_queue.put(msg)

    def join(self,timeout=None):
        self.stopped.set()
        super(J1708WorkerThread,self).join(timeout=timeout)

    def send_message(self,msg,has_check=False):
        self.driver.send_message(msg,has_check)


class J1587WorkerThread(threading.Thread):
    def __init__(self,my_mid):
        super(J1587WorkerThread,self).__init__()
        self.my_mid = my_mid
        self.read_queue = multiprocessing.Queue()
        self.send_queue = multiprocessing.Queue()
        self.mailbox = queue.Queue()
        self.sessions = {}
        self.worker = J1708WorkerThread(self.read_queue)
        self.stopped = threading.Event()

    def run(self):
        self.worker.start()
        while not self.stopped.is_set():
            qs = select.select([self.read_queue._reader,self.send_queue._reader],[],[],1)[0]
            if qs is []:
                continue
            for q in qs:
                if q is self.read_queue._reader:
                    while not self.read_queue.empty():
                        msg = self.read_queue.get()
                        self.handle_message(msg)
                else:
                    while not self.send_queue.empty():
                        msg = self.send_queue.get()
                        self.worker.send_message(msg)
                    

        self.worker.join()

    def handle_message(self,msg):
        if len(msg) < 4 or msg[1] not in TRANSPORT_PIDS:
            self.mailbox.put(msg)
        elif not msg[3] == self.my_mid:#connection message not for us; just pass it on
            self.mailbox.put(msg)
        else:
            if bytes([msg[0]]) in list(self.sessions.keys()) and self.sessions[bytes([msg[0]])].is_alive():
                self.sessions[bytes([msg[0]])].give(msg)
            else:
                if is_rts_frame(msg):
                    session = J1587ReceiveSession(msg,self.send_queue,self.mailbox)
                    self.sessions[bytes([msg[0]])] = session
                    session.start()
                else:
                    abort = ABORT_FRAME(self.my_mid,msg[0])
                    self.send_queue.put(abort.to_buffer())

    def read_message(self,block=True,timeout=None):
        return self.mailbox.get(block=block,timeout=timeout)

    def send_message(self,msg):
        self.send_queue.put(msg)

    def transport_send(self,dst,msg):
        success = threading.Event()
        send_session = J1587SendSession(self.my_mid,dst,msg,self.send_queue,success)
        self.sessions[bytes([dst])] = send_session
        send_session.start()
        send_session.join()
        if not success.is_set():
            raise Exception("J1587 send either aborted or timed out")

    def join(self,timeout=None):
        self.stopped.set()
        super(J1587WorkerThread,self).join(timeout=timeout)
        

class J1587Driver():
    def __init__(self,my_mid):
        self.my_mid = my_mid
        self.J1587Thread = J1587WorkerThread(self.my_mid)
        self.J1587Thread.start()

    def read_message(self):
        return self.J1587Thread.read_message()

    def send_message(self,msg):
        self.J1587Thread.send_message(msg)

    def transport_send(self,dst,msg):
        self.J1587Thread.transport_send(dst,msg)

    def __del__(self):
        self.J1587Thread.join(timeout=1)
        
if __name__ == '__main__':
    driver = J1587Driver(0xb6)
    msg = b'\x00\xc8\x07\x04\x06\x00\x46\x41\x41\x5a\x05\x48'
    driver.transport_send(0x80,msg)
    for i in range(100):
        print(repr(driver.read_message()))

