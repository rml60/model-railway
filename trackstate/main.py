""" trackstate (main.py) MicroPython script
    
    Sends trackstates (16 contacts) as can-frame bytearray via WLAN
    
    Protocol: Maerklin can-bus
    
    The can command for trackstate (16) must be send with active responsebit!
    
    Author: Rainer Maier-Lohmann
    ---------------------------------------------------------------------------
    "THE BEER-WARE LICENSE" (Revision 42):
    <r.m-l@gmx.de> wrote this file.  As long as you retain this notice you
    can do whatever you want with this stuff. If we meet some day, and you 
    think this stuff is worth it, you can buy me a beer in return.
    ---------------------------------------------------------------------------
    (c) 2021
"""
from machine import Timer
import time

import hc4067
from mcan import mcanhash, mcancommand, states

#-------------------------------------------------------------------------------
# constants
#-------------------------------------------------------------------------------
VERSION = '0.04'
TIMER = Timer(0)
BUFFERSIZE = 13

#-------------------------------------------------------------------------------
# classes and functions
#-------------------------------------------------------------------------------
def handleInterrupt(TIMER):
  """
  """
  global currState
  currState = 0
  # inx.value ist entweder 0 oder 1
  #currState = currState | in0.value()*2**0
  #currState = currState | in1.value()*2**1
  currState = mp.signalValueByte

class OledInfoText():
  def __init__(self, oled, ipAddrStr, mcanHash, versionStr=VERSION):
    """
    """
    self.__oled = oled
    self.__version = 'Version:    {}'.format(versionStr)
    self.__hash = 'MCAN-Hash:  {}'.format(mcanHash)
    self.__ip = ipAddrStr

  def set(self):
    """
    """
    self.__oled.fill(0)
    oled.text('1234567890123456',0,16)
    self.__oled.text(self.__version, 0, 31, 2)
    self.__oled.text(self.__hash, 0, 40)
    self.__oled.text(self.__ip, 0, 55)

class CanConnection():
  def __init__(self):
    """
    """
    self.__csip = CSIP    
    self.__tcpPort = CSPORT
    print('CS-IP:',self.__csip,' Port:',self.__tcpPort)

    self.__socket = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    self.__socket.connect((self.__csip, self.__tcpPort))
    #self.__socket.setblocking(False)

  def send(self, mcanMsg):
    """
    """
    self.__socket.send(mcanMsg)

#-------------------------------------------------------------------------------
# main
#-------------------------------------------------------------------------------
if __name__ == '__main__':
  mp = hc4067.Hc4067( pinEn=32, pinSig=33
                  , pinS0=12, pinS1=13, pinS2=14, pinS3=15
                  , ports=2)
    
  currState = mp.signalValueByte
  recentState = currState
  trackstates = states.States()

  mcanHash = mcanhash.McanHash(macAddr)
  print('MAC-Adresse: {} - mcanHash: {}'.format(macAddrStr, mcanHash))
  mcanCmd = mcancommand.McanCommand(int(mcanHash))
  mcanCmd.setCommand(0x22,response=True)

  TIMER.init(period=50, mode=Timer.PERIODIC, callback=handleInterrupt)
  conn = None
  """while conn is None:
    try:
      conn = CanConnection()
      oled.text('connection Ok.',8,1)
      oled.show()
    except:
      oled.fill(0)
      oled.text('ERROR',44,1)
      oled.text('Central Station',0,16)
      oled.text(CSIP,8,25)
      oled.text('not found.',8,33)
      oled.text(wlan.ifconfig()[0],0,55)
      oled.show()
      conn = None
  """
  infoText = OledInfoText(oled, wlan.ifconfig()[0], mcanHash)
  infoText.set()
  trackstates.setStateBits(currState)
  oled.text(trackstates.shortStr,0,5)
  oled.show()
  while True:
    trackstates.setStateBits(currState)
    if trackstates.isChanged:
      infoText.set()
      oled.text(trackstates.shortStr,0,5)
      oled.show()
    if conn is not None:
      for subId, state, recentState in trackstates.changedStates:
        contactNo = CONTACTBASE + subId
        mcanCmd.setTrackState(DEVICEID, contactNo, state, recentState)
        #conn.send(mcanCmd.frame)
        print(DEVICEID, contactNo, state, mcanCmd.frame)

    trackstates.setRecentToCurrent()
    time.sleep_ms(100)
