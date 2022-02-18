#! /usr/bin/env python

import socket
import time

IP = '127.0.0.1'
PORT = 8080
VERSION=2

def chr16(w):
  return chr(w/256) + chr(w%256)

def msg_wrap(msg):
  rv = "GLPX"
  rv += chr(VERSION)
  rv += chr16(len(msg))
  rv += msg
  return rv

# Construct a GigglePixel message with a single-entry color palette
def color_msg(r,g,b, priority=1, flags=0, source_id=1, dest_id=1):
  msg = chr(1)
  msg += chr(priority)
  msg += chr(flags)
  msg += chr16(source_id)
  msg += chr16(dest_id)
  msg += chr16(1)
  fraction = 1
  msg += chr(fraction)
  msg += chr(r)
  msg += chr(g)
  msg += chr(b)
  return msg_wrap(msg)

# Loop endlessly, sending these three RGB values at 1Hz
colors = [(255,0,0), (0,255,0), (0,0,255)]
while True:
  rgb = colors.pop(0)
  colors.append(rgb)
  msg = color_msg(*rgb)
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sock.sendto(msg, (IP, PORT))
  time.sleep(1)
