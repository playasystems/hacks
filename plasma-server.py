#! /usr/bin/env python

import colorsys
import sys

gp = __import__('gigglepixel-server')
from math import *
from random import randint
from time import sleep
from x256 import x256

ANIM_PERIOD = 0.05
PAL_EVERY = 5 

ROWS = 5 
COLS = 30

def send_pal():
  pass

def p(s):
  sys.stdout.write(s)

def dist(x0, y0, x1, y1):
  dx = x1-x0
  dy = y1-y0
  return sqrt(dx**2 + dy**2)

p("\033[H\033[2J")

up_guy = None
def draw_people(cycle):
  global up_guy
  p("\033[0m")

  if randint(0, 20) == 0:
    up_guy = None
  if randint(0, 40) == 0:
    up_guy = randint(0, COLS/3-1)

  for x in xrange(COLS/3):
    if x == up_guy:
      p("\\o/")
    else:
      p(".o.")
  p("\n")

cycle = 0
draw_people(cycle)

def loop():
  global cycle
  p("\033[H")  # Move to top-left corner

  draw_people(cycle)

  fg = None
  bg = None

  for y in xrange(ROWS):
    for x in xrange(COLS):
      v0 = sin(dist(x + cycle, y, 128.0, 128.0) / 8.0)
      v1 = sin(dist(x, y, 64.0, 64.0) / 8.0)
      v2 = 0 # sin(dist(x, y + cycle / 7, 192.0, 64) / 7.0)
      v3 = 0 # sin(dist(x, y, 192.0, 100.0) / 8.0)
      # Sum goes from -2 to +2; hue must be 0-1 
      hue = 0.5 + (v0 + v1 + v2 + v3) / 4.0
      rgb = list(int(255 * c) for c in colorsys.hsv_to_rgb(hue, 1, 1))
      ix = x256.from_rgb(*rgb)
      p("\033[38;5;%dm#" % ix)
      if (x == COLS / 2 and y == ROWS / 2):
        fg = rgb
      elif (x == 0 and y == 0):
        bg = rgb

    if (y < ROWS-2):
      p("\n")
    elif(y == ROWS-2):
      p("\033[90m%%\n")
    else:
      p("\033[90m%%%\n oo")
      p(" " * (COLS-6))
      p("oo   o\n")

  if (cycle % PAL_EVERY == 0):
    msg = gp.color_msg((fg, bg), source_id=2)
    gp.send_msg(msg)

  p("\n")
  sleep(ANIM_PERIOD)
  cycle += 1

try:
  while True:
    loop()
except KeyboardInterrupt:
  print "\033[0m\n"
