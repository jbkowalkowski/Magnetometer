
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


def initialize():
    s=write_cmd(ser,b'0WC01B00\r', 'no autostart')
    s=write_cmd(ser,b'0WC00B00\r', 'no echo')
    s=write_cmd(ser,b'0WC02B00\r', 'raw data transfers')
    s=write_cmd(ser,b'0WC08B10\r', 'continuous ASCII send') # ASCII
    #s=write_cmd(ser,b'0WC08B11\r', 'continuous binary send') # Binary
    s=write_cmd(ser,b'0WC35B50\r', 'delay of 0x50 between sends (.25 sec?)')
    s=write_cmd(ser,b'0WC01B5A\r', 'autostart option on')

# pass the parameters in as a struct
def collect_data(ser, total, fout):
    print("sending 0sd start data transfers")
    ser.write(b'0sd\r')

    # also check all_done flag here
    for i in range(total):
        if all_done: break
        s = ser.read_until(expected='\n', size=500)
        ss=[float(x.strip(': ')) for x in pat.findall(s.decode("utf-8"))]
        ss2 = [x/(2**15) for x in ss]
        
        #s = ser.read(500)
        print(ss+ss2)
        if len(ss)>1: fout.writerow(ss+ss2)
        # be sure to flush the data


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

def rate_to_reg(rate):
    # 80 = 0x50 ~= .25 seconds (just a guess)
    m=80/.25
    return hex(int(rate*m))[2:]


if __name__=="__main__":
    a = get_args()

    now = time.strftime('%Y%m%d-%H:%M:%S',time.localtime())
    RTS = rate_to_reg(a.rate)
    filename = "readings-{a.name}-{now}.csv" 

    pat = re.compile(':.* ')
    signal.signal(signal.SIGINT, signal_handler)

    fout = open(filename,'w', newline='')
    fout_csv = csv.writer(fout, delimiter=',')
    fout_csv.writerow(["x.raw","y.raw","z.raw","T.raw","x","y","z","T", "mag", "az", "alt"])

    ser = serial.Serial(a.port, 9600, timeout=a.rate) # TTL
    print(ser)

    s = write_complete(ser)

    # add clear output here... 

    #print(s, file=fout)
    s = ser.read(500)
    #s = ser.read_until('\x04', 500)
    print(s)
    #print(s, file=fout)


    ser.close()
    fout.close()


