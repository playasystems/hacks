#! /usr/bin/env python3

import sys

from random import randint
from time import sleep

from packet import *
from udp import *

MY_ID=123

# Print without newline
def p(s):
  sys.stdout.write(s)

broadcaster = GigglePixelBroadcaster(source_override=MY_ID)

while True:
  gp = GPPacket.fromJson('{"packet_type": "CLIENT_ID"}')
  gp.payload["ip"] = "1.2.3.%d" % randint(100, 200)
  gp.payload["mac"] = "88:88:88:88:%0.2X:%0.2X" % (randint(0x10, 0xff), randint(0x10, 0xff))
  gp.payload["name"] = "Fake client v1.0"
  print("Sending: %s %s %s" % (gp.payload["mac"], gp.payload["ip"], gp.payload["name"]))
  broadcaster.send_packet(gp)
  sleep(5)
