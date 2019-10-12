
#!/usr/bin/env python
#
#   Adapted from boatimu.py as prototype

########################################################################################

# SIGNALKIOSK-README follows:

# signalKiosk.py tries to follow the structure/architecture of boatimu.py

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

#Note: i dont run a lcd display on tinypilot/pypilot so if there is not a gpio PIN available,
# that conflict will need to be addressed

########################################################################################


from __future__ import print_function
import os, sys
import time, math, multiprocessing, select
import datetime
import socket

import RPi.GPIO as GPIO
from Adafruit_LED_Backpack import SevenSegment

from signalk import kjson

from signalk.pipeserver import NonBlockingPipe
from signalk.server import SignalKServer
from signalk.pipeserver import SignalKPipeServer
from signalk.values import *

from signalk import linebuffer

Brightness	= 1

DISPLAYCMD	= 'TIME'

CMDServer	= 'localhost'
CMDPort		= 10000

#telem_list = ['ALRM','ALT', 'ATMP', 'AUTO', 'BRG', 'COG', 'CSE', 
#'DTE', 'DPT', 'ETA', 'HEEL', 'PTCH', 'SAT', 'SPD', 'WTMP', 'TIME', 'VTW']
telem_list = ['TIME','HDG','CSE','HEEL','SOG','DPTH','TEST']
#eventually read list from telem_list.txt
#   	MNEMONIC		SIGK_PATH
#i.e.	"CSE"			"ap.heading_command"


display = SevenSegment.SevenSegment()
#####################################################################################################
segment = SevenSegment.SevenSegment(address=0x70, busnum=1)
# Initialize the display. Must be called once before using the display
segment.begin()
#####################################################################################################

#print "Setting Display Brightness"
display.set_brightness(Brightness)   #ht16k33


try:
  import SevenSegment #7Seg stuff here
except ImportError:
  SevenSegment = False
  print('SevenSegment-Driver library not detected, please install it')


def InitButton():

	#print("Entering Initialization !\n")
	#General GPIO
	GPIO.setwarnings(False)    # Ignore warning for now
	GPIO.setmode(GPIO.BOARD)   # Use physical pin numbering

	#Push-Button
	# Set pin 18 to be an input pin and set initial value to be pulled low (off)
	GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


def Button_Callback(): #worked when 'channel' removed
#def button_callback(channel):  IS/WAS the "channel" variable necessary
    #print("Button was pushed!\n\n")
    #Set next telem selection on Kiosk.
    UpdatedispCMD()
    return


def UpdatedispCMD():  #should be named Update-Selection-CMD
	cmdtmp = getCMDcur()
	lentry = getCMDIndex(cmdtmp)		#Compare to telem_list VARIABLE-LIST
	if(cmdtmp=='TEST'):					#TEST is Designated End-Of-List, go to beginning of list
		setCMDcur('TIME')
	else:
		setCMDcur(telem_list[lentry+1])	#Index to Next Telemetry entry in list
	return								#Update with New-Telemtry-Entry determined

def getCMDcur():
	curcmd = DISPLAYCMD
	return curcmd
	
def setCMDcur(newcmd):
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


		
def UpdateDisplay():
	segment.clear()
	if DISPLAYCMD == 'TIME':
		DispTime()
		
	if DISPLAYCMD == 'HDG':
		DispHDNG()
		
	if DISPLAYCMD == 'CSE':
		DispCMD()
		
	if DISPLAYCMD == 'HEEL':
		DispHeeL()
		
	if DISPLAYCMD == 'DPTH':
		DispDepth()
		
	if DISPLAYCMD == 'SOG':
		DispSOG()
		
	if DISPLAYCMD == 'NONe':  #display no data available
		DispNDat
		
	return



def DisplayTelem (telem):
	segment.clear()
	segment.set_fixed_decimal(True)
	segment.write_display()
	segment.print_float(telem, decimal_digits=1, justify_right=True)
	segment.write_display()
	time.sleep(1)	#For 1 second
	return
	
	
def DispHDNG ():
	segment.clear()
	#HdnG - Heading
	segment.set_digit_raw(0,0xF6)
	segment.set_digit_raw(1,0x5E)
	segment.set_digit_raw(2,0xbd)
	segment.set_digit_raw(3,0x80)
	segment.write_display()
	time.sleep(2)
	
	telem = GetHeading ()
	DisplayTelem (telem)
	#VERSUS
	#dispVal = GetHeading ()
	#segment.clear()
	#segment.set_fixed_decimal(True)
	#segment.write_display()
	#segment.print_float(dispVal, decimal_digits=1, justify_right=True)
	#segment.write_display()
	#time.sleep(2)
	return
	
	
	
def DispCMD ():
	#CSE - Course
	segment.clear()
	segment.set_digit_raw(0,0x39)
	segment.set_digit_raw(1,0x6d)
	segment.set_digit_raw(2,0xf9)
	segment.set_digit_raw(3,0x80)
	segment.write_display()
	time.sleep(1)
	
	telem = GetCommand ()
	DisplayTelem (telem)
	return


