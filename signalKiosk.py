
#!/usr/bin/env python
#
######################################################################

# SIGNALKIOSK-README:

# signalKiosk.py will query a signalK-Server for telemetry: wind, depth, speed, etc.
# and display those telemetry (preceeded by a labelling mnemonic every-10-displays/sec.
# Example: HDG,pause,150.6,pause,150.6,pause...7sec elapse...150.6,pause, HDG,pause,150.6,pause......)
# on a 4-character,seven-segment-display; with 000.0 decimal/precision

# signalKiosk.py will monitor a tcp-socket (as a command-server), and queue up the
# requested telemetry signalled (see telem_list variable in code)  Additionally, this command-server
# port will be used for future configuaration (in-band-signalling) enhancements i.e., to define 
# IPs, ports, delays/time, etc.  e.g, SKServer=10.10.10.1, SKPort=22222, TelemLabelOccurSec=10,
# TelemLabelOccurSec=0 means no labels, CountDownTimerMode, etc.

#signalKiosk.py will monitor a push-button-switch that will, in-sequence, advance the
#selection of telemetry defined in the tele_list variable/imported-file

#######################################################################

from __future__ import print_function
import os, sys
import time, math
import datetime
import socket
from multiprocessing import Process, Pipe
import psutil
#import keyboard #must run as root ???

import RPi.GPIO as GPIO
from Adafruit_LED_Backpack import SevenSegment
from signalk import kjson

global SIGKHOST
global SIGKPORT
global SIGNALKHOST
global SIGNALKPORT
global BRIGHTNESS
global DISPLAYLABEL
global LABELINTERVAL
global DISPLAYREFRESH

global DISPLAYCMD

BRIGHTNESS	= 1

DISPLAYCMD	= 'HDG'

DISPLAYLABEL	= 1
LABELINTERVAL	= 30 #15000 milliseconds = 15 seconds

CMDServer	= '' #Listen to network SignalKioskClients
#CMDServer	= 'localhost'
CMDPort		= 10000

#SIGKHOST	= '10.0.0.103'
#SIGKHOST	= 'localhost'
#SIGKPORT	= 21311
#SIGKPORT	= 21311

#######################################################################
#sk_list = [('HDG','ap.heading'),('CMD','ap.heading_command'),('HEEL','imu.roll')]
#######################################################################

telem_list = ['BNAV','HDG','CMD','HEEL','TIME','TEST','ALL']

display = SevenSegment.SevenSegment()

segment = SevenSegment.SevenSegment(address=0x70, busnum=1)

segment.begin() # Initialize the display

#print('\nSetting Display Brightness')
display.set_brightness(BRIGHTNESS)   #ht16k33

#######################################################################

os.nice(15) #-20 to 20

#######################################################################

def ReadTelemList ():
	print('\nAttempting to READ telem_list file!\n')
	
	global skStrings
	skStrings = []

	for t in open('telemSKstring.txt').read().split():
		a, b = t.strip('').split(',')
		skStrings.append((str(a), str(b)))
    
	#print('skStrings Tuple-List follows: \n')
	#print(skStrings)
	if skStrings:
		print('Telemetry_List imported successfully!\n')
	return

#######################################################################

def ResolveSKstrng (param):
	# go thru list for match
	for j in skStrings:
		if j[0] == param:
			#FOUND = True
			sk = j[1]
			break
	return sk

#######################################################################

def SKCfgRead ():
	
	global SIGNALKHOST
	global SIGNALKPORT
	global BRIGHTNESS
	global DISPLAYLABEL
	global LABELINTERVAL
	global DEFDISPLAYCMD
	global DISPLAYREFRESH
	
	print('\nAttempting to READ KioskConf file!\n')
	global skcfg
	skcfg = []
	filename = 'SKConfig.txt'
	with open(filename) as f:
		skcfg = f.read().splitlines()
	print(skcfg)
	if skcfg:
		SIGNALKHOST = skcfg[2]
		SIGNALKPORT = skcfg[3]
		BRIGHTNESS = int(skcfg[4])
		DISPLAYLABEL = int(skcfg[5])
		LABELINTERVAL = int(skcfg[6])
		DEFDISPLAYCMD = skcfg[7]
		DISPLAYREFRESH = float(skcfg[8])
		print('\nSK configuration imported successfully!')
	return
	
