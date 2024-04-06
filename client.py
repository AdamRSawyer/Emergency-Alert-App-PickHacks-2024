#client code

import socket
import struct
from message import Message

def sendMessage(message, serverAddress, serverPort):
	clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	clientsocket.connect((serverAddress, serverPort))
	messageSize = len(message.Extra) + 140
	serializedMessage = None
	if (len(message.Extra) == 0):
		serializedMessage = struct.pack("I128cff", messageSize, *message.Name, float(message.Lat), float(message.Log))
	else:
		serializedMessage = struct.pack(f"I128cff{messageSize - 140}c", messageSize, *message.Name, float(message.Lat), float(message.Log), *message.Extra)
	clientsocket.send(serializedMessage)
	clientsocket.close()

if __name__ == "__main__":
	senderVal1 = input("Enter Name: ")
	senderVal2 = input("Enter Latitude: ")
	senderVal3 = input("Enter Log: ")
	senderVal4 = input("Enter Extra Message: ")

	message = Message(senderVal1, senderVal2, senderVal3, senderVal4)
	serverAddress = 'localhost'
	serverPort = 9999

	sendMessage(message, serverAddress, serverPort)
