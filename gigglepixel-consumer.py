#! /usr/bin/env python
# -*- coding: utf8 -*-

# Show a dancing thing that (barely) consumes GigglePixel palette packets

PORT = 8080

import socket
import time

note = u'♪'
face = u'(・o･)'

arm_phase = False
def arms():
  global arm_phase
  arm_phase = not arm_phase
  if arm_phase:
    return u'┏┛'
  else:
    return u'┗┓'

def draw():
  l, r = arms()
  print l + face + r + ' ' + note,
  l, r = arms()
  print l + face + r,
  arms() # Burn a call just so phases alternate between frames
  print "\033[1A" # Keep drawing over and over on the same line

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
client.bind(("", PORT))

BUF_SIZE = 1024
while True:
  data, addr = client.recvfrom(BUF_SIZE)

  # We're not actually decoding the packet or confirming that it's really GigglePixel.
  # We're not even decoding the full RGB value. We're just checking to see if it's
  # one of three hardcoded values: all-red, all-green, or all-blue. And, in fact,
  # if the optional CRC is present, this whole thing breaks. But ya gotta start somewhere!
  rgb = list(ord(c) for c in data[-3:])
  if (rgb[0] == 255): print "\033[31m",
  if (rgb[1] == 255): print "\033[32m",
  if (rgb[2] == 255): print "\033[34m",
  draw()