#######################################################################
#FOCUS
def SKCfgWrite (cmdvalue,ln):

	#print('\nAttempting to WRITE command to KioskConf file!\n')
	fname = 'SKConfig.txt'
	with open(fname, 'r') as file:
		lines = file.readlines()
		#an array of lines
	if len(lines) > int(ln):
			lines[ln] = ''+str(cmdvalue)+'\n'
			#print('\nLine to be written: '+lines[ln]+':index is '+str(ln)+'')
	with open(fname, 'w') as file:
		file.writelines( lines )
		
	file.close()
		
	return

#######################################################################

def CommandFilter (data):
	
	global SIGNALKHOST
	global SIGNALKPORT
	global BRIGHTNESS
	global DISPLAYLABEL
	global LABELINTERVAL
	global DEFDISPLAYCMD

	if "::" in data: #string contains '::' "delimiter"
		#cmdroot		= data less all before delimiter '::'
		#cmdpayload	= data less all after delimiter '::'
		#CMDROOT = ''
		#CMDPAYLOAD = ''
		CMDROOT, CMDPAYLOAD = data.strip('').split('::')
		
		print(CMDROOT)
		print(CMDPAYLOAD)
		
		if CMDROOT == 'SIGNALKHOST':
			print('\nIts a Command: set the SIGNALKHOST_variable to ' + CMDPAYLOAD + '')
			SIGNALKHOST = CMDPAYLOAD
			SKCfgWrite(SIGNALKHOST,2)  #line3
			return (1)
		elif CMDROOT == 'SIGNALKPORT':
			print('\nSetting the SIGNALKPORT_variable to ' + CMDPAYLOAD + '')
			SIGNALKPORT = CMDPAYLOAD
			SKCfgWrite(SIGNALKPORT,3)  #line4
			return (1)
		elif CMDROOT == 'BRIGHTNESS':
			print('\nSetting the BRIGHTNESS_variable to ' + CMDPAYLOAD + '')
			BRIGHTNESS = int(CMDPAYLOAD)
			SKCfgWrite(BRIGHTNESS,4)  #true-line 5
			return (1)
		elif CMDROOT == 'DISPLAYLABEL':
			print('\nSetting the DISPLAYLABEL_variable to ' + CMDPAYLOAD + '')
			DISPLAYLABEL = int(CMDPAYLOAD)
			SKCfgWrite(DISPLAYLABEL,5)  #line6
			return (1)
		elif CMDROOT == 'LABELINTERVAL':
			print('\nSetting the LABELINTERVAL_variable to ' + CMDPAYLOAD + '')
			LABELINTERVAL = int(CMDPAYLOAD)
			SKCfgWrite(LABELINTERVAL,6)  #line7
			return (1)
			
		elif CMDROOT == 'DEFDISPLAYCMD':
			print('\nSetting the DEFDISPLAYCMD_variable to ' + CMDPAYLOAD + '')
			DEFDISPLAYCMD = CMDPAYLOAD
			SKCfgWrite(DEFDISPLAYCMD,7)  #line7
			return (1)
			
		elif CMDROOT == 'DISPLAYREFRESH':
			print('\nSetting the DISPLAYREFRESH_variable to ' + CMDPAYLOAD + '')
			DISPLAYREFRESH = CMDPAYLOAD
			SKCfgWrite(DISPLAYREFRESH,8)  #line8
			return (1)
			
		elif CMDROOT == 'PUSH':
			Button_Callback(666)
			return (1)	
			
		elif CMDROOT == 'SHUTDOWN':
			print('\nSimulation::SHUTDOWN Initiated: Preparing for ShutDown!\n')
			#sys('sudo halt')
			#os.system("shutdown /s /t 1")
			#os.system("shutdown now -h")
			#os.system('shutdown -P now')
			return (1)		
			
	return (0) #if not a config update
	
