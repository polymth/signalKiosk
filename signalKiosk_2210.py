
#!/usr/bin/env python
#

########################################################################################

# SIGNALKIOSK-README follows:

# signalKiosk.py is meant to run on tinypilot-OS

# signalKiosk.py should execute independently, or/with pypilot(for now) on tinypilot

# signalKiosk.py will query a signalK-Server for telemetry(like):, wind, depth, speed, etc.
# and display those telemetry (preceeded by labelling mnemonic every-10-displays/sec.
# Example: HDG,pause,150.6,pause,150.6,pause...7sec elapse...150.6,pause, HDG,pause,150.6,pause......)
# on a 4-character,seven-segment-display; with 000.0 decimal/precision

# signalKiosk.py will monitor a tcp-socket (as a command-server), and queue up the
# requested telemetry signalled (see telem_list variable in code)  Additionally, this command-server
# port will be used for future configuaration (in-band-signalling) enhancements i.e., to define 
# IPs, ports, delays/time, etc.  e.g, SKServer=10.10.10.1, SKPort=22222, TelemLabelOccurSec=10,
# TelemLabelOccurSec=0 means no labels, CountDownTimerMode, etc.

#signalKiosk.py will monitor a push-button-switch that will, in-sequence, advance the
#selection of telemetry defined in the tele_list variable/imported-file

########################################################################################


from __future__ import print_function
import os, sys
import time, math
import datetime
import socket
from multiprocessing import Process, Pipe
#import threading

import RPi.GPIO as GPIO
from Adafruit_LED_Backpack import SevenSegment
from signalk import kjson

Brightness	= 1

#DISPLAYCMD	= 'HDG'

CMDServer	= 'localhost'
CMDPort		= 10000

SIGKHOST	= '10.0.0.100'
#SIGKHOST	= 'localhost'
SIGKPORT	= 21311
#SIGKPORT	= 21311

telem_list = ['TIME','HDG','CSE','HEEL','SOG','DPT','TEST']


display = SevenSegment.SevenSegment()
#####################################################################################################
segment = SevenSegment.SevenSegment(address=0x70, busnum=1)

# Initialize the display. Must be called once before using the display
segment.begin()
#####################################################################################################

#print "Setting Display Brightness"
display.set_brightness(Brightness)   #ht16k33
####################################################################################

def CommandFilter (data):
	
	#if data contains string '::' delimiter
		#dataroot		= data less all after delimiter '::'
		#datapayload	= data less all before delimiter '::'
	
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
	

####################################################################################	

def InitButton():

	#print("Entering Initialization !\n")
	#General GPIO
	GPIO.setwarnings(False)    # Ignore warning for now
	GPIO.setmode(GPIO.BOARD)   # Use physical pin numbering

	#Push-Button
	# Set pin 18 to be an input pin and set initial value to be pulled low (off)
	GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

####################################################################################

def Button_Callback(): #worked when 'channel' removed
#def button_callback(channel):  IS/WAS the "channel" variable necessary
    #print("Button was pushed!\n\n")
    #Set next telem selection on Kiosk.
    #IndexDispCMD()
    return
    
####################################################################################

def IndexDispCMD():  #should be named Update-Selection-CMD
	cmdtmp = getCMDcur()
	lentry = getCMDIndex(cmdtmp)		#Compare to telem_list VARIABLE-LIST
	if(cmdtmp =='TEST'):				#TEST is Designated End-Of-List, go to beginning of list
		setCMDcur('TIME')
	else:
		setCMDcur(telem_list[lentry+1])	#Index to Next Telemetry entry in list
	return								#Update with New-Telemtry-Entry determined


def getCMDcur():
	curcmd = DISPLAYCMD
	return curcmd
	
	
def setCMDcur(newcmd):
	#print('Setting DISPLAYCMD to: ')
	#print(newcmd)
	DISPLAYCMD = newcmd
	return
		
		
def getCMDIndex(cmdtmp):
	index = telem_list.index(cmdtmp)
	listlen = len(telem_list)
	index = index + 1
	if(index >= listlen):
		return 0
	else:
		return index

####################################################################################
		
