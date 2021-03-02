""" trackstate (boot.py) MicroPython script
    
    Author: Rainer Maier-Lohmann
    ---------------------------------------------------------------------------
    "THE BEER-WARE LICENSE" (Revision 42):
    <r.m-l@gmx.de> wrote this file.  As long as you retain this notice you
    can do whatever you want with this stuff. If we meet some day, and you 
    think this stuff is worth it, you can buy me a beer in return.
    ---------------------------------------------------------------------------
    (c) 2021
"""
# This file is executed on every boot (including wake-boot from deepsleep)
from machine import Pin, Timer, SoftI2C
from network import WLAN, STA_IF
import ubinascii
from oled import oledssd1306
import time

from wlancfg import SSID, PASSPHRASE

#-------------------------------------------------------------------------------
# constants
#-------------------------------------------------------------------------------
CFGFILENAME='config.ini'

NETIP='192.168.178.122'
NETDNS='192.168.178.1'
NETGW='192.168.178.1'
NETMASK='255.255.255.0'

CSIP='192.168.178.112'
CSPORT=15731

DEVICEID = 0
CONTACTBASE = 4 * 16 # (trackstateModulNumber - 1) * 16 contacts 

#SLCPIN=22
#SDAPIN=21
#OLEDWIDTH = 128
#OLEDHEIGHT = 64

#-------------------------------------------------------------------------------
# functions
#-------------------------------------------------------------------------------
def getConfig(cfgFilename):
  """
  """
  config = None
  try:
    with open(cfgFilename) as cfg:
      lines = cfg.readlines()
    lines = [x.replace('\n','').replace('\r','') for x in lines]
    config = dict()
    for line in lines:
      lineParts = line.split('=')
      if len(lineParts) > 1:
        config[lineParts[0].upper()] = lineParts[1]
  except Exception as e:
    print(e)
    print('{} not found.'.format(cfgFilename))
  return config

#-------------------------------------------------------------------------------
# setup
#-------------------------------------------------------------------------------
cfg = getConfig(CFGFILENAME)

i2c = SoftI2C(scl=Pin(int(cfg['SCLPIN'])), sda=Pin(int(cfg['SDAPIN'])))
oled = oledssd1306.Ssd1306I2c(int(cfg['OLEDWIDTH']), int(cfg['OLEDHIGHT']), i2c)

macAddr = int.from_bytes(WLAN().config('mac'), 'little')
macAddrStr = ubinascii.hexlify(WLAN().config('mac'),':').decode()

oled.fill(0)
oled.text('WLAN connect ...',0,1)
oled.show()
wlan = WLAN(STA_IF)
if cfg['IP'] != '':
 wlan.ifconfig((cfg['IP'], cfg['MASK'], cfg['GW'], cfg['DNS']))
wlan.active(True)
wlan.connect(SSID, PASSPHRASE)
while wlan.isconnected() == False:
  pass
oled.fill(0)
oled.text('WLAN connect OK',0,1)
oled.show()
