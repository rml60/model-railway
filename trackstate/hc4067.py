""" hardware.py

    Simple drivers for external hardware to use with esp32.
     - 74HC4067 16-channel analog/digital Multiplexer 
     
    gnd: 4067-pin12, vcc: 4067-pin24
    sig: 4067-pin1,  en:  4067-pin15
    s0:  4067-pin10, s1:  4067-pin11, s2:  4067-pin14, s3:  4067-pin13
    y0:  4067-pin9,  y1:  4067-pin8,  y2:  4067-pin7,  y3:  4067-pin6
    y4:  4067-pin5,  y5:  4067-pin4,  y6:  4067-pin3,  y7:  4067-pin2
    y8:  4067-pin23, y9:  4067-pin22, y10: 4067-pin21, y11: 4067-pin20
    y12: 4067-pin19, y13: 4067-pin18, y14: 4067-pin17, y15: 4067-pin16

    Author:   Rainer Maier-Lohmann
    ---------------------------------------------------------------------------
    "THE BEER-WARE LICENSE" (Revision 42):
    <r.m-l@gmx.de> wrote this file.  As long as you retain this notice you
    can do whatever you want with this stuff. If we meet some day, and you 
    think this stuff is worth it, you can buy me a beer in return.
    ---------------------------------------------------------------------------    
    Copyright (c) 2021 
"""
from machine import Pin
from utime import sleep_us

#-------------------------------------------------------------------------------
# constants
#-------------------------------------------------------------------------------
CHECK_MAX = 100
CHECK_MIN_ZEROS = 20
CHECK_DELAY_US = 250
PORTS_DEFAULT = 16

#-------------------------------------------------------------------------------
# classes
#-------------------------------------------------------------------------------
class Hc4067():
  """ Simple driver for 74HC4067 16-channel analog/digital Multiplexer 
  """
  def __init__( self
              , pinSig
              , pinS0, pinS1, pinS2, pinS3
              , addr=0
              , pinEn = None # via hardware set to 0 - no need to configure
              , ports=PORTS_DEFAULT
              ):
    self.__numberOfPorts = ports
    self.__enable = Pin(pinEn, Pin.OUT) if pinEn else None
    self.__signal = Pin(pinSig, Pin.IN, Pin.PULL_UP)
    self.__addrPins = [pinS0, pinS1, pinS2, pinS3]
    self.__pins = []
    for pin in self.__addrPins:
      self.__pins.append(Pin(pin, Pin.OUT))
    self.__addr = addr
    self.__setAddrBits()
  
  @property
  def portValues(self):
    """ returns a list with all inport values.
    """
    portValues = []
    for addr in range(0, self.__numberOfPorts, 1):
      self.__setAddr(addr)
      value = self.__getRepeatedValue()
      portValues.append(value)
    return portValues

  @property
  def valueByte(self):
    """ returns a integer with the sum of all inport values according to the
        bitposition. bitposition = address
        ( 1 = 1 (value=2^0, ..., 16 = 16 (value=2^15) )
    """
    valueByte = 0
    for addr in range(0, self.__numberOfPorts, 1):
      self.__setAddr(addr)
      value = self.__getRepeatedValue()
      if value != 0:
        valueByte |= 2**addr
      else:
        valueByte &= 0xFFFF - 2**addr
    return valueByte

  def readPortValue(self, addr):
    """ returns the value of the inport of the address.
    """
    self.__setAddr(addr)
    return self.__getRepeatedValue()

  def __getRepeatedValue(self):
    """ returns the interpreted value of the selected inport.
        Value is 1, if a minimal count of zeros were readed in a loop for
        specified times.       
        values: 1 - set, 0 - open 
    """
    numberOfZeros = 0
    bitVal = 0
    for i in range(0, CHECK_MAX):
      val = self.__signal.value()
      if val == 0:
        numberOfZeros += 1
      if numberOfZeros >= CHECK_MIN_ZEROS:
        bitVal = 1
        break
      sleep_us(CHECK_DELAY_US)
    return bitVal
 
  def __setAddr(self, addr):
    """ sets the address for selecting the inport.
    """
    self.__addr = addr
    self.__setAddrBits()
    
  def __isAddrBitSet(self, value, bitNo):
    """ True, if the given bit number in value is set.
    """
    return ((value & 2**bitNo) >> bitNo)

  def __setAddrBitValues(self):
    """ sets the address bits according to the address
    """
    self.__addrBitValues = []
    for index, pin in enumerate(self.__addrPins):
      self.__addrBitValues.append(self.__isAddrBitSet(self.__addr, index))
      
  def __setAddrBits(self):
    """ sets the address out pins according to the address bits
    """
    self.__setAddrBitValues()
    for pinValue, pin in zip(self.__addrBitValues, self.__pins):
      pin.value(pinValue)