def UpdateDisplay(cmd,labl):

	segment.clear()
	#print('Into UpdateDisplayProc')
	if cmd == 'TIME':
		DispTime(1)
		return
		
	if cmd == 'HDG':
		#DispHDNG(1)
		DispHDNG(labl)
		return
		
	if cmd == 'CSE':
		DispCMD(1)
		return
		
	if cmd == 'HEEL':
		DispHeeL(1)
		return
		
	if cmd == 'DPTH':
		DispDepth(1)
		return
		
	if cmd == 'SOG':
		DispSOG(1)
		return
		
	if cmd == 'NONe':  #display no data available
		DispNDat
		return
		
	if cmd == 'BNAV':
		DispHDNG(1)
		DispCMD(1)
		DispHeeL(1)
		#DispSOG()		#NA at this time
		DispTime()
		return
		
	if cmd == 'ALL':
		DispTestSegments()
		DispAlert()
		DispNDat()
		DispTime()
		DispHEllO()
		DispFIN()
		DispHDNG(1)
		DispCMD(1)
		DispHeeL(1)
		#DispDepth(1)	#NA at this time
		#DispSOG(1)		#NA at this time
		return
		
	return

####################################################################################

def DisplayTelem (telem):
	print(telem)
	segment.clear()
	segment.set_fixed_decimal(True)
	segment.write_display()
	segment.print_float(telem, decimal_digits=1, justify_right=True)
	segment.write_display()
	time.sleep(1)	#For 1 second
	return
	
####################################################################################
	
def DispHDNG (lstat):
	segment.clear()
	if lstat == 1:
		#HdnG - Heading
		segment.set_digit_raw(0,0xF6)
		segment.set_digit_raw(1,0x5E)
		segment.set_digit_raw(2,0xbd)
		segment.set_digit_raw(3,0x80)
		segment.write_display()
		time.sleep(2)
	
	telem = GetHeading ()
	DisplayTelem (telem)
	return
	
	
def DispCMD (lstat):
	segment.clear()
	#CSE - Course
	if lstat == 1:
		segment.set_digit_raw(0,0x39)
		segment.set_digit_raw(1,0x6d)
		segment.set_digit_raw(2,0xf9)
		segment.set_digit_raw(3,0x80)
		segment.write_display()
		time.sleep(1)
	
	telem = GetCommand ()
	DisplayTelem (telem)
	return


def DispHeeL (lstat):
	segment.clear()
	#HeeL - Heel
	if lstat == 1:
		segment.set_digit_raw(0,0xF6)
		segment.set_digit_raw(1,0xf9)	#7b=large-small-e
		segment.set_digit_raw(2,0xf9)
		segment.set_digit_raw(3,0x38)
		segment.write_display()
		time.sleep(1)
	
	telem = GetRoll()
	DisplayTelem (telem)
	return


def DispDepth (lstat):
	segment.clear()
	#dPtH - Depth
	if lstat == 1:
		segment.set_digit_raw(0,0x5E)
		segment.set_digit_raw(1,0xF3)
		segment.set_digit_raw(2,0xF8)
		segment.set_digit_raw(3,0xF6)
		segment.write_display()
		time.sleep(1)
	
	telem = GetDepth()
	DisplayTelem (telem)
	return


def DispSOG (lstat):
	segment.clear()
	#SOG - Speed Over Ground
	if lstat == 1:
		segment.set_digit_raw(0,0x6d)
		segment.set_digit_raw(1,0xbf)
		segment.set_digit_raw(2,0xBD)
		segment.set_digit_raw(3,0x80)
		segment.write_display()
		time.sleep(1)
	
	dispVal = GetSOG()
	segment.clear()
	segment.set_fixed_decimal(True)
	segment.write_display()
	segment.print_float(abs(dispVal), decimal_digits=3, justify_right=True)
	segment.write_display()
	time.sleep(1)
	return
	

def DispNDat ():
	segment.clear()
	#NonE - No Data Available
	segment.set_digit_raw(0,0x37)
	segment.set_digit_raw(1,0xbf)
	segment.set_digit_raw(2,0x37)
	segment.set_digit_raw(3,0x7b)
	segment.write_display()
	time.sleep(1)
	return
	
	
def DispAlert ():
	#ALRt - Alert
	segment.clear()
	segment.set_digit_raw(0,0xF7)
	segment.set_digit_raw(1,0x38)
	# was segment.set_digit_raw(2,0xF7)
	segment.set_digit_raw(2,0xD0)	
	segment.set_digit_raw(3,0xF8)
	segment.write_display()
	time.sleep(2)
	return

def DispHEllO ():
	segment.clear()
	segment.set_digit_raw(0,0xF6)
	segment.set_digit_raw(1,0xF9)
	segment.set_digit_raw(2,0x36)
	segment.set_digit_raw(3,0xBF)
	segment.write_display()
	time.sleep(2)
	return
	
def DispFIN ():
	segment.clear()
	segment.set_digit_raw(0,0xF1)
	segment.set_digit_raw(1,0x86)
	segment.set_digit_raw(2,0x37)
	segment.set_digit_raw(3,0x80)
	segment.write_display()
	time.sleep(2)
	return

