""" trackstate (main.py) MicroPython script
    
    Sends trackstates (16 contacts) as can-frame bytearray via WLAN (Protocol:
    Maerklin can-bus).
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

from hardware import hc4067
from mcan import mcanhash, mcancommand, states

#-------------------------------------------------------------------------------
# constants
#-------------------------------------------------------------------------------
VERSION = '0.07'

#-------------------------------------------------------------------------------
# classes and functions
#-------------------------------------------------------------------------------
class InfoText():
  yposRow0 =  0
  yposRow1 =  9
  yposRow2 = 20
  yposRow3 = 34
  yposRow4 = 43
  yposRow5 = 56

  def __init__( self, display, ipAddrStr, mcanHash, csipStr
              , contactAddr=1, versionStr=VERSION):
    """
    """
    self.__state = '0000000000000000'
    self.__csError = '   '
    self.__display = display
    #self.__version = 'Hash:{:4}  v{:>4}'.format(str(mcanHash), versionStr)
    self.__version = 'Trackstate v{:>4}'.format(versionStr)
    self.__hash = 'MCAN-Hash:  {:4}'.format(str(mcanHash))
    self.__ip = ipAddrStr
    self.__ipStr = '{:>16}'.format(self.__ip)
    self.__csip = csipStr
    csipBytes = self.__csip.split('.')
    if len(csipBytes) == 4:
      self.__csipLast2Bytes = '.'+ '.'.join(csipBytes[2:])
    else:
      self.__csipLast2Bytes = 'Err CSIP'
    self.__contactsStr = 'cont.: {:04}-{:04}'.format(contactAddr, contactAddr+15)
    self.__csConState = False

  def show(self):
    self.__display.show()
    
  def set(self):
    """ 
    """
    self.__display.fill(0)
    self.__display.text(self.__contactsStr , 0, self.yposRow1)
    self.__display.text(self.__ipStr , 0, self.yposRow2)

    self.__display.text('CS:', 0, self.yposRow3)
    self.__display.text(self.__csError, 32, self.yposRow3)
    self.__display.text(self.__csipLast2Bytes, 63, self.yposRow3)
    self.__display.text(self.__hash, 0, self.yposRow4)
    self.__display.text(self.__version, 0, self.yposRow5)
   
  def setTrackstate(self, state):
    self.__display.text(self.__state, 0, self.yposRow0, color=0)
    self.__state = state
    self.__display.text(state, 0, self.yposRow0)
    
   
  def setCsConState(self, state):
    """ set Central Station connection state:
            - True:  connection established
            - False: no connection
    """
    self.__csConState = state
    self.__display.text(self.__csError, 32, self.yposRow3, color=0)
    if self.__csConState:
      self.__csError = '  '
    else:
      self.__csError = 'ERR'
    self.__display.text(self.__csError, 32, self.yposRow3)

class CsConnection():
  def __init__(self, csIpAddr, csIpPort, timeoutSec=1):
    """
    """
    self.__csip = csIpAddr    
    self.__tcpPort = csIpPort
    self.__timeoutSec = timeoutSec
    #print('CS-IP:',self.__csip,' Port:',self.__tcpPort)
    self.__connected = False

  # @property
  # def isConnected(self):
  #   print('CS connected: {}'.format(self.__connected))
  #   return self.__connected

  def connect(self):
    self.__socket = socket( AF_INET, SOCK_STREAM )
    self.__socket.setblocking(False)
    self.__socket.settimeout(self.__timeoutSec)
    try:
      self.__socket.connect((self.__csip, self.__tcpPort))
      self.__connected = True
    except Exception as e:
      print('Connection error')
      self.__connected = False
    
  def close(self):
    self.__socket.close()
    self.__connected = False
    
  def send(self, mcanMsg):
    """
    """
    if self.__connected:
      # print('send ({}...) ...'.format(mcanMsg[:15]))
      self.__socket.send(mcanMsg)
    else:
      # print('not send ({}...)!'.format(mcanMsg[:15]))
      pass

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
  mp = hc4067.Hc4067( pinSig=32, pinS0=12, pinS1=13, pinS2=14, pinS3=15 )
  currState = mp.value
  recentState = currState
  trackstates = states.States()

  mcanHash = mcanhash.McanHash(macAddr)
  mcanCmd = mcancommand.McanCommand(int(mcanHash))
  mcanCmd.setCommand(0x22,response=True)

  currState = mp.value
  csConnection = CsConnection(CSIP, CSPORT)
  
  infoText = InfoText(oled, wlan.ifconfig()[0], mcanHash, CSIP, contactAddr=CONTACTBASE)
  infoText.set()
  csConStateOk = pingOk(CSIP)
  infoText.setCsConState(csConStateOk)
  
  trackstates.setStateBits(currState)
  
  infoText.setTrackstate(trackstates.shortStr)
  infoText.show()
  while True:
    currState = mp.value
    csConStateOk = pingOk(CSIP)
    infoText.setCsConState(csConStateOk) # showed only if trackstate changes
    trackstates.setStateBits(currState)
    #print(currState)
    if trackstates.isChanged:
      infoText.setTrackstate(trackstates.shortStr)
      infoText.show()
      if csConStateOk:
        csConnection.connect()
        #result = csConnection.isConnected
        pass
      for subId, state, recentState in trackstates.changedStates:
        contactNo = CONTACTBASE + subId
        mcanCmd.setTrackState(DEVICEID, contactNo, state, recentState)
        if csConStateOk:
         csConnection.send(mcanCmd.frame)
         print(DEVICEID, contactNo, state, mcanCmd.frame)
      if csConStateOk:
        csConnection.close()
        pass

    trackstates.setRecentToCurrent()
    #time.sleep_us(100000)
