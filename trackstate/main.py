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
import usocket
import time

import hc4067
from mcan import mcanhash, mcancommand, states

#-------------------------------------------------------------------------------
# constants
#-------------------------------------------------------------------------------
VERSION = '0.05'
TIMER = Timer(0)
BUFFERSIZE = 13
STATE_YPOS = 4

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

class InfoText():
  def __init__(self, display, ipAddrStr, mcanHash, csipStr, versionStr=VERSION):
    """
    """
    self.__display = display
    self.__version = 'Hash:{:4}  v{:>4}'.format(str(mcanHash), versionStr)
    #self.__hash = 'MCAN-Hash:  {}'.format(mcanHash)
    self.__ip = ipAddrStr
    self.__csip = csipStr
    self.__csConError = True 

  def set(self):
    """
    """
    self.__display.fill(0)
    self.__display.line(STATE_YPOS, 1)
    self.__display.line(STATE_YPOS+21,1)
    oled.text(' 2 4 6 8 0 2 4 6',0,STATE_YPOS+12)
    
    self.__display.text(self.__version, 0, 32)
    #self.__display.text(self.__hash, 0, 37)
    csipBytes = self.__csip.split('.')
    if len(csipBytes) == 4:
      csipLast2Bytes = '.'+ '.'.join(csipBytes[2:])
    else:
      csipLastByte = 'Err'
    if self.__csConError:
      csError = 'ERR'
    else:
      csError = 'con'
      
    self.__display.text('CS: {:3} {:>8}'.format(csError, csipLast2Bytes),0,42)
    self.__display.text('{:>16}'.format(self.__ip), 0, 55)
    
#   def setCsip(self, csip):
#     self.__csip = csip
#     if self.__csConError:
#       csError = 'ERR'
#     else:
#       csError = 'con'
#     self.__display.text('CS: {:3} {:>8}'.format(csError, csipLast2Bytes),0,42)
    
  def setCsConState(self, newState):
    """ set Central Station connection state:
          True:  connection established
          False: no connection
    """
    self.__csConState = newState

class CsConnection():
  def __init__(self, timeout=100):
    """
    """
    self.__csip = CSIP    
    self.__tcpPort = CSPORT
    print('CS-IP:',self.__csip,' Port:',self.__tcpPort)
    self.__csConnected = False
    try:
      self.__socket = usocket.socket( usocket.AF_INET, usocket.SOCK_STREAM )
      self.__socket.settimeout(timeout/1000)
      self.__socket.connect((self.__csip, self.__tcpPort))
      self.__csConnected = True
      #self.__socket.setblocking(False)      
    except Exception as e:
      # EHOSTUNREACH
      self.__csConnected = False
      print('ERROR:', e)

  def send(self, mcanMsg):
    """
    """
    if self.__csConnected:
      print('send ({}...) ...'.format(mcanMsg[:15]))
      self.__socket.send(mcanMsg)
    else:
      print('not send ({}...)!'.format(mcanMsg[:15]))

#-------------------------------------------------------------------------------
# main
#-------------------------------------------------------------------------------
if __name__ == '__main__':
  csConState = False
  mp = hc4067.Hc4067( pinEn=32, pinSig=33
                    , pinS0=12, pinS1=13, pinS2=14, pinS3=15
                    , ports=16
                    )
  currState = mp.signalValueByte
  recentState = currState
  trackstates = states.States()

  mcanHash = mcanhash.McanHash(macAddr)
  mcanCmd = mcancommand.McanCommand(int(mcanHash))
  mcanCmd.setCommand(0x22,response=True)

  TIMER.init(period=50, mode=Timer.PERIODIC, callback=handleInterrupt)
  csConnetion = CsConnection()
  
  infoText = InfoText(oled, wlan.ifconfig()[0], mcanHash, CSIP)
  infoText.set()

  trackstates.setStateBits(currState)
  oled.text(trackstates.shortStr,0, STATE_YPOS+4)
  oled.show()
  while True:
    trackstates.setStateBits(currState)
    if trackstates.isChanged:
      infoText.set()
      oled.text(trackstates.shortStr,0,STATE_YPOS+4)
      oled.show()
      for subId, state, recentState in trackstates.changedStates:
        contactNo = CONTACTBASE + subId
        mcanCmd.setTrackState(DEVICEID, contactNo, state, recentState)
        csConnetion.send(mcanCmd.frame)
        print(DEVICEID, contactNo, state, mcanCmd.frame)

    trackstates.setRecentToCurrent()
    time.sleep_ms(100)

#   while csConnetion is None:
#     try:
#       
#       oled.text('connection Ok.',8,1)
#       oled.show()
#     except:
#       oled.fill(0)
#       oled.text('ERROR',44,1)
#       oled.text('Central Station',0,16)
#       oled.text(CSIP,8,25)
#       oled.text('not found.',8,33)
#       oled.text(wlan.ifconfig()[0],0,55)
#       oled.show()
#       #conn = None