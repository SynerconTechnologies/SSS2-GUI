#!/usr/bin/env python

import sys, os
import multiprocessing#
import queue #needed separately for the Empty exception
import time, datetime
import serial  # requires pyserial
import struct

class SerialReadProcess(multiprocessing.Process):
    def __init__(self, output_queue, port):
        multiprocessing.Process.__init__(self)
        self.output_queue = output_queue
        self.exit = multiprocessing.Event()
        self.f = None
        self.port = port
    def shutdown(self):
        self.exit.set()
    def run(self):
        print("setting up serial")
        with serial.Serial(self.port, timeout=0.1) as ser:
            ser.write(b'C0,1\n')
            ser.write(b'C1,1\n')
            print("Sent Streaming Request")
            while not self.exit.is_set():
                bytes_available = ser.inWaiting()
                if (bytes_available > 0):
                    try:
                        data = ser.read(bytes_available)
                        #print(data)
                        self.output_queue.put(data)
                    except queue.Full:
                        continue

def collectRawData(activeport):
    q = multiprocessing.Queue(maxsize=10000)
    s = SerialReadProcess(q, activeport)
    s.start()
    s.join()
    s.run()
    # write data from the queue to disk
    f = open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'raw.txt'), 'wb')
    f.seek(0)
    data_collection_started = False
    print( "READING DATA")
    while(True):
        try:
            data = q.get()
            print(data)
            f.write(data)
            data_collection_started = True;
            last_data_collection_time = time.time()
            sys.stdout.write('.')
        except queue.Empty:
            if data_collection_started:
                if (time.time() - last_data_collection_time) > 10:
                    print( "all done!")
                    break
    s.join()
    f.close()
    s.shutdown()
    
    

    
if __name__ == '__main__':
    collectRawData('COM42')