#######################################################################
	
def UpdateDisplay(cmd,labl):

	segment.clear()
	#print('Into UpdateDisplayProc')
	
	if cmd == 'TIME':
		#DispTIMElabel() #label
		#if labl:
			#DispTIMElabel()
		DispTime()
		return
		
	if cmd == 'TEST':
		DispTestSegments()
		return
		
	if cmd == 'HDG':
		DispHDNG(labl)
		#DispHDNG(cmd,labl)
		return
		
	if cmd == 'CMD':
		DispCMD(labl)
		return
		
	if cmd == 'HEEL':
		DispHeeL(labl)
		return
		
	if cmd == 'DPTH':
		DispDepth(1)
		return
		
	if cmd == 'SOG':
		DispSOG(1)
		return
		
	if cmd == 'NONE':  #display no data available
		DispNDat
		return
		
	if cmd == 'BNAV':
		ClearSKVal(skval)
		DispHDNG(1) #DispHDNG(labl)
		time.sleep(0.25)
		DispCMD(1)
		time.sleep(0.25)
		DispHeeL(1)
		#DispDepth(1)
		#DispSOG()		#NA at this time
		#if labl:
		DispTIMElabel()
		DispTime()
		return
		
	if cmd == 'ALL':
		print('Displaying ALL Telemetry including PROMPTS:')
		DispTestSegments()
		DispSTART()
		DispSTOP()
		DispAUTO()
		DispPilot()
		DispON()
		DispOFF()
		DispTRUE()
		DispMAG()
		DispAIS()
		DispAlert()
		DispFALT ()
		DispGPS()
		DispHALT()
		DispHELP()
		DispSOS()
		DispSPD()
		DispTEMP()
		DispTWD ()
		DispTWS ()
		DispNDat()
		DispTIMElabel()
		DispTime()
		DispNCON()
		DispHEllO()
		DispFIN()
		DispHDNG(1)
		DispCMD(1)
		DispHeeL(1)
		#DispDepth(1)	#NA at this time
		#DispSOG(1)		#NA at this time
		DispPUSH()
		return
		
	return

#######################################################################

def DisplayTelem (telem):
	#print(telem)
	telem = round(telem,1)
	print(round(telem,1))
	segment.clear()
	segment.set_fixed_decimal(True)
	segment.write_display()
	segment.print_float(telem, decimal_digits=1, justify_right=True)
	segment.write_display()
	time.sleep(1) #for 1 second
	return
	
#######################################################################
	
def DispHDNG (lstat):
	#DispHDNG(cmd,labl)
	segment.clear()
	if lstat == 1:
		#HdnG - Heading
		segment.set_digit_raw(0,0xF6)
		segment.set_digit_raw(1,0x5E)
		segment.set_digit_raw(2,0xD4) #capital G=bd or x6F
		segment.set_digit_raw(3,0x6F)
		segment.write_display()
		time.sleep(0.25)
	#rqst = 'HDG'
	#DisplayTelem (GetHeading(ResolveSKstrng(rqst)))
	DisplayTelem (GetHeading ())
	#time.sleep()
	return

#######################################################################
	
def DispCMD (lstat):
	segment.clear()
	#CSE - Course
	if lstat == 1:
		
		segment.set_digit_raw(0,0x39)
		#segment.set_digit_raw(1,0x33)#37,D4
		#segment.set_digit_raw(2,0x27)#37,D4
		segment.set_digit_raw(1,0xD4)#37,D4
		segment.set_digit_raw(2,0xD4)#37,D4
		segment.set_digit_raw(3,0x5E)#5E
		
		segment.write_display()
		time.sleep(0.5)
	
	#DisplayTelem (ResolveSKstrng('CMD'))
	DisplayTelem (GetCommand ())
	return

#######################################################################

