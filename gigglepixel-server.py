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
  rv += chr16(7 + len(msg))
  rv += msg
  return rv

# Construct a GigglePixel message with a single-entry color palette
def color_msg(colors, priority=1, flags=0, source_id=1, dest_id=1):
  msg = chr(1)
  msg += chr(priority)
  msg += chr(flags)
  msg += chr16(source_id)
  msg += chr16(dest_id)
  msg += chr16(len(colors))
  for rgb in colors:
    r,g,b = rgb
    fraction = 1
    msg += chr(fraction)
    msg += chr(r)
    msg += chr(g)
    msg += chr(b)
  return msg_wrap(msg)

def send_msg(msg):
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sock.sendto(msg, (IP, PORT))


if __name__ == '__main__':
  # Loop endlessly, sending these three RGB values at 1Hz
  colors = [(255,0,0), (0,255,0), (0,0,255)]
  while True:
    rgb = colors.pop(0)
    colors.append(rgb)
    msg = color_msg(colors)
    send_msg(msg)
    print "Sent new palette"
    time.sleep(1)
