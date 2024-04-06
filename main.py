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

def newClient(clientsocket):
	client = MongoClient(MONGODB_URI)
	db = client[DB_NAME]
	while True:
		data = clientsocket.recv(1024)
		if not data:
			break
		s = struct.unpack("I128cff", data[0:140])
		name = s[1: 129]
		lat = float(s[129])
		log = float(s[130])
		received = " "
		if (s[0] - 140 > 0):
			received = struct.unpack(f"{s[0] - 140}c", data[140:])
		namesend = listConvert(name)
		receivedsend = listConvert(received)
		stationID = policeLocation(lat, log, apikey)
		stationNum, stationName = policeDetails(stationID, apikey)
		numsend = numFormat(stationNum)

		outboundLock = threading.Lock()
		outboundMsg = 
		
		inboundLock = threading.Lock()
		inboundMsg = 


		inboundMsg = f"Emergency Call from Alert App: Name is {namesend} Location: {lat} latitude and {log} longitude. Communicate with me and messaged will be transcribed to user"

		print(f"Received message from {namesend}: ")
		callThread = threading.Thread(target=Call, args=(numsend, inboundMsg, outboundMsg, inboundLock, outboundLock))
		callThread.start()

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
			collection.insert_one(messageData)
			print("Data in MongoDB")

	clientsocket.close()

def startServer():
	serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serverSocket.bind(('localhost', 9999))
	serverSocket.listen(5)
	print("Server started. Waiting for connections...")

	while True:
		clientsocket, clientaddress = serverSocket.accept()
		print(f"Connection from {clientaddress} established.")

		clientThread = threading.Thread(target=newClient, args = (clientsocket,))
		clientThread.start()
		print("Client Thread Started")


if __name__ == "__main__":
	startServer()