def DispCSE (lstat):
	segment.clear()
	#CSE - Course
	if lstat == 1:
		segment.set_digit_raw(0,0x39)
		segment.set_digit_raw(1,0xED)
		segment.set_digit_raw(2,0x79)
		segment.set_digit_raw(3,0x00)
		segment.write_display()
		time.sleep(0.5)

	DisplayTelem (GetCommand ())
	return

#######################################################################

def DispHeeL (lstat):
	segment.clear()
	#HeeL - Heel
	if lstat == 1:
		segment.set_digit_raw(0,0xF6)
		segment.set_digit_raw(1,0xf9)	#7b=large-small-e
		segment.set_digit_raw(2,0xf9)	#7b=large-small-e
		segment.set_digit_raw(3,0x38)
		segment.write_display()
		time.sleep(0.5)
	
	DisplayTelem (GetRoll())
	return

#######################################################################

def DispDepth (lstat):
	segment.clear()
	#dPtH - Depth
	if lstat == 1:
		segment.set_digit_raw(0,0x5E)
		segment.set_digit_raw(1,0xF3)
		segment.set_digit_raw(2,0xF8)
		segment.set_digit_raw(3,0xF6)
		segment.write_display()
		time.sleep(0.5)
		
	DisplayTelem (GetDepth())
	return

#######################################################################

def DispSOG (lstat):
	segment.clear()
	#SOG - Speed Over Ground
	if lstat == 1:
		segment.set_digit_raw(0,0x6d)
		segment.set_digit_raw(1,0xbf)
		segment.set_digit_raw(2,0xBD)
		segment.set_digit_raw(3,0x80)
		segment.write_display()
		time.sleep(0.5)
	
	dispVal = GetSOG()
	segment.clear()
	segment.set_fixed_decimal(True)
	segment.write_display()
	segment.print_float(abs(dispVal), decimal_digits=3, justify_right=True)
	segment.write_display()
	time.sleep(0.5)
	return
#######################################################################

def DispNDat ():
	segment.clear()
	#NonE - No Data Available
	segment.set_digit_raw(0,0x37)
	segment.set_digit_raw(1,0xbf)
	segment.set_digit_raw(2,0x37)
	segment.set_digit_raw(3,0x7b)
	segment.write_display()
	time.sleep(2)
	return

#######################################################################

def DispNCON ():
	segment.clear()
	#nCON - No SK Server Connection Established
	segment.set_digit_raw(0,0xd4)
	segment.set_digit_raw(1,0x39)
	segment.set_digit_raw(2,0xBF)
	segment.set_digit_raw(3,0x37)
	segment.write_display()
	time.sleep(2)
	return

#######################################################################

def DispON ():
	segment.clear()
	#ON - 
	segment.set_digit_raw(0,0xBF)
	segment.set_digit_raw(1,0xD4) #37-upperCase
	segment.set_digit_raw(2,0x00)
	segment.set_digit_raw(3,0x00)
	segment.write_display()
	time.sleep(2)
	return

#######################################################################

def DispOFF ():
	segment.clear()
	#OFF
	segment.set_digit_raw(0,0xBF)
	segment.set_digit_raw(1,0xF1)
	segment.set_digit_raw(2,0xF1)
	segment.set_digit_raw(3,0x00)
	segment.write_display()
	time.sleep(2)
	return


#######################################################################
	
def DispAlert ():
	#ALRt - Alert
	segment.clear()
	segment.set_digit_raw(0,0xF7)
	segment.set_digit_raw(1,0x38)
	# was segment.set_digit_raw(2,0xF7)
	segment.set_digit_raw(2,0xD0)	
	segment.set_digit_raw(3,0xF8)
	segment.write_display()
	time.sleep(3)
	return

#######################################################################

def DispSTART ():
	#Strt - Alert
	segment.clear()
	segment.set_digit_raw(0,0x6D)
	segment.set_digit_raw(1,0xF8)
	segment.set_digit_raw(2,0xD0)	
	segment.set_digit_raw(3,0xF8)
	segment.write_display()
	time.sleep(3)
	return

#######################################################################

