
import serial
import re
import csv
import signal
import sys
import os
import argparse
import time

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

    s=write_cmd(ser,b'0WC01B00\r', 'no autostart')
    s=write_cmd(ser,b'0WC00B00\r', 'no echo')
    s=write_cmd(ser,b'0WC02B00\r', 'raw data transfers')
    s=write_cmd(ser,b'0WC08B10\r', 'continuous ASCII send') # ASCII
    #s=write_cmd(ser,b'0WC08B11\r', 'continuous binary send') # Binary
    #s=write_cmd(ser,b'0WC35B50\r', 'delay of 0x50 between sends (.25 sec?)')
    s=write_cmd(ser,delay_cmd, f'delay of {hexrate} between sends (.25 sec?)')
    s=write_cmd(ser,b'0WC01B5A\r', 'autostart option on')

class MeasurementBuiler:
    def __init__(self, p):
        self.params = p
        self.count = 0
        self.current = b''

    def add(self,s):
        # a reading always ends in \x04, including the ack messages.
        # a reading always starts with MX:

        # add s to current
        # scan for end of message
        # slice s for call to store
        # return measurement from current, leaving remaining bytes

        rc = self.store(s)
        if rc == True:
            self.current=b''
        return rc

    def store(self, meas):
        rc=False
        ss=[float(x.strip(': ')) for x in self.params.pat.findall(meas.decode("utf-8"))]
        ss2 = [x/(2**15) for x in ss]
        # this check should not be here if the add() code checks for begin/end of measurement
        if len(ss)>1: 
            self.params.fout_csv.writerow(ss+ss2)
            self.params.fout.flush()
            self.count+=1
            rc=True
        return rc

# pass the parameters in as a struct
def collect_data(p):
    mb = MeasurementBuiler(p)
    print("sending 0sd to start data transfers")
    p.ser.write(b'0sd\r')

    # also check all_done flag here
    while not all_done and (p.total==0 | mb.count<p.total): 
        s = p.ser.read(100)
        mb.add(s)
        
        #s = ser.read(500)
        print(ss+ss2)


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
    # examples of swithes
    #parser.add_argument("-d","--show-dates", default=Fake.show_dates, action='store_true', dest="show_dates",help="Show dates on graph")
    #parser.add_argument("-r","--no-render", default=Fake.render, action='store_false', dest="render",help="Do not view the graph")
    pp = parser.parse_args()

    return pp


if __name__=="__main__":
    a = get_args()

    a.now = time.strftime('%Y%m%d-%H:%M:%S',time.localtime())
    a.RTS = rate_to_reg(a.rate)
    a.filename = "readings-{a.name}-{now}.csv" 
    a.pat = re.compile(':.* ')

    a.fout = open(filename,'w', newline='')
    a.fout_csv = csv.writer(fout, delimiter=',')
    a.fout_csv.writerow(["x.raw","y.raw","z.raw","T.raw","x","y","z","T", "mag", "az", "alt"])

    a.ser = serial.Serial(a.port, 9600, timeout=a.rate) # TTL
    print(a.ser)

    signal.signal(signal.SIGINT, signal_handler)
    initialize(a)
    # clear the device here (read until empty)
    collect_data(a)

    s = write_complete(a.ser)

    # add clear device here (read until empty) 
    s = a.ser.read(500)

    a.ser.close()
    a.fout.close()


