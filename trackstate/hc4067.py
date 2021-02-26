# The MIT License (MIT)
""" hardware.py
    =================================================================

    Simple drivers for external hardware to use with esp32.
     - 74HC4067 16-channel analog/digital Multiplexer 

    Author:   Rainer Maier-Lohmann
    
    Copyright (c) 2020 Rainer Maier-Lohmann
"""
from machine import Pin

class Hc4067():
  """ Simple driver for 74HC4067 16-channel analog/digital Multiplexer 
  """
  def __init__(self, pinEn, pinSig, pinS0, pinS1, pinS2, pinS3, addr=0, ports=16):
    self.__numberOfPorts = ports
    self.__enable = Pin(pinEn, Pin.OUT)
    self.__signal = Pin(pinSig, Pin.IN)
    self.__addrPins = [pinS0, pinS1, pinS2, pinS3]
    self.__pins = []
    for pin in self.__addrPins:
      self.__pins.append(Pin(pin, Pin.OUT))
    self.__addr = addr
    self.__setAddrBits()
  
  @property
  def signalValues(self):
    signalValues = []
    for addr in range(0,self.__numberOfPorts,1):
      self.__setAddr(addr)
      #signalValues.append(self.__signal.value())
      signalValues.append(self.__getRepeatedValue())
    return signalValues

  @property
  def signalValueByte(self):
    valueByte = 0
    for addr in range(0,self.__numberOfPorts,1):
      self.__setAddr(addr)
      value = self.__getRepeatedValue()
      if value != 0:
        valueByte |= 2**addr
      else:
        valueByte &= 0xFFFF - 2**addr
    return valueByte


  def signalValue(self, addr):
    self.__setAddr(addr)
    #return self.__signal.value()
    return self.__getRepeatedValue()

  def __getRepeatedValue(self):
    numberOfZeros = 0
    for i in range(0,25):
      val = self.__signal.value()
      if val == 0:
        numberOfZeros += 1
    if numberOfZeros > 20:
      val = 0
    else:
      val = 1
    return val
 
  def __setAddr(self, addr):
    self.__addr = addr
    self.__setAddrBits()
    
  def __isAddrBitSet(self, value, bitNr):
    return ((value & 2**bitNr) >>  bitNr) == True

  def __setAddrBitValues(self):
    self.__addrBitValues = []
    for index, pin in enumerate(self.__addrPins):
      self.__addrBitValues.append(self.__isAddrBitSet(self.__addr, index))
      
  def __setAddrBits(self):
    self.__setAddrBitValues()
    for pinValue, pin in zip(self.__addrBitValues, self.__pins):
      pin.value(pinValue)