def DispSTOP ():
	#StoP - Alert
	segment.clear()
	segment.set_digit_raw(0,0x6D)
	segment.set_digit_raw(1,0xF8)
	segment.set_digit_raw(2,0xDC)	
	segment.set_digit_raw(3,0xF3)
	segment.write_display()
	time.sleep(3)
	return

#######################################################################

def DispAIS ():
	#AIS - Alert
	segment.clear()
	segment.set_digit_raw(0,0xF7)
	segment.set_digit_raw(1,0x86)
	segment.set_digit_raw(2,0x6D)	
	segment.set_digit_raw(3,0x00)
	segment.write_display()
	time.sleep(3)
	return
	
#######################################################################

def DispAUTO ():
	#AUTO - Autopilot
	segment.clear()
	segment.set_digit_raw(0,0xF7)
	segment.set_digit_raw(1,0x9C)
	segment.set_digit_raw(2,0xF8)
	segment.set_digit_raw(3,0xDC)
	segment.write_display()
	time.sleep(1.5)
	return

#######################################################################

def DispSOS ():
	#SOS - Alert
	segment.clear()
	segment.set_digit_raw(0,0x6D)
	segment.set_digit_raw(1,0xBF)
	segment.set_digit_raw(2,0x6D)	
	segment.set_digit_raw(3,0x00)
	segment.write_display()
	time.sleep(3)
	return

#######################################################################

def DispSPD ():
	#SPD - Speed
	segment.clear()
	segment.set_digit_raw(0,0x6D)
	segment.set_digit_raw(1,0xF3)
	segment.set_digit_raw(2,0x5E)#BF	
	segment.set_digit_raw(3,0x00)
	segment.write_display()
	time.sleep(3)
	return

#######################################################################

def DispTEMP ():
	#TnnP - Temperature
	segment.clear()
	segment.set_digit_raw(0,0xF8)
	segment.set_digit_raw(1,0xd4)
	segment.set_digit_raw(2,0xd4)
	segment.set_digit_raw(3,0xF3)
	segment.write_display()
	time.sleep(2)
	return

#######################################################################
	
def DispTIMElabel ():
	#tine - Time
	segment.clear()
		
	segment.set_digit_raw(0,0xF8)
	segment.set_digit_raw(1,0x06)#86,98
	segment.set_digit_raw(2,0x37)#37,d4
	segment.set_digit_raw(3,0x7b)# was 7b,f9
	
	segment.write_display()
	time.sleep(1)
	return

#######################################################################

def DispHEllO ():
	segment.clear()
	segment.set_digit_raw(0,0xF6)
	segment.set_digit_raw(1,0xF9)
	segment.set_digit_raw(2,0x36)
	segment.set_digit_raw(3,0xBF)
	segment.write_display()
	time.sleep(2)
	return

#######################################################################

def DispFALT ():
	segment.clear()
	segment.set_digit_raw(0,0xF1)
	segment.set_digit_raw(1,0xF7)
	segment.set_digit_raw(2,0x38)
	segment.set_digit_raw(3,0xF8)
	segment.write_display()
	time.sleep(2)
	return

#######################################################################

def DispMAG ():
	segment.clear()
	segment.set_digit_raw(0,0xD4)#37,D4,33
	segment.set_digit_raw(1,0xD4)#37,D4,27
	segment.set_digit_raw(2,0xF7)
	segment.set_digit_raw(3,0xBD)#BD,6F
	
	segment.write_display()
	time.sleep(2)
	return

#######################################################################

def DispTRUE ():
	segment.clear()
	segment.set_digit_raw(0,0xF8)
	segment.set_digit_raw(1,0xD0)
	segment.set_digit_raw(2,0x9C)
	segment.set_digit_raw(3,0xF9)
	segment.write_display()
	time.sleep(2)
	return


#######################################################################

def DispHALT ():
	segment.clear()
	segment.set_digit_raw(0,0xF6)
	segment.set_digit_raw(1,0xF7)
	segment.set_digit_raw(2,0x38)
	segment.set_digit_raw(3,0xF8)
	segment.write_display()
	time.sleep(2)
	return
