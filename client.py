#client code

import socket
import struct
from message import Message
from time import perf_counter, sleep
import fcntl, os
import errno
import sys

def sendMessage(message, clientSocket):
	messageSize = len(message.Extra) + 140
	serializedMessage = None
	if (len(message.Extra) == 0):
		serializedMessage = struct.pack("I128cff", messageSize, *message.Name, float(message.Lat), float(message.Log))
	else:
		serializedMessage = struct.pack(f"I128cff{messageSize - 140}c", messageSize, *message.Name, float(message.Lat), float(message.Log), *message.Extra)
	clientSocket.send(serializedMessage)
	

if __name__ == "__main__":

	serverAddress = '10.106.63.188'
	serverPort = 4760
	clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	clientsocket.connect((serverAddress, serverPort))
	clientsocket.setblocking(0)
	clientsocket.settimeout(1)

	senderVal1 = input("Enter Name: ")
	senderVal2 = input("Enter Latitude: ")
	senderVal3 = input("Enter Log: ")
	senderVal4 = input("Enter Extra Message: ")

	maxClientTime = 80
	initTime = perf_counter()

	message = Message(senderVal1, senderVal2, senderVal3, senderVal4)

	while perf_counter() - initTime < maxClientTime:
		data = False
		try:
			data = clientsocket.recv(1024)
		except socket.timeout as e:
			err = e.args[0]
		except socket.error as e:
			print(e)
			sys.exit(1)
		
				
		if data:
			s = struct.unpack('I', data[0:4])
			msg = struct.unpack(f'{s[0] - 4}c', data[4:])
			msg = b''.join(msg).decode('utf-8')
			print(msg)
		sendMessage(message, clientsocket)
		sleep(5)

	clientsocket.close()