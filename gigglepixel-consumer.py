#! /usr/bin/env python
# -*- coding: utf8 -*-

# Show a dancing thing that (barely) consumes GigglePixel palette packets

PORT = 7016

import socket
import sys
from time import time
from x256 import x256

note = u'♪'
face = u'(・o･)'

def p(s):
  sys.stdout.write(s)

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
  p (l + face + r + ' ' + note + ' ')
  l, r = arms()
  p (l + face + r)
  p ("\n\033[1A")  # Keep drawing over and over on the same line

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
client.bind(("", PORT)) # Bind to INADDR_ANY (0.0.0.0) and thus listen on all available interfaces

def ord16(b0, b1):
  return ord(b0) << 8 | ord(b1)

def decode(s):
  if len(s) <= 16: return None
  if not s.startswith("GLPX"): return None
  msglen = ord16(s[5], s[6])
  if msglen <= 16: return None
  if ord(s[7]) != 1: return None
  num_colors = ord16(s[14], s[15])
  if num_colors < 1: return None
  color_data = s[16:]
  frac = color_data[0]
  r = ord(color_data[1])
  g = ord(color_data[2])
  b = ord(color_data[3])
  return (r,g,b)

BUF_SIZE = 1024
next_dance = time()
try:
  while True:
    draw()
    now = time()
    time_left = next_dance - now
    data = ""
    if time_left > 0:
      client.settimeout(time_left)
      try:
        data, addr = client.recvfrom(BUF_SIZE)
      except socket.timeout:
        pass
    rgb = decode(data)
    if rgb is None:
      next_dance = time() + 1
      arms()  # Toggle arm positions
    else:
      ix = x256.from_rgb(*rgb)
      p("\033[38;5;%dm" % ix)  
except KeyboardInterrupt:
  print "\033[0m"