#######################################################################

def DispHELP ():
	segment.clear()
	segment.set_digit_raw(0,0xF6)
	segment.set_digit_raw(1,0xF9)
	segment.set_digit_raw(2,0x38)
	segment.set_digit_raw(3,0xF3)
	segment.write_display()
	time.sleep(2)
	return
#######################################################################

def DispFIN ():
	segment.clear()
	segment.set_digit_raw(0,0xF1)
	segment.set_digit_raw(1,0x86)
	segment.set_digit_raw(2,0x37)
	segment.set_digit_raw(3,0x80)
	segment.write_display()
	time.sleep(2)
	return
	
#######################################################################

def DispGPS ():
	segment.clear()
	segment.set_digit_raw(0,0xBD)#6F
	segment.set_digit_raw(1,0xF3)
	segment.set_digit_raw(2,0x6D)
	segment.set_digit_raw(3,0x80)
	segment.write_display()
	time.sleep(2)
	return
	
#######################################################################

def DispPilot ():
	segment.clear()
	#segment.set_digit_raw(0,0xF3)
	#segment.set_digit_raw(1,0x30)
	#segment.set_digit_raw(2,0x38)
	#segment.set_digit_raw(3,0xf8)
	
	segment.set_digit_raw(0,0xF3)
	segment.set_digit_raw(1,0x16)
	segment.set_digit_raw(2,0xDC)
	segment.set_digit_raw(3,0xf8)
	
	segment.write_display()
	time.sleep(3)
	#segment.clear()
	#segment.write_display()
	return

#######################################################################


def DispPUSH ():
	segment.clear()
	segment.set_digit_raw(0,0xED)
	segment.set_digit_raw(1,0xB8)
	segment.set_digit_raw(2,0x58)
	segment.set_digit_raw(3,0xF8)
	segment.write_display()
	time.sleep(.5)
	segment.clear()
	segment.write_display()
	return

#######################################################################
	
def DispTWS ():
	#tuuS - TWS
	segment.clear()
	segment.set_digit_raw(0,0xF8)
	segment.set_digit_raw(1,0x9C)
	segment.set_digit_raw(2,0x9C)
	segment.set_digit_raw(3,0x6D)
	segment.write_display()
	time.sleep(2)
	return
	
#######################################################################
	
def DispTWD ():
	#tuuD - TWD
	segment.clear()
	segment.set_digit_raw(0,0xF8)
	#segment.set_digit_raw(1,0x9C)
	segment.set_digit_raw(1,0x3C)
	segment.set_digit_raw(2,0x1E)
	#segment.set_digit_raw(2,0x9C)
	segment.set_digit_raw(3,0x5E)
	segment.write_display()
	time.sleep(2)
	return
	
#######################################################################

def GetSignalkValue(sks,tlm,skval):

	skval.send(sks)
	time.sleep(0.25) #FAILS When removed
	if skval.poll():
	#if tlm.poll():
		it = skval.recv()
		#it = tlm.recv()
		return it
	else:
		return 0.0
		
#######################################################################

def ClearSKVal(skval):

	while skval.poll():
		bbckt = skval.recv()
	
#######################################################################

def GetHeading ():
	#GetHeading(skval)

	#skstring = "ap.heading"
	skstring = ResolveSKstrng('HDG')
	dispVal=GetSignalkValue(skstring,tlm,skval)
	return float(dispVal)
	
#######################################################################
	
def GetCommand ():
	#skstring = "ap.heading_command"
	skstring = ResolveSKstrng('CMD')
	dispVal=GetSignalkValue(skstring,tlm,skval)
	return float(dispVal)
	
#######################################################################
	
def GetRoll ():
	#skstring = "imu.roll"
	skstring = ResolveSKstrng('HEEL')
	dispVal=GetSignalkValue(skstring,tlm,skval)
	return float(dispVal)

#######################################################################

def GetTrueWindDir ():
	#skstring = "environment.wind.direction.True"
	dispVal=GetSignalkValue("environment.wind.direction.True")
	return float(dispVal)
	
