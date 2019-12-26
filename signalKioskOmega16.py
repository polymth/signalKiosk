
#!/usr/bin/env python
#

#######################################################################

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
#import threading
import psutil
#import keyboard #must run as root ???

import RPi.GPIO as GPIO
from Adafruit_LED_Backpack import SevenSegment
from signalk import kjson

BRIGHTNESS	= 1

global DISPLAYCMD
global tlm
global skval
global skstring

DISPLAYCMD		= 'ALL'

DISPLAYLABEL	= 0
LABELINTERVAL	= 5000 #15000 milliseconds = 15 seconds

CMDServer	= 'localhost'
CMDPort		= 10000

SIGKHOST	= '10.0.0.101'
#SIGKHOST	= 'localhost'
SIGKPORT	= 21311
#SIGKPORT	= 21311


#######################################################################

#sk_list = [('HDG','ap.heading'),('CMD','ap.heading_command'),('HEEL','imu.roll')]
telem_list = ['TIME','ALL','BNAV','HDG','CMD','HEEL','TEST']

#######################################################################
display = SevenSegment.SevenSegment()
#######################################################################
segment = SevenSegment.SevenSegment(address=0x70, busnum=1)

# Initialize the display
segment.begin()
#######################################################################

#print "Setting Display Brightness"
display.set_brightness(BRIGHTNESS)   #ht16k33
#######################################################################

#os.nice(15) #-20 to 20

#######################################################################

def ReadTelemList ():
	print('\nAttempting to READ telem_list from FILE into sk_list!\n')
	return

#######################################################################

def CommandFilter (data):
	
	#if data string contains '::' "delimiter"
		#dataroot		= data less all before delimiter '::'
		#datapayload	= data less all after delimiter '::'
	
	print('Into CommandFilter Proc')
	print(data)
	DISPLAYCMD = data
	
	if data == 'SIGNALKHOST':
	#if dataroot == 'SIGNALKHOST':
		print('Its a Command: set the host variable')
		#SIGNALKHOST = datapayload
		return (1)
	elif data == 'SIGNALKPORT':
		print('Its a Command: set the port variable')
		#SIGNALKPORT = datapayload
		return (1)
	#elif data == 'ANOTHER_COMMAND':
		#print('Its a Command: set the variable')
		#VARIABLE = datapayload
		return (1)
		
	return (0) #if not a config update
	#return
	
#######################################################################
	
def UpdateDisplay(cmd,labl):

	segment.clear()
	#print('Into UpdateDisplayProc')
	
	if cmd == 'TIME':
		#DispTIMElabel() #label
		if labl:
			DispTIMElabel()
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
		DispHDNG(labl)
		DispCMD(labl)
		DispHeeL(labl)
		#DispDepth(1)
		#DispSOG()		#NA at this time
		if labl:
			DispTIMElabel()
		DispTime()
		return
		
	if cmd == 'ALL':
		print('Displaying ALL Telemetry including PROMPTS:')
		DispTestSegments()
		DispAlert()
		DispSTART()
		DispSTOP()
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
		#DispPUSH()
		return
		
	return

#######################################################################

def DisplayTelem (telem):
	print(telem)
	segment.clear()
	segment.set_fixed_decimal(True)
	segment.write_display()
	#telem = round((telem * 2) / 2)
	segment.print_float(telem, decimal_digits=1, justify_right=True)
	segment.write_display()
	time.sleep(1)	#For 1 second
	return
	
#######################################################################
	
def DispHDNG (lstat):
	#DispHDNG(cmd,labl)
	segment.clear()
	if lstat == 1:
		#HdnG - Heading
		segment.set_digit_raw(0,0xF6)
		segment.set_digit_raw(1,0x5E)
		segment.set_digit_raw(2,0xbd)
		segment.set_digit_raw(3,0x80)
		segment.write_display()
		time.sleep(0.5)
	
	DisplayTelem (GetHeading ())
	return

#######################################################################
	
def DispCMD (lstat):
	segment.clear()
	#CSE - Course
	if lstat == 1:
		segment.set_digit_raw(0,0x39)
		#segment.set_digit_raw(1,0x6d)
		segment.set_digit_raw(1,0x54)#37=large M-segment
		segment.set_digit_raw(2,0x54)
		#segment.set_digit_raw(2,0xf9)
		segment.set_digit_raw(3,0x5E)
		#segment.set_digit_raw(3,0x80)
		segment.write_display()
		time.sleep(0.5)

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
		segment.set_digit_raw(2,0xf9)
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
	#StrT - Alert
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
	#StrT - Alert
	segment.clear()
	segment.set_digit_raw(0,0x6D)
	segment.set_digit_raw(1,0xF8)
	segment.set_digit_raw(2,0xDC)	
	segment.set_digit_raw(3,0xF3)
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
	segment.set_digit_raw(1,0x9C)
	segment.set_digit_raw(2,0x9C)
	segment.set_digit_raw(3,0x5E)
	segment.write_display()
	time.sleep(2)
	return
	
