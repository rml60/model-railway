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
from machine import Pin, Timer, I2C
from network import WLAN, STA_IF
import time
import ubinascii

try:
  import usocket as socket
except:
  import socket

from oled import oledssd1306
from mcan import mcanhash, mcancommand, states

#-------------------------------------------------------------------------------
# constants
#-------------------------------------------------------------------------------
VERSION = '0.03'
TIMER = Timer(0)
BUFFERSIZE = 13
OLEDWIDTH = 128
OLEDHEIGHT = 64

DEVICEID = 0
CONTACTBASE = 4 * 16 # (trackstateModulNumber - 1) * 16 contacts 

#-------------------------------------------------------------------------------
# setup
#-------------------------------------------------------------------------------
out0 = Pin(12, Pin.OUT)
out1 = Pin(13, Pin.OUT)
in0 = Pin(32, Pin.IN, Pin.PULL_UP)
in1 = Pin(33, Pin.IN, Pin.PULL_UP)

#-------------------------------------------------------------------------------
# classes and functions
#-------------------------------------------------------------------------------
def handleInterrupt(TIMER):
  """
  """
  global currState
  currState = 0
  # inx.value ist entweder 0 oder 1
  currState = currState | in0.value()*2**0
  currState = currState | in1.value()*2**1

def getConfig(cfgFilename):
  """
  """
  config = None
  config = dict()
  try:
    with open(cfgFilename) as cfg:
      lines = cfg.readlines()
    lines = [x.replace('\n','').replace('\r','') for x in lines]
    for line in lines:
      lineParts = line.split('=')
      if len(lineParts) > 1:
        config[lineParts[0]] = lineParts[1]
  except Exception as e:
    print(e)
    print('{} not found.'.format(cfgFilename))
  return config

def getMac():
  """
  """
  return int.from_bytes(WLAN().config('mac'), 'little')

def getMacStr():
  """
  """
  return ubinascii.hexlify(WLAN().config('mac'),':').decode()

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
  def __init__(self, cfg):
    """
        udp deprecated
        udpTxPort: send port to Central Station receive Port
        udpRxPort: receive port 
    """
    self.__station = None
    self.__cfg = cfg
    self.__ip = cfg['ip']
    self.__mask = cfg['mask']
    self.__csip = cfg['csip']

    self.__gw = cfg['gw']
    self.__dns = cfg['dns']
    self.__ssid = cfg['ssid'].strip()
    self.__pp = cfg['passphrase'].strip()
    self.__tcpPort = int(cfg['tcpport'])
    print('CS-IP:',self.__csip,' Port:',self.__tcpPort)

    self.__connectWlan()
    while self.__station.isconnected() == False:
      pass
    self.__socket = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    self.__socket.connect((self.__csip, self.__tcpPort))
    #self.__socket.setblocking(False)

  @property
  def isconnected(self):
    """
    """
    if self.__station is None:
      return False
    return self.__station.isconnected()

  @property
  def ifconfig(self):
    """
    """
    return self.__station.ifconfig

  def send(self, mcanMsg):
    """
    """
    self.__socket.send(mcanMsg)
    
  def __connectWlan(self):
    """
    """
    self.__station = WLAN(STA_IF)
    self.__station.ifconfig((self.__ip, self.__mask, self.__gw, self.__dns))
    self.__station.active(True)
    self.__station.connect(self.__ssid, self.__pp)

#-------------------------------------------------------------------------------
# main
#-------------------------------------------------------------------------------
if __name__ == '__main__':
  currState = 0
  recentState = currState
  trackstates = states.States()

  cfg = getConfig('config.ini')

  i2c = I2C(-1, scl=Pin(int(cfg['sclpin'])), sda=Pin(int(cfg['sdapin'])))
  oled = oledssd1306.Ssd1306I2c(OLEDWIDTH, OLEDHEIGHT, i2c)

  mac = getMac()
  mcanHash = mcanhash.McanHash(mac)
  print('MAC-Adresse: {} - mcanHash: {}'.format(getMacStr(), mcanHash))
  mcanCmd = mcancommand.McanCommand(int(mcanHash))
  mcanCmd.setCommand(0x22,response=True)

  if cfg is not None:
    TIMER.init(period=50, mode=Timer.PERIODIC, callback=handleInterrupt)
    conn = None
    while conn is None:
      try:
        oled.fill(0)        
        oled.text('connect ...',24,1)
        oled.show()
        conn = CanConnection(cfg)
        oled.text('connection Ok.',8,1)
        oled.show()
      except:
        oled.fill(0)
        oled.text('ERROR',32,1)
        oled.text('CS not found.',8,20)
        oled.show()
        print('ERROR: Central Station not found')
        conn = None

    if conn is not None:
      infoText = OledInfoText(oled, conn.ifconfig()[0], mcanHash)
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
 
          for subId, state, recentState in trackstates.changedStates:
            contactNo = CONTACTBASE + subId
            mcanCmd.setTrackState(DEVICEID, contactNo, state, recentState)
            conn.send(mcanCmd.frame)
            print(DEVICEID, contactNo, state, mcanCmd.frame)
 
        trackstates.setRecentToCurrent()
        
        out0.value(currState & 1)
        out1.value(currState & 2)
        time.sleep_ms(100)