####################################################################################
	
def GetSignalkValue (name):
	
	connection = socket.create_connection((SIGKHOST,SIGKPORT))
	request = {'method' : 'get', 'name' : name}
	connection.send(kjson.dumps(request)+'\n')
	line=connection.recv(1024)
	try:
		msg = kjson.loads(line.rstrip())
		value = msg[name]["value"]
	except:
		value = ""
	connection.close();
	return value
	
####################################################################################

def GetHeading ():
	dispVal=GetSignalkValue("ap.heading")
	return float(dispVal)
	
def GetCommand ():
	dispVal=GetSignalkValue("ap.heading_command")
	return float(dispVal)
	
def GetRoll ():
	dispVal=GetSignalkValue("imu.roll")
	return float(dispVal)
	
def GetTrueWindDir ():
	dispVal=GetSignalkValue("environment.wind.direction.True")
	return float(dispVal)
	
def GetTrueWindSpeed ():
	dispVal=GetSignalkValue("environment.wind.speed")
	return float(dispVal)
	
def GetSOG ():
	dispVal=GetSignalkValue("ap.P")
	#dispVal=GetSignalkValue("navigation.speedOverGround")
	return float(dispVal)

def GetDepth ():
	dispVal=GetSignalkValue("environment.water.depthSurface")
	#dispVal=GetSignalkValue("imu.pitch")
	#return float(dispVal)
	return dispVal

####################################################################################

def DispTestSegments ():

	segment.clear()
	segment.set_digit(0, "8")
	segment.set_digit(1, "8")
	segment.set_digit(2, "8")
	segment.set_digit(3, "8")
  # Turn-On colon and Ascended Decimal-Point
	segment.set_colon(True)
	segment.set_fixed_decimal(True)

  # Write the display buffer to the hardware.  This must be called to
  # update the actual display LEDs.
	segment.write_display()

  # Wait a quarter second (less than 1 second to prevent colon blinking getting$
	time.sleep(1.5)
	segment.clear()

####################################################################################

def DispTime ():

	now = datetime.datetime.now()
	hour = now.hour
	minute = now.minute
	second = now.second

	segment.clear()
	segment.write_display()
	
  # Set hours
	segment.set_digit(0, int(hour / 10))     # Tens
	segment.set_digit(1, hour % 10)          # Ones
  # Set minutes
	segment.set_digit(2, int(minute / 10))   # Tens
	segment.set_digit(3, minute % 10)        # Ones
  # Toggle colon
	segment.set_colon(second % 10)              # Toggle colon at 1Hz

  # Write the display buffer to the hardware.  This must be called to
  # update the actual display LEDs.
	segment.write_display()

  # Wait a quarter second (less than 1 second to prevent colon blinking getting$
	time.sleep(1.0)

####################################################################################

def buttonConfig():
	try:
		GPIO.add_event_detect(18,GPIO.RISING,callback=Button_Callback) # Setup event on pin 18 rising edge
		message = input("Press Button/Enter to SELECT-NEXT Telemetry Available!\n\n")
		return
	except:
		#Button_Callback()
		return

####################################################################################

def labelMgr(lstatus):
	
	while True:
		time.sleep(15)	
		lstatus.send(1)

####################################################################################
	
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

####################################################################################
####################################################################################

def main():

	#InitButton()
	
	(rcvr,txmtr) = Pipe(False)
	proc = Process(target=CmdListener, args=(txmtr,))
	proc.start()
	#proc.join()
	
	(interval,lstatus) = Pipe(False)
	displabel = Process(target=labelMgr, args=(lstatus,))
	displabel.start()
	
	#DISPLAYCMD		= 'ALL'
	DISPLAYCMD		= 'HDG'
	
	DISPLAYLABEL	= 1
	LABELINTERVAL	= 15000 #15000 milliseconds = 15 seconds

	
	while True:
		lstat = 0
		print (DISPLAYCMD + " is the current DISPLAYCMD ")
		if rcvr.poll():
			val = rcvr.recv()
			if CommandFilter(val) == 0:
				DISPLAYCMD = val
		if interval.poll():
			lstat = interval.recv()
			print('Time To Write Telemetry Label')
			#print(lstat)
		else:
			print('Still Counting-Down Label-Interval')
			lstat = 0
			
		UpdateDisplay(DISPLAYCMD,lstat) #default to labels on every 15 seconds
		#segment.clear()
		time.sleep(1)
		
####################################################################################

if __name__ == '__main__':
    main()