#######################################################################
	
def GetTrueWindSpeed ():
	#skstring = "environment.wind.speed"
	dispVal=GetSignalkValue("environment.wind.speed")
	return float(dispVal)
	
#######################################################################
	
def GetSOG ():
	dispVal=GetSignalkValue("ap.P")
	#dispVal=GetSignalkValue("navigation.speedOverGround")
	return float(dispVal)

#######################################################################

def GetDepth ():
	#skstring = "environment.water.depthSurface"
	dispVal=GetSignalkValue("environment.water.depthSurface")
	#dispVal=GetSignalkValue("imu.pitch")
	#return float(dispVal)
	return dispVal

#######################################################################

def DispTestSegments ():

	segment.clear()
	segment.set_digit(0, "8")
	segment.set_digit(1, "8")
	segment.set_digit(2, "8")
	segment.set_digit(3, "8")
  # Turn-On colon and Ascended Decimal-Point
	segment.set_colon(True)
	segment.set_fixed_decimal(True)

	segment.write_display()

  # Wait a quarter second (less than 1 second to prevent colon blinking getting$
	time.sleep(1.5)
	segment.clear()

#######################################################################

def DispTime ():

	now = datetime.datetime.now()
	hour = now.hour
	minute = now.minute
	second = now.second

	segment.clear()
	segment.write_display()
	
  # Set hours
	segment.set_digit(0, int(hour / 10))	# Tens
	segment.set_digit(1, hour % 10)			# Ones
  # Set minutes
	segment.set_digit(2, int(minute / 10))	# Tens
	segment.set_digit(3, minute % 10)		# Ones
  # Toggle colon
	segment.set_colon(second % 10)			# Toggle colon at 1Hz

	segment.write_display()

  # Wait a quarter second (less than 1 second to prevent colon blinking getting$
	time.sleep(1)
	#time.sleep(0.25)

#######################################################################

def InitButton():
	GPIO.setmode(GPIO.BOARD)   # Use physical board-pin-numbering
	
	GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP) #Take to GND for interrupt/Button
	#EVENT GROUNDING PIN #23 to PIN #25
	GPIO.add_event_detect(23,GPIO.FALLING,callback=Button_Callback, bouncetime=400)
	return

#######################################################################

#FOCUS

def Button_Callback (pin):
	global DISPLAYCMD
	DispPUSH ()
	print("Button was PRESSED")
	#Set next telem selection
	
	#tllen = len(telem_list)
	
	if(DISPLAYCMD =='TIME'):  #TEST is End-Of-List, goto begin of list
		#DISPLAYCMD = 'TIME'
		DISPLAYCMD = telem_list[0]
		return DISPLAYCMD
	else:
		lentry = telem_list.index(DISPLAYCMD)
		lentry = lentry + 1
		DISPLAYCMD = telem_list[lentry]
		return DISPLAYCMD

#######################################################################

def labelMgr(lstatus):
	
	global LABELINTERVAL
	while True:
		dt = LABELINTERVAL
		#print('dt = '+str(dt)+'')
		#time.sleep(30) #30 seconds
		time.sleep(dt)
		#should this really be a timer invocation
		lstatus.send(1)

#######################################################################
	
def CmdListener (txmtr):
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_address = (CMDServer, CMDPort)
	sock.bind(server_address)
	sock.listen(1) # Listen for incoming connections
	while True:
		## Wait for a connection
		#print('Waiting for a Connection!')
		connection, client_address = sock.accept()
		#print >>sys.stderr, 'Got past Connection, client...'
		try:
			while True:
				data = connection.recv(32)#16
				print('Received Command: ')
				print(data)
				#Send new command then break and close connection
				txmtr.send(data)
				break
		finally:
			## Clean up the connection
			connection.close()
			
##############################################################

