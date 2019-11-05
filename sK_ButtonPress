from __future__ import print_function
import os, sys
import time, math
import RPi.GPIO as GPIO
#global DISPLAYCMD
DISPLAYCMD	= 'HDG'
telem_list = ['ALL','BNAV','HDG','CMD','HEEL','TIME','TEST']

def InitButton():
	GPIO.setwarnings(False)    # Ignore warning for now
	GPIO.setmode(GPIO.BOARD)   # Use physical pin numbering
	# Set pin 18 to be an input pin and set initial value to be pulled low (off)
	GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	GPIO.add_event_detect(18,GPIO.RISING,callback=Button_Callback, bouncetime=400) # Event:pin-18 rising
	return

def Button_Callback ():
	#global DISPLAYCMD
	print("Button was pressed")
	DISPLAYCMD = bcProxy()
	return
	
def bcProxy ():
	global DISPLAYCMD
    #Set next telem selection on Kiosk.
	if(DISPLAYCMD =='TEST'):  #TEST is End-Of-List, goto begin of list
		DISPLAYCMD = 'ALL'
		return DISPLAYCMD
	lentry = telem_list.index(DISPLAYCMD)
	lentry = lentry + 1
	DISPLAYCMD = telem_list[lentry]
	return DISPLAYCMD
	
def main():
	DISPLAYCMD = "HDG"
	InitButton()
	print (DISPLAYCMD + " is the current starting DISPLAYCMD ")
	while True:
		print (DISPLAYCMD + " is the current DISPLAYCMD ")
		DISPLAYCMD = bcProxy()
		time.sleep(2)

if __name__ == '__main__':
    main()

