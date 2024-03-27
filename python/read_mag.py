'''
let azim = Math.atan( dx / dy ); // keep result in radians
let elev = Math.asin( dz / dist );

 X = Math.round( dist * ( Math.cos( elev ) * Math.sin( azim ) ) );
 Y = Math.round( dist * ( Math.cos( elev ) * Math.cos( azim ) ) );
 Z = Math.round( dist * Math.sin( elev ) );
'''




import serial
import re
import csv
import signal
import sys
import os
import argparse
import time
from math import sqrt, atan, pi, acos, atan2, asin
import numpy as np
from datetime import datetime as dt

'''

Command formats:
1) send command to modify register value:
    0L\r
2) send modification:
    0WC<register>B<value>\r

There will be a response to both (1) and (2).
It will be something like: 
    "Enabled!\r\n\x04" for (1)
    "Done\r\n\x04" for (2)

The format of a reading is:
    "MX:<value> \r\nMY:<value> \r\nMZ:<value> \r\nT:  <value>  \r\n\x04"

'''

all_done = False

def write_cmd(ser, st, msg):
    ser.write(b'0L\r')
    b1 = ser.read(100)
    print(f'request command, response {b1}')
    ser.write(st)
    b2 = ser.read(100)
    print(f'requst change {msg}, response {b2}')
    return b2

def write_complete(ser):
    ser.write(b'\x13\r')
    s=write_cmd(ser,b'0WC01B00\r', 'stopping autostart')
    all_done = True
    return s

def signal_handler(sig, frame):
    print('You pressed Ctrl+C to stop processing!')
    all_done=True
    #sys.exit(0)

def rate_to_reg(rate):
    # 80 = 0x50 ~= .25 seconds (just a guess)
    m=80/.25
    return hex(int(rate*m))[2:]

def initialize(args):
    hexrate = rate_to_reg(args.rate)
    delay_cmd = bytes(f'0WC35B{hexrate}\r','utf-8')

    s=write_cmd(args.ser,b'0WC01B00\r', 'no autostart')
    s=write_cmd(args.ser,b'0WC00B00\r', 'no echo')
    s=write_cmd(args.ser,b'0WC02B00\r', 'raw data transfers')
    s=write_cmd(args.ser,b'0WC08B10\r', 'continuous ASCII send') # ASCII
    #s=write_cmd(args.ser,b'0WC08B11\r', 'continuous binary send') # Binary
    #s=write_cmd(args.ser,b'0WC35B50\r', 'delay of 0x50 between sends (.25 sec?)')
    s=write_cmd(args.ser,delay_cmd, f'delay of {hexrate} between sends (.25 sec?)')
    s=write_cmd(args.ser,b'0WC01B5A\r', 'autostart option on')

def clear_device(args):
    all_s=b''
    while(True):
        s = args.ser.read(10)
        if len(s) == 0: break
        all_s = all_s + s
    return all_s

def to_r(x,y,z):
    return sqrt(x**2+y**2+z**2)

# azimuth
def to_theta(x,y,z):
    r=to_r(x,y,z)
    m=sqrt(x**2+y**2)
    return atan2(x,y) #* (180/pi)
    return acos(z/r)
    return atan(m/z) if z>0 else \
        atan(m/z)+pi if z<0 else \
            pi/2 if z==0 and x*y!=0 else \
                None if x==0 and y==0 and z==0 else 0 

# elevation
def to_phi(x,y,z):
    r=to_r(x,y,z)
    return asin(z/r) #* (180/pi)
    return np.sign(y)*acos(x/sqrt(x**2+y**2))
    return atan(y/x) if x>0 else \
        atan(y/x)+pi if x<0 and y>=0 else \
            atan(y/x)-pi if x<0 and y<0 else \
                pi/2 if x==0 and y>0 else \
                    -pi/2 if x==0 and y<0 else \
                        None if x==0 and y==0 else 0