def DispHeeL ():
	#HeeL - Heel
	segment.clear()
	segment.set_digit_raw(0,0xF6)
	segment.set_digit_raw(1,0xf9)	#7b=large-small-e
	segment.set_digit_raw(2,0xf9)
	segment.set_digit_raw(3,0x38)
	segment.write_display()
	time.sleep(1)
	
	telem = GetRoll()
	DisplayTelem (telem)
	return


def DispDepth ():
	#dPtH - Depth
	segment.clear()
	segment.set_digit_raw(0,0x5E)
	segment.set_digit_raw(1,0xF3)
	segment.set_digit_raw(2,0xF8)
	segment.set_digit_raw(3,0xF6)
	segment.write_display()
	time.sleep(1)
	
	telem = GetDepth()
	DisplayTelem (telem)
	return


def DispSOG ():
	#SOG - Speed Over Ground
	segment.clear()
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
	

def DispNDat ():
	#NonE - No Data Available
	segment.clear()
	segment.set_digit_raw(0,0x37)
	segment.set_digit_raw(1,0xbf)
	segment.set_digit_raw(2,0x37)
	segment.set_digit_raw(3,0x7b)
	segment.write_display()
	time.sleep(1)
	
	
def GetSignalkValue (name):
	connection = socket.create_connection((HOST, PORT))
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



def TestSegments ():

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


def cmd_process(cmd_pipe):

	#print 'cmd on', os.getpid()
	if os.system('sudo chrt -pf 2 %d 2>&1 > /dev/null' % os.getpid()):
		print('warning, failed to make cmd process realtime')
      
	
	#Start CommandServer()
	## Create a TCP/IP socket
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	## Bind the socket to the port
	server_address = (CMDServer, CMDPort)
	print >>sys.stderr, 'Starting Command Server Listener on %s port %s' % server_address
	sock.bind(server_address)

	## Listen for incoming connections
	sock.listen(1)
	#print "Command Server Listening"

	while True:
		#sock.listen(1)
		## Wait for a connection
		print >>sys.stderr, 'Waiting for a connection'
		connection, client_address = sock.accept()
		
		try:
			while True:
				data = connection.recv(16)
				print >>sys.stderr, 'Received Display Command:  "%s"' % data
				TestSegments() #BRIEFLY
				#print "BEEP, BEEP"
				pipe.send(data, False)
		finally:
			## Clean up the connection
			connection.close()
			#return
			#break



class SignalKiosk(object):
  def __init__(self, server, *args, **keywords):
    self.server = server
    self.cmd_pipe, cmd_pipe = NonBlockingPipe('cmd_pipe')
    
  def __del__(self):
    print('terminate imu process')
    self.cmd_process.terminate()

  def Register(self, _type, name, *args, **kwargs):
    value = _type(*(['cmd.' + name] + list(args)), **kwargs)
    return self.server.Register(value)
    
  def CMDRead(self):    
    data = False
    while self.poller.poll(0): # read all the data from the pipe
		data = self.cmd_pipe.recv()
		return data
    

class SignalKioskServer():
  def __init__(self):
    # setup all processes to exit on any signal
    self.childpids = []
    def cleanup(signal_number, frame=None):
        print('got signal', signal_number, 'cleaning up')
        while self.childpids:
            pid = self.childpids.pop()
            os.kill(pid, signal.SIGTERM) # get backtrace
        sys.stdout.flush()
        if signal_number != 'atexit':
          raise KeyboardInterrupt # to get backtrace on all processes

    # is broken yet, so doesn't raise an exception
    def printpipewarning(signal_number, frame):
        print('got SIGPIPE, ignoring')

    import signal
    for s in range(1, 16):
        if s == 13:
            signal.signal(s, printpipewarning)
        elif s != 9:
            signal.signal(s, cleanup)

    #  server = SignalKServer()
    self.server = SignalKPipeServer()
    #self.boatcmd = BoatIMU(self.server)
    self.kioskcmd = SignalKiosk(self.server)

    self.childpids = [self.kioskcmd.cmd_process.pid]
    signal.signal(signal.SIGCHLD, cleanup)
    import atexit
    atexit.register(lambda : cleanup('atexit'))
    #self.t00 = time.time()

  def iteration(self):
    self.server.HandleRequests()
    #self.data = self.boatimu.IMURead()
    self.data = self.kioskcmd.CMDRead()
    
    
def main():
	#boatimu = BoatIMUServer()
	print >>sys.stderr, 'Into main()'
	signalkiosk = SignalKioskServer()
	#quiet = '-q' in sys.argv

	try:
		GPIO.add_event_detect(18,GPIO.RISING,callback=Button_Callback) # Setup event on pin 18 rising edge
		message = input("Press Button/Enter to SELECT-NEXT Telemetry Available!\n\n")
		return
	except KeyboardInterrupt:
		#print 'Received CTRL+C, Update CMD-File then Close-Down'
		Button_Callback()
		return

	InitButton()

	while True:
		#boatimu.iteration()
		signalkiosk.iteration()
		#data = boatimu.data
		data = signalkiosk.data

		if data:
			DISPLAYCMD = data
			UpdateDisplay()
			break
		else:
			UpdateDisplay()
			break
		#Check for Commands and Refresh
		sleep(0.5)


if __name__ == '__main__':
    main()

