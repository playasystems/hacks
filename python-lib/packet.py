#! /usr/bin/env python3

import json
import struct
import sys
from base64 import b64encode, b64decode

if sys.version_info < (3, 0):
  sys.exit("Python 3 required")

class GPException(Exception):
  pass

class GPPacket():
  MAGIC = b"GLPX"
  LATEST_VERSION = 2
  NAME_LEN = 30

  packet_types = dict(PALETTE=1, SERVER_ID=3, CLIENT_ID=4)
  packet_types_by_number = {v: k for k, v in packet_types.items()} # reverse mapping
  
  @classmethod
  def new_setattr(self, name, value):
    if not hasattr(self, name):
      raise AttributeError("GPPacket has no %r field" % name)

  def __init__(self, version, priority, flags_int, source, dest, crc=None):
    self.version = int(version)
    self.priority = int(priority)
    self.flags = self.split8(int(flags_int))
    self.source = int(source)
    self.dest = int(dest)
    self.crc = crc
    self.packet_type = None
    self.payload = None
    self.__setattr__ = self.new_setattr

  @classmethod
  def unpack32(cls, b0, b1, b2, b3):
    return b0 << 24 | b1 << 16 | b2 << 8 | b3;

  @classmethod
  def unpack16(cls, b0, b1):
    return b0 << 8 | b1

  @classmethod
  def pack(cls, value, num_bytes):
    return value.to_bytes(num_bytes, 'big') 

  @classmethod
  def pack8(cls, value):
    return cls.pack(value, 1)

  @classmethod
  def pack16(cls, value):
    return cls.pack(value, 2)

  @classmethod
  def pack32(cls, value):
    return cls.pack(value, 4)

  @classmethod
  def join_bitlist(cls, bl):
    return int(''.join('01'[i] for i in bl), 2)

  @classmethod
  def pack_bitlist(cls, bl):
    n = cls.join_bitlist(bl)
    return cls.pack8(n)

  @classmethod
  def split8(cls, b):
    return [1 if b & (1 << (7-n)) else 0 for n in range(8)]

  @classmethod
  def unpack_double(cls, bytes):
    assert len(bytes) == 8
    a = struct.unpack('d', bytes)
    assert len(a) == 1
    return a[0]

  @classmethod
  def pack_double(cls, n):
    return struct.pack('d', n)

  @classmethod
  def unpack_float(cls, bytes):
    assert len(bytes) == 4
    a = struct.unpack('f', bytes)
    assert len(a) == 1
    return a[0]

  @classmethod
  def pack_float(cls, n):
    return struct.pack('f', n)

  @classmethod
  def calc_crc(cls, payload):
    crc = 0xFFFF
    for i in range(0, len(payload)):
        crc ^= payload[i] << 8
        for j in range(0,8):
            if (crc & 0x8000) > 0:
                crc = (crc << 1) ^ 0x1021
            else:
                crc = crc << 1
    return crc & 0xFFFF

  @classmethod
  def from_binary(cls, encoded):
    if len(encoded) < 14: raise GPException("Header too short")
    if not encoded.startswith(cls.MAGIC):
      raise GPException("Bad magic number");
    version = encoded[4]
    # Disabled the next line; go ahead and try to parse packets from the future
    # if version > LATEST_VERSION: raise GPException("Version from the future")
    length = cls.unpack16(encoded[5], encoded[6])
    if (length < 14): raise GPException("Length too short")
    if len(encoded) == length:
      crc_valid = None
    elif len(encoded) == length + 2:
      sans_payload = encoded[0:length]
      calculated_crc = cls.calc_crc(sans_payload)
      found_crc = cls.unpack16(encoded[length], encoded[length+1])
      crc_valid = found_crc == calculated_crc
    else:
      raise GPException("Length mismatch")
    priority = encoded[8]
    flags_int = encoded[9]
    source = cls.unpack16(encoded[10], encoded[11])
    dest = cls.unpack16(encoded[12], encoded[13])
    rv = GPPacket(version, priority, flags_int, source, dest, crc_valid)
    packet_type_num = encoded[7]
    packet_type = cls.packet_types_by_number.get(packet_type_num, None)
    if packet_type is None:
      raise GPException("Unknown packet type %d" % packet_type)
    if packet_type == "PALETTE": 
      decoder = GPPacket.decode_palette
    elif packet_type == "SERVER_ID":
      decoder = GPPacket.decode_server_id
    elif packet_type == "CLIENT_ID":
      decoder = GPPacket.decode_client_id
    else:
      raise SystemError("Internal error in decoding table")
    rv.packet_type = packet_type
    rv.payload=decoder(encoded[14:length])
    return rv
 
  @classmethod
  def decode_palette(cls, payload):
    if len(payload) < 2:
      raise GPException("Short palette header")
    num_entries = cls.unpack16(payload[0], payload[1])
    # Note that we allow palette bodies to have *trailing* data, for futureproofing
    if len(payload) < 2 + 4 * num_entries:
      raise GPException("Short palette body")
    entries = []
    for i in range(num_entries):
      start_index = 2 + 4 * i
      frac = payload[start_index]
      r = payload[start_index+1]
      g = payload[start_index+2]
      b = payload[start_index+3]
      entries.append(dict(frac=frac,red=r,green=g,blue=b))
    return dict(entries=entries)

  def encode_palette(self):
    rv = bytearray()
    entries = self.payload["entries"]
    rv += self.pack16(len(entries))
    for d in entries:
      rv += self.pack8(d["frac"])
      rv += self.pack8(d["red"])
      rv += self.pack8(d["green"])
      rv += self.pack8(d["blue"])
    return rv

  @classmethod
  def decode_server_id(cls, payload):
    name_bytes = payload[:cls.NAME_LEN]
    name = name_bytes.decode('UTF-8').strip('\0')
    # Ignore anything that follows, for future-proofing
    return dict(name=name)

  def encode_server_id(self):
    name_bytes = self.payload["name"].encode('UTF-8')
    name_bytes = name_bytes[:GPPacket.NAME_LEN]
    name_bytes = name_bytes.ljust(GPPacket.NAME_LEN, b'\0')
    return name_bytes

  @classmethod
  def decode_client_id(cls, payload):
    mac_bytes = payload[0:6]
    ip_bytes = payload[6:10]
    name_bytes = payload[10:10+cls.NAME_LEN]
    mac = ":".join(("%0.2X" % b for b in mac_bytes))
    ip = ".".join("%d" % b for b in ip_bytes)
    name = name_bytes.decode('UTF-8').strip('\0')
    # Ignore anything that follows, for future-proofing
    return dict(mac=mac, ip=ip, name=name)

  def encode_client_id(self):
    rv = bytearray()
    for b in self.payload["mac"].split(":"):
      rv += self.pack8(int(b, 16))
    for b in self.payload["ip"].split("."):
      rv += self.pack8(int(b))
    name_bytes = self.payload["name"].encode('UTF-8')
    name_bytes = name_bytes[:GPPacket.NAME_LEN]
    name_bytes = name_bytes.ljust(GPPacket.NAME_LEN, b'\0')
    rv.extend(name_bytes)
    return rv

  def to_binary(self):
    b = bytearray(self.MAGIC)
    b += self.pack8(self.version)
    b += b'\0\0' # Length; will be overwritten later
    packet_type_num = self.packet_types[self.packet_type] 
    b += self.pack8(packet_type_num)
    b += self.pack8(self.priority)
    b += self.pack_bitlist(self.flags)
    b += self.pack16(self.source)
    b += self.pack16(self.dest)
    b += self.encode_payload()
    length_bytes = self.pack16(len(b))
    b[5] = length_bytes[0]
    b[6] = length_bytes[1]
    if self.crc:
      b += self.pack16(self.calc_crc(b))
    return b

  def encode_payload(self):
   if self.packet_type == "PALETTE":
      return self.encode_palette()
   elif self.packet_type == "SERVER_ID":
      return self.encode_server_id()
   elif self.packet_type == "CLIENT_ID":
      return self.encode_client_id()
   else:
     raise SystemError("Internal error in encoding table")

  @classmethod
  def from_base64(cls, s):
    encoded = b64decode(s)
    return cls.from_binary(encoded)

  def to_base64(self):
    binary = self.to_binary()
    return b64encode(binary)

  def toJson(self, indent=2, sort_keys=True):
    d = dict()
    for k, v in self.__dict__.items():
      if not k.startswith("_"):
        d[k] = v
    return json.dumps(d, default=lambda o: o.__dict__, indent=indent, sort_keys=sort_keys)

  @classmethod
  def fromJson(cls, json_str):
    d = json.loads(json_str)
    packet_type = d.pop("packet_type")
    if packet_type not in cls.packet_types:
      raise ValueError("Unknown packet type %r" % packet_type) 
    version = d.pop("version", cls.LATEST_VERSION)
    priority = d.pop("priority", 0)
    flags = d.pop("flags", [0,0,0,0,0,0,0,0])
    flags_int = cls.join_bitlist(flags)
    source = d.pop("source", 0)
    dest = d.pop("dest", 0) 
    crc = d.pop("crc", None)

    gp = GPPacket(version, priority, flags_int, source, dest, crc)
    gp.packet_type = packet_type
    gp.payload = d.pop("payload", {})
    for k in d:
      sys.stderr.write("Leftover key: %r\n" % k)
    return gp 

