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
#from machine import Timer
from usocket import socket, AF_INET, SOCK_STREAM
from utime import sleep_us
from uping import ping

from hc4067 import Hc4067
from mcan import mcanhash, mcancommand, states

#-------------------------------------------------------------------------------
# constants
#-------------------------------------------------------------------------------
VERSION = '0.06'
TIMER = Timer(0)
BUFFERSIZE = 13
STATE_YPOS = 4

#-------------------------------------------------------------------------------
# classes and functions
#-------------------------------------------------------------------------------
# def handleInterrupt(TIMER):
#   """
#   """
#   global currState
#   currState = 0
#   # inx.value ist entweder 0 oder 1
#   #currState = currState | in0.value()*2**0
#   #currState = currState | in1.value()*2**1
#   currState = mp.valueByte

class InfoText():
  def __init__(self, display, ipAddrStr, mcanHash, csipStr, versionStr=VERSION):
    """
    """
    self.__display = display
    self.__version = 'Hash:{:4}  v{:>4}'.format(str(mcanHash), versionStr)
    #self.__hash = 'MCAN-Hash:  {}'.format(mcanHash)
    self.__ip = ipAddrStr
    self.__csip = csipStr
    self.__csConState = False 

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
    if self.__csConState:
      csError = 'OK'
    else:
      csError = 'ERR'
      
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
  def __init__(self, csIpAddr, csIpPort, timeoutSec=1):
    """
    """
    self.__csip = csIpAddr    
    self.__tcpPort = csIpPort
    self.__timeoutSec = timeoutSec
    print('CS-IP:',self.__csip,' Port:',self.__tcpPort)
    self.__connected = False
    #try: 
      #self.__socket.setblocking(False)      
    #except Exception as e:
      # EHOSTUNREACH
    #  self.__csConnected = False
    #  print('ERROR:', e)

  @property
  def isConnected(self):
    print('CS connected: {}'.format(self.__connected))
    return self.__connected

  def connect(self):
    self.__socket = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    self.__socket.setblocking(False)
    self.__socket.settimeout(self.__timeoutSec)
    try:
      self.__socket.connect((self.__csip, self.__tcpPort))
      self.__connected = True
    except Exception as e:
      print('Connection error')
      self.__connected = False
      
    #try:
    #    urllib.request.urlopen(self.__csip, timeout=1)
    #    print('CS found')
    #    self.__socket.connect((self.__csip, self.__tcpPort))
    #    self.__connected = True
    #except urllib.request.URLError:
    #    print('CS not found')
    #    self.__connected = False
    
  def close(self):
    self.__socket.close()
    self.__connected = False
    
  def send(self, mcanMsg):
    """
    """
    if self.__connected:
      print('send ({}...) ...'.format(mcanMsg[:15]))
      self.__socket.send(mcanMsg)
    else:
      print('not send ({}...)!'.format(mcanMsg[:15]))

def pingOk(host, count=1):
    response = ping(host, count=count, quiet=True)
    return response[1] == count
#-------------------------------------------------------------------------------
# main
#-------------------------------------------------------------------------------
if __name__ == '__main__':
  csConState = False
  # en:  4067-pin15 - esp32-d35-pin20  - not used 
  # sig: 4067-pin1  - esp32-d32-pin21
  # s0:  4067-pin10 - esp32-d12-pin27
  # s1:  4067-pin11 - esp32-d13-pin28
  # s2:  4067-pin14 - esp32-d14-pin26
  # s3:  4067-pin13 - esp32-d15-pin3
  mp = Hc4067( pinSig=32, pinS0=12, pinS1=13, pinS2=14, pinS3=15 )
  currState = mp.valueByte
  recentState = currState
  trackstates = states.States()

  mcanHash = mcanhash.McanHash(macAddr)
  mcanCmd = mcancommand.McanCommand(int(mcanHash))
  mcanCmd.setCommand(0x22,response=True)

  #TIMER.init(period=20, mode=Timer.PERIODIC, callback=handleInterrupt)
  currState = mp.valueByte
  csConnection = CsConnection(CSIP, CSPORT)
  
  infoText = InfoText(oled, wlan.ifconfig()[0], mcanHash, CSIP)
  infoText.set()
  csConStateOk = pingOk(CSIP)
  infoText.setCsConState(csConStateOk)
  
  trackstates.setStateBits(currState)
  
  oled.text(trackstates.shortStr,0, STATE_YPOS+4)
  oled.show()
  while True:
    currState = mp.valueByte
    trackstates.setStateBits(currState)
    print(currState)
    if trackstates.isChanged:
      infoText.set()
      csConStateOk = pingOk(CSIP)
      infoText.setCsConState(csConStateOk)
      oled.text(trackstates.shortStr, 0, STATE_YPOS+4)
      oled.show()
      if csConStateOk:
        #csConnection.connect()
        #result = csConnection.isConnected
        pass
      for subId, state, recentState in trackstates.changedStates:
        contactNo = CONTACTBASE + subId
        mcanCmd.setTrackState(DEVICEID, contactNo, state, recentState)
        if csConStateOk:
         #csConnection.send(mcanCmd.frame)
         print(DEVICEID, contactNo, state, mcanCmd.frame)
      if csConStateOk:
        #csConnection.close()
        pass

    trackstates.setRecentToCurrent()
    #time.sleep_ms(100)
    #print('new tick')

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