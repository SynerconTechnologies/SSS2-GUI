import serial
import serial.tools.list_ports
import time

ser = serial.Serial("COM42",baudrate=4000000,timeout=0,
                                    parity=serial.PARITY_ODD,write_timeout=0,
                                    xonxoff=False, rtscts=False, dsrdtr=False)
i=0
print("Serial Listener")
ser.write(bytes("C0,1\n",'ascii'))
buffer=b''
while True:
    #if ser.inWaiting():
        lines = ser.readline()
        for line in lines:
            print(line)
        
