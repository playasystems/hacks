#! /usr/bin/env python3

PORT = 7016
TTL = 630

import socket
import sys
from time import time
from datetime import datetime

from udp import *

# Print without newline
def p(s):
  sys.stdout.write(s)

known_clients = dict()

def handle_packet(gp):
  if gp is None: return
  if gp.packet_type != "CLIENT_ID":
    return
  is_new = gp.payload["mac"] not in known_clients
  known_clients[gp.payload["mac"]] = time()
  if is_new:
    print("%s %s %s %s" % (datetime.now().strftime("%H:%M:%S"), gp.payload["mac"], gp.payload["ip"], gp.payload["name"]))

listener = GigglePixelListener()
while True:
  gp = listener.get_packet(1)
  handle_packet(gp)

  now = time()
  macs = list(known_clients.keys())
  for mac in macs:
    last_seen = known_clients[mac]
    age = now - last_seen
    if age > TTL:
      print("%s hasn't been seen in a while" % mac)
      known_clients.pop(mac) 
