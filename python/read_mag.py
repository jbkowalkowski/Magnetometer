
import serial
import re
import csv
import signal
import sys

all_done = False

def write_complete(ser):
    ser.write(b'\x13\r')
    s=write_cmd(ser,b'0WC01B00\r')
    print(s)
    all_done = True
    return s

def write_cmd(ser, st):
    ser.write(b'0L\r')
    b1 = ser.read(100)
    ser.write(st)
    b2 = ser.read(100)
    return b1+b2

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    
    sys.exit(0)

pat = re.compile(':.* ')
signal.signal(signal.SIGINT, signal_handler)

ser = serial.Serial('COM1', 9600, timeout=.25) # TTL
#ser = serial.Serial('COM3', 9600, timeout=.5) # RS232
print(ser)

s=write_cmd(ser,b'0WC01B00\r')
print(s)
s=write_cmd(ser,b'0WC00B00\r')
print(s)
s=write_cmd(ser,b'0WC02B00\r')
print(s)
s=write_cmd(ser,b'0WC08B10\r') # ASCII
#s=write_cmd(ser,b'0WC08B11\r') # Binary
print(s)
s=write_cmd(ser,b'0WC35B50\r')
print(s)
s=write_cmd(ser,b'0WC01B5A\r')
print(s)

ser.write(b'0sd\r')

fout = open("readings.csv",'w', newline='')
fout_csv = csv.writer(fout, delimiter=',')
fout_csv.writerow(["x_r","y_r","z_r","T_r","x","y","z","T"])

for i in range(150):
    if all_done: break
    s = ser.read_until(expected='\n', size=500)
    ss=[float(x.strip(': ')) for x in pat.findall(s.decode("utf-8"))]
    ss2 = [x/(2**15) for x in ss]
    
    #s = ser.read(500)
    print(ss+ss2)
    if len(ss)>1: fout_csv.writerow(ss+ss2)
    #print(s, file=fout)

s = write_complete(ser)

#print(s, file=fout)
s = ser.read(500)
#s = ser.read_until('\x04', 500)
print(s)
#print(s, file=fout)

ser.close()
fout.close()