#######################################################################

def GetSignalkValue(sks,tlm,skval):

	skval.send(sks)
	time.sleep(0.5)
	if skval.poll():
		it = skval.recv()
		return it
	else:
		return 000.0
	
#######################################################################

def GetHeading ():
	#GetHeading(skval)

	skstring = "ap.heading"
	dispVal=GetSignalkValue(skstring,tlm,skval)
	return float(dispVal)
	
#######################################################################
	
def GetCommand ():
	skstring = "ap.heading_command"
	dispVal=GetSignalkValue(skstring,tlm,skval)
	return float(dispVal)
	
#######################################################################
	
def GetRoll ():
	skstring = "imu.roll"
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

####################################################################################

def InitButton():
	GPIO.setmode(GPIO.BOARD)   # Use physical board-pin-numbering
	
	GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP) #Take to GND for interrupt/Button
	#EVENT GROUNDING PIN #23 to PIN #25
	GPIO.add_event_detect(23,GPIO.FALLING,callback=Button_Callback, bouncetime=300)
	return

#######################################################################

def Button_Callback (pin):
	global DISPLAYCMD
	DispPUSH ()
	print("Button was PRESSED")
	#Set next telem selection
	
	#tllen = len(telem_list)
	
	if(DISPLAYCMD =='TEST'):  #TEST is End-Of-List, goto begin of list
		DISPLAYCMD = 'TIME'
		return DISPLAYCMD
	lentry = telem_list.index(DISPLAYCMD)
	lentry = lentry + 1
	DISPLAYCMD = telem_list[lentry]
	return DISPLAYCMD

####################################################################################

def labelMgr(lstatus):
	
	while True:
		time.sleep(30)
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
				data = connection.recv(16)
				print('Received Command: ')
				print(data)
				#Send new command then break and close connection
				txmtr.send(data)
				break
		finally:
			## Clean up the connection
			connection.close()
			
			
#######################################################################
		
##############################################################

def GsKVProc(tlm,skval):
	
	while True:
		print('\nAttempting Connection!\n')
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		connection = socket.create_connection((SIGKHOST,SIGKPORT))
		# CONNECTION HANDLING is WEAK ?????????????
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
		#if no connection:
		else:
			DispNCON()
			#print('No Server Connection Established!')
			time.sleep(5)

#######################################################################

(tlm,skval) = Pipe() #into GsKVProc()
#(skvalsrc,skvaldst) = Pipe(False) #into GsKVProc()
skProc = Process(target=GsKVProc, args=(skval,tlm))
#######################################################################
#######################################################################
#######################################################################


def main():

	ReadTelemList()

	
	global DISPLAYCMD
	DISPLAYCMD		= 'HDG'
	DISPLAYLABEL	= 1
	LABELINTERVAL	= 30000 #15000 milliseconds = 15 seconds

	InitButton()
	
	(rcvr,txmtr) = Pipe(False)
	proc = Process(target=CmdListener, args=(txmtr,))
	proc.start()
	#proc.join()
	
	#if DISPLAYLABEL is True:
	(interval,lstatus) = Pipe(False)
	displabel = Process(target=labelMgr, args=(lstatus,))
	displabel.start()
	
	#Preparation for GetSignalkValue() to maintain socket with SignalK server
	#(tlm,skval) = Pipe() #into GsKVProc()
	#(skvalsrc,skvaldst) = Pipe(False) #into GsKVProc()
	#proc = Process(target=GsKVProc, args=(skval,tlm))
	skProc.start()
	#proc.join()

	
	while True:
		lstat = 0
		print (DISPLAYCMD + " is the current DISPLAYCMD \n ")
		
		if rcvr.poll():
			val = rcvr.recv()
			#if CommandFilter(val) == 0:
			DISPLAYCMD = val
			#else:
			#print('Store Command Parameter in config file')
			#NNNN
		
		#print('DISPLAYLABEL is '+ str(DISPLAYLABEL) +'')
		#print('Still Counting-Down Label-Interval')
		
		if DISPLAYLABEL:
			if interval.poll():
				lstat = interval.recv()
				print('Time To Write Telemetry Label for DISPLAYCMD: '+ DISPLAYCMD +'')
				#print(lstat)
			else:
				#print('Still Counting-Down Label-Interval')
				lstat = 0

		UpdateDisplay(DISPLAYCMD,lstat) #default to labels on every 15 seconds
		
		skstring = 'ap.heading'
		#skstring = 'ap.heading_command'
		#callGsKVProc(skstring,tlm,skval)
		
		#callGsKVProc('ap.heading_command',tlm,skval)
		#callGsKVProc()
		
		#pip install keyboard #(module)
		#if keyboard.is_pressed('S') or keyboard.is_pressed('s'):
			#Button_Callback()
		
		print('\nPROCESSOR Utilization: ' + str(psutil.cpu_percent()) + ' percent! \n')
		
		time.sleep(0.5)
		
#######################################################################

if __name__ == '__main__':
    main()