class MeasurementBuilder:
    def __init__(self, p):
        self.params = p
        self.count = 0
        self.current = b''
        self.state = 's' # state 's' find start, 'e' find end

        p.fout = open(a.filename,'w', newline='')
        p.fout_csv = csv.writer(a.fout, delimiter=',')
        p.fout_csv.writerow(["timestamp","x.raw","y.raw","z.raw","T.raw","x","y","z","T", "mag", "az", "alt"])


    def extract_all(self):
        rc=False

        if self.state=='s':
            i=self.current.find(b"MX")
            if i>=0:
                self.current=self.current[i:]
                self.state='e'
        if self.state == 'e':
            i=self.current.find(b'\x04')
            if i>=0:
                meas = self.current[0:i+1]
                self.current=self.current[i+1:]
                self.store(meas)
                self.state='s'
                rc=True

        #print(f'state={self.state}, rc={rc}')
        return rc


    def add(self,s):
        # a reading always ends in \x04, including the ack messages.
        # a reading always starts with MX:

        # add s to current
        # scan for end of message
        # slice s for call to store
        # return measurement from current, leaving remaining bytes

        rc=0
        self.current += s
        while(self.extract_all()==True):
            rc+=1

        return rc

    def store(self, meas):
        now = dt.now().strftime("%y-%m-%d %H:%M:%S")
        rc=False
        ss=[float(x.strip(': ')) for x in self.params.pat.findall(meas.decode("utf-8"))]
        ss2 = [x/(2**15) for x in ss]
        mag = sqrt(ss2[0]**2 + ss2[1]**2 + ss2[2]**2)
        az=to_theta(ss2[0], ss2[1], ss2[2])
        alt=to_phi(ss2[0], ss2[1], ss2[2])
        self.params.fout_csv.writerow([now]+ss+ss2+[mag,az,alt])
        self.params.fout.flush()
        self.count+=1
        rc=True
        return rc

# pass the parameters in as a struct
def collect_data(p):
    mb = MeasurementBuilder(p)
    print("sending 0sd to start data transfers")
    p.ser.write(b'0sd\r')

    # also check all_done flag here
    while not all_done and (p.total==0 | mb.count<p.total): 
        s = p.ser.read(100)
        mb.add(s)
        print('.', end='')

    print("Stopping data collection")
    # last measurement is discarded
    s = write_complete(p.ser)
    s = clear_device(p)

class Fake:
    port="COM3"
    total_samples=0
    name=''
    rate=.25

def get_args():
    if 'site-packages' in sys.argv[0]: # os.path.basename(sys.argv[0]):
        # provide a fake for interactive application use
        return Fake()

    parser = argparse.ArgumentParser()
    parser.add_argument("-p","--port", default=Fake.port, dest="port",help="Serial communication port to use e.g. COM2")
    parser.add_argument("-n","--num-samples", default=Fake.total_samples, dest="total_samples",help="Total number of samples to collect, default: 0=go forever")
    parser.add_argument("-r","--run-name", default=Fake.name, dest="name",help="Name of this run (optional)")
    parser.add_argument("-s","--send_rate", default=Fake.rate, dest="rate",help="Send rate in seconds (default = .25)")
    parser.add_argument("-t","--test", default=False, action='store_true', dest="test",help="run a simple test")
    # examples of swithes
    #parser.add_argument("-d","--show-dates", default=Fake.show_dates, action='store_true', dest="show_dates",help="Show dates on graph")
    #parser.add_argument("-r","--no-render", default=Fake.render, action='store_false', dest="render",help="Do not view the graph")
    pp = parser.parse_args()

    if pp.test:
        pp.name="test"

    return pp

def do_test(a):
    f = open("../data/test_data.txt", mode="rb")
    data_in = f.read().decode("unicode_escape")
    f.close()

    print("From file:")
    #print(data_in)
    print(f'type = {type(data_in)}, length={len(data_in)}')
    data = data_in.encode('utf-8')
    print("Converted to bytes")
    print(data)
    #print(data.decode())
    print(f'type = {type(data)}, length={len(data)}')
    print(data.find(b'\x04'))


    mb = MeasurementBuilder(a)
    c = mb.add(data)
    print(f'test count = {c}')


if __name__=="__main__":
    a = get_args()

    a.now = time.strftime('%Y%m%d-%H-%M-%S',time.localtime())
    a.RTS = rate_to_reg(a.rate)
    a.filename = f"readings-{a.name}-{a.now}.csv" 
    a.pat = re.compile(':.* ')


    if a.test:
        do_test(a)
        sys.exit(0)

    a.ser = serial.Serial(a.port, 9600, timeout=a.rate) # TTL
    print(a.ser)

    signal.signal(signal.SIGINT, signal_handler)
    initialize(a)
    clear_device(a)
    collect_data(a)

    a.ser.close()
    a.fout.close()