if __name__ == '__main__':
    # For my first trick, I'll parse a JSON-encoded GigglePixel packet
    palette_json = """
{
  "packet_type": "PALETTE",
  "payload": {
    "entries": [ { "blue": 80, "frac": 100, "green": 90, "red": 68 } ]
  }
}
"""
    gp = GPPacket.fromJson(palette_json)

    # Next, I'll encode it in base64, with CRC
    gp.crc = True
    b64 = gp.to_base64()
    print (b64.decode() + "\n\n")

    # Now let's parse that base64 and print it as JSON
    gp = GPPacket.from_base64(b64)
    print (gp.toJson() + "\n\n")

    # And here's a SERVER_ID packet
    gp = GPPacket.fromJson('{"packet_type": "SERVER_ID", "payload": { "name": "Timbuktu Shrub" } }')
    print (gp.toJson())

    # And a CLIENT_ID as bytes
    client_bytes = [ 0x47, 0x4C, 0x50, 0x58, 0x02, 0x00, 0x36, 0x04, 0x05, 0x00, 0xAB, 0xF1,
                     0x00, 0x00, 0x44, 0x17, 0x93, 0x12, 0xAB, 0xF1, 0xC0, 0xA8, 0x01, 0x7C,
                     0x54, 0x45, 0x20, 0x4D, 0x65, 0x64, 0x61, 0x6C, 0x6C, 0x69, 0x6F, 0x6E,
                     0x20, 0x76, 0x30, 0x2E, 0x31, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ]
    gp = GPPacket.from_binary(bytearray(client_bytes))
    b64 = gp.to_base64()
    gp = GPPacket.from_base64(b64)
    print (gp.toJson())

