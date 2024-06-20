
import socket
import sys
import time

HOST = "195.168.0.195"
HOST = "scourge"
PORT = 6700

data = bytes("hello\n", 'utf-8')

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

for i in range(50):
    sock.sendto(data, (HOST,PORT))
    time.sleep(1)




