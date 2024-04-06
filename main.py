#TCP server Code
import time
import socket
import threading
import struct
import requests
import multiprocessing as mp
from pymongo import MongoClient
from queue import Queue
from threading import Lock
from call.Call import *
import ssl


MONGODB_URI = "mongodb+srv://SK:PickHacks@pickhacks.s50jyfl.mongodb.net/?retryWrites=true&w=majority&appName=PickHacks"
DB_NAME = "messages"
COLLECTION_NAME = "messages"



db_lock = Lock()
apikey = 'AIzaSyAvEcUwJvMn0mXPBx1g66Xlu-QCLI5OmB0'

def listConvert(listInput):
	new = filtered_bytes = [byte for byte in listInput if byte != b'\x00']
	ret = b''.join(filtered_bytes).decode('utf-8')
	return ret

def policeLocation(latitude, longitude, apikey):
	url = 'https://maps.googleapis.com/maps/api/place/findplacefromtext/json'
	params = {
		"fields": "formatted_address,name,geometry,place_id",
		"input": "police",
		"inputtype": "textquery",
		"locationbias": f"circle:2000@{latitude}, {longitude}",
		"key": apikey
	}
	response = requests.get(url, params=params)
	data = response.json()
	if data['status'] == 'OK' and data['candidates']:
		place_id = data['candidates'][0].get('place_id')
	return place_id

def policeDetails(placeid, apikey):
	url2 = 'https://maps.googleapis.com/maps/api/place/details/json'
	params2 = {
		"fields": "name,formatted_phone_number",
		"place_id": placeid,
		"key": apikey
	}
	response2 = requests.get(url2, params=params2)
	data2 = response2.json()
	if data2['status'] == 'OK':
		phone = data2['result'].get('formatted_phone_number')
		name = data2['result'].get('name')
	return phone, name

def numFormat(phoneNumber):
	formattedNum = "+1"
	if phoneNumber != None:
		for x in list(phoneNumber):
			if x.isdigit():
				formattedNum += x
	return formattedNum

def newClient(clientsocket, port):

	maxCallTime = 60
	
	client = MongoClient(MONGODB_URI, tlsInsecure=True)
	db = client[DB_NAME]

	namesend, receivedsend, stationID, stationNum, stationName, numsend = None, [], None, None, None, None

	alertMsgRcvd = False
	while not alertMsgRcvd:
		data = clientsocket.recv(1024)
		if not data:
			break

		alertMsgRcvd = True
			
		s = struct.unpack("I128cff", data[0:140])
		name = s[1: 129]
		lat = float(s[129])
		log = float(s[130])
		received = " "
		if (s[0] - 140 > 0):
			received = struct.unpack(f"{s[0] - 140}c", data[140:])
		namesend = listConvert(name)
		receivedsend.append(listConvert(received))
		stationID = policeLocation(lat, log, apikey)
		stationNum, stationName = policeDetails(stationID, apikey)
		numsend = numFormat(stationNum)

	mngr = mp.Manager()

	outboundLock = threading.Lock()
	outboundMsg = mngr.list([]) 

	inboundLock = threading.Lock()
	inboundMsg = mngr.list([])


	outboundMsg.append(f"Emergency Call from Alert App: Name is {namesend} Location: {lat} latitude and {log} longitude. Communicate with me and messaged will be transcribed to user")

	print(f"Received message from {namesend}: ")

	defaultNumber = "+15733032511"

	# while db_lock.locked():
	# 	time.sleep(0.001)
	# with db_lock:
	# 	collection = db[COLLECTION_NAME]
	# 	messageData = {
	# 		"Name: ": namesend,
	# 		"Latitude: ": lat,
	# 		"Longitude: ": log,
	# 		"Alert Message: ": receivedsend,
	# 		"Nearest Station Name: ": stationName,
	# 		"Nearest Station Phone Number: ": numsend
	# 	}
	# 	print(f"Stuck in collection insertion")
	# 	collection.insert_one(messageData)
	# 	print("Data in MongoDB")

	# sleep(1)


	callThread = threading.Thread(target=Call, args=(defaultNumber, outboundMsg, inboundMsg, outboundLock, inboundLock, port, maxCallTime))
	callThread.start()

	init_time = perf_counter()
	while perf_counter() - init_time < maxCallTime:
		data = clientsocket.recv(1024)
		
		if data:
			s = struct.unpack("I128cff", data[0:140])
			received = " "
			if (s[0] - 140 > 0):
				received = struct.unpack(f"{s[0] - 140}c", data[140:])
			namesend = listConvert(name)
			received = listConvert(received)
			receivedsend.append(received)

			while outboundLock.locked():
				sleep(0.001)
			with outboundLock:
				outboundMsg.append(received)
				print(f"Main Thread Outbound Msgs:\n{outboundMsg}")

			#print(f'Arrived at inbound')
			rcvdMessage = None
			if len(inboundMsg) > 0:
				while inboundLock.locked():
					sleep(0.001)
				with inboundLock:
					rcvdMessage = ''.join([i for i in inboundMsg])
					inboundMsg[:] = []

			if (rcvdMessage != None):
				receivedsend.append(rcvdMessage)
				print(f"Main Thread Cur Inbound Msg:\n{rcvdMessage}")

			sleep(2)
	
	clientsocket.close()

	while db_lock.locked():
		time.sleep(0.001)
	with db_lock:
		collection = db[COLLECTION_NAME]
		messageData = {
			"Name: ": namesend,
			"Latitude: ": lat,
			"Longitude: ": log,
			"Alert Message: ": receivedsend,
			"Nearest Station Name: ": stationName,
			"Nearest Station Phone Number: ": numsend
		}
		print(f"Stuck in collection insertion")
		collection.insert_one(messageData)
		print("Data in MongoDB")


def startServer():

	portList = [ i for i in range(4950, 4980)]

	serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serverSocket.bind(('localhost', 4760))
	serverSocket.listen(5)
	print("Server started. Waiting for connections...")

	while True:
		clientsocket, clientaddress = serverSocket.accept()
		print(f"Connection from {clientaddress} established.")

		clientThread = threading.Thread(target=newClient, args = (clientsocket,portList.pop(0)))
		clientThread.start()
		print("Client Thread Started")


if __name__ == "__main__":
	startServer()

