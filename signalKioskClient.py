
#!/usr/bin/env python
import time
import datetime
import socket
import sys

def CommandTransmit():

	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	# Connect the socket to the port where the server is listening
	server_address = ('localhost', 10000)
	print >>sys.stderr, 'connecting to %s port %s' % server_address
	sock.connect(server_address)
	print >>sys.stderr, 'Command Please'

	try:
		# Send message
		message = raw_input()
		print >>sys.stderr, 'Sending "%s"' % message
		sock.sendall(message.upper())
		
		
		
	finally:
		print >>sys.stderr, 'Closing Client Socket'
		sock.close()

CommandTransmit()



