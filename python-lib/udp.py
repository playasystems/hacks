#! /usr/bin/env python3

import socket
import sys
from time import time

from packet import *

GIGGLEPIXEL_PORT=7016

class GigglePixelListener:
  # Bind by default to "", which means INADDR_ANY (0.0.0.0) and thus listen on all available interfaces
  def __init__(self, interface="", port=GIGGLEPIXEL_PORT):
    self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    self.client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    self.client.bind((interface, port))

  def get_packet(self, timeout=None, print_errors=True):
    BUF_SIZE = 1024
    if timeout is not None:
      self.client.settimeout(timeout)

    try:
      data, addr = self.client.recvfrom(BUF_SIZE)
    except socket.timeout:
      return None

    try:
      return GPPacket.from_binary(data)
    except (AssertionError, GPException) as e:
      if print_errors:
        sys.stderr.write("Error parsing GP packet: %s\n" % e)
      return None

class GigglePixelBroadcaster:
  # Default to 255.255.255.255, which means "broadcast everywhere"
  def __init__(self, default_ip="255.255.255.255", default_port=GIGGLEPIXEL_PORT, source_override=None):
    self.default_ip = default_ip
    self.default_port = default_port
    self.source_override = source_override

  def send_packet(self, gp, ip=None, port=None, broadcast=True):
    if ip is None:
      ip = self.default_ip
    if port is None:
      port = self.default_port

    if self.source_override is not None:
      gp.source = self.source_override

    msg = gp.to_binary()
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    server.bind(('', GIGGLEPIXEL_PORT))
    if broadcast:
      server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    server.sendto(msg, (ip, port))