def GsKVProc(tlm,skval):
	
	#global SIGNALKHOST
	#global SIGNALKPORT
	
	while True:
		print('\nAttempting Connection!\n')
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		
		try:
			#print(SIGNALKHOST)	
			connection = socket.create_connection((SIGNALKHOST,SIGNALKPORT))
			# CONNECTION HANDLING WEAK ???????
			if connection:
				print('Connection Established from GskVProc to SK_Server!\n')
			
				while True:
					#time.sleep(2) #FOR TEST PURPOSE DELAY ONLY
					if skval.poll():
						wsk = skval.recv()
						request = {'method' : 'get', 'name' : wsk}
						connection.send(kjson.dumps(request)+'\n')
						line=connection.recv(1024)
						msg = kjson.loads(line.rstrip())
						value = msg[wsk]["value"]
						#Return telemetry data
						skval.send(str(value))
						#tlm.send(str(value))

						#if not connection:
							#DispNCON()
							#print('No Server Connection Established!')
							#time.sleep(2)
		except:
			DispNCON()
			print('\nNo Server Connection Established!')
			time.sleep(2)
		#finally:

#######################################################################
#######################################################################

(tlm,skval) = Pipe() #into GsKVProc()
#(skvalsrc,skvaldst) = Pipe(False) #into GsKVProc()
skProc = Process(target=GsKVProc, args=(skval,tlm))

#######################################################################

SKCfgRead()

#######################################################################

def main():

	global DISPLAYCMD
	
	global SIGNALKHOST
	global SIGNALKPORT
	global BRIGHTNESS
	global DISPLAYLABEL
	global LABELINTERVAL
	global DEFDISPLAYCMD
	global DISPLAYREFRESH
		
	DISPLAYCMD		= 'BNAV'
	DISPLAYLABEL	= 1

	#SKCfgRead()
	DISPLAYCMD = DEFDISPLAYCMD
	ReadTelemList()
	InitButton()
	#Preparation for GetSignalkValue() to maintain socket with SignalK server
	skProc.start()
	#sis = ResolveSKstrng('CMD') #Called for testing purposes
	#print('SKS is ' + sis +'\n')
	
	(rcvr,txmtr) = Pipe(False)
	proc = Process(target=CmdListener, args=(txmtr,))
	proc.start()
	#proc.join()
	
	#if DISPLAYLABEL is True:
	(interval,lstatus) = Pipe(False)
	displabel = Process(target=labelMgr, args=(lstatus,))
	displabel.start()
	
	while True:
		lstat = 0
		print (DISPLAYCMD + " is the current DISPLAYCMD \n ")
		
		if rcvr.poll():
			val = rcvr.recv()
			if CommandFilter(val) == 0:
				DISPLAYCMD = val
		
		print('SIGNALKHOST is '+ SIGNALKHOST +'')
		print('SIGNALKPORT is '+ str(SIGNALKPORT) +'')
		print('BRIGHTNESS is '+ str(BRIGHTNESS) +'')
		print('DISPLAYLABEL is '+ str(DISPLAYLABEL) +'')
		print('LABELINTERVAL is '+ str(LABELINTERVAL) +'')
		print('DEFDISPLAYCMD is '+ DEFDISPLAYCMD +'')
		print('DISPLAYREFRESH is '+ str(DISPLAYREFRESH) +'')

		if DISPLAYLABEL:
			if interval.poll():
				lstat = interval.recv()
				print('Post Telemetry Label for DISPLAYCMD: '+ DISPLAYCMD +'')
				#print(lstat)
			else:
				#print('Waiting LABEL-INTERVAL\n')
				lstat = 0

		display.set_brightness(BRIGHTNESS)  
		
		UpdateDisplay(DISPLAYCMD,lstat) #default to labels on every 15 seconds
		
		#pip install keyboard #(module)
		#if keyboard.is_pressed('S') or keyboard.is_pressed('s'):
			#Button_Callback()
		
		#print('\nPROCESSOR Utilization: ' + str(psutil.cpu_percent()) + ' percent! \n')
		
		time.sleep(DISPLAYREFRESH)
		#time.sleep(0.5)
		
#######################################################################

if __name__ == '__main__':
    main()

