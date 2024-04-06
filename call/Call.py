import audioop
import base64
import json
import os

from flask import Flask, request 
from flask_sock import Sock, ConnectionClosed
from twilio.twiml.voice_response import VoiceResponse, Start
from twilio.rest import Client
from pyngrok import ngrok, conf, installer

import multiprocessing as mp

import ssl

import vosk

import threading
from time import sleep, perf_counter

class Call:
    
    # inbound and outbound msgs are manager.list
    def __init__(self, outboundNumber: str, inboundMsgs, outboundMsgs, inboundLock, outboundLock, maxCallTime = 60):
        self.outboundNumber = outboundNumber

        self.app = Flask(__name__)
        self.sock = Sock(self.app)
        self.twilio_client = Client()
        self.model = vosk.Model("./call/voice-model")

        self.maxCallTime = maxCallTime

        self.inboundLock = inboundLock
        self.inboundMsgs = inboundMsgs
        self.outboundLock = outboundLock
        self.outboundMsgs = outboundMsgs

        self.app.add_url_rule('/call', "call", self.call, methods=["POST"])
        
        @self.sock.route('/stream')
        def stream(ws):

            CL = '\x1b[0K'
            BS = '\x08'

            rec = vosk.KaldiRecognizer(self.model, 16000)
            while True:
                message = ws.receive()
                packet = json.loads(message)
                if packet['event'] == 'start':
                    print("Streaming starting:")
                elif packet['event'] == 'stop':
                    print('\nStreaming has stopped')
                    ngrok.disconnect(self.public_url)
                    return

                elif packet['event'] == 'media':
                    audio = base64.b64decode(packet['media']['payload'])
                    audio = audioop.ulaw2lin(audio, 2)
                    audio = audioop.ratecv(audio, 2, 1, 8000, 16000, None)[0]
                    if (rec.AcceptWaveform(audio)):
                        r = json.loads(rec.Result())
                        #print(CL + r['text'] + ' ', end='', flush=True)
                        while self.outboundLock.locked():
                            sleep(0.001)
                        with self.outboundLock:
                            self.outboundMsgs.append(r['text'])
                    # else:
                    #     r = json.loads(rec.PartialResult())
                    #     print(CL + r['partial'] + BS * len(r['partial']), end='', flush=True)
                

        
        
        if not os.path.exists(conf.get_default().ngrok_path):
            myssl = ssl.create_default_context()
            myssl.check_hostname = False 
            myssl.verify_mode=ssl.CERT_NONE
            installer.install_ngrok(conf.get_default().ngrok_path, context=myssl)

        self.port = 4998
        self.public_url = ngrok.connect(self.port, bind_tls=True).public_url
    
        self.number = self.twilio_client.incoming_phone_numbers.list()[0]
        #self.number.update(voice_url=self.public_url + '/call')
        #print(f"Waiting for calls on {self.number.phone_number}")

        flskThrd = threading.Thread(target=self.flaskThread, args=[])
        flskThrd.start()
        sleep(5)
        self.call()
        
    def flaskThread(self):
        self.app.run(port=self.port)

    def call(self):
        print(f"Making outbound call to: {self.outboundNumber}")

        response = VoiceResponse()
        start = Start() 
        print(f'wss://{self.public_url[8:]}/stream')
        start.stream(url=f'wss://{self.public_url[8:]}/stream')
        response.append(start)
        response.say("Hello")
        response.pause(length=60)
        response = str(response)
        response = response[response.find('>') + 1:]
        print(response)
        call = self.twilio_client.calls.create(twiml=str(response),
                                               to=self.outboundNumber,
                                               from_=self.number.phone_number)
        
        sleep(10)
        initTime = perf_counter()
        while perf_counter() - initTime < self.maxCallTime:
            while self.inboundLock.locked():
                sleep(0.001)
            with self.inboundLock:
                if len(self.inboundMsgs) > 0:
                    msg = self.inboundMsgs.pop(0)

                    #print(f"Main Thread inbound Msgs:\n{self.inboundMsgs}")

                    response = VoiceResponse()
                    response.say(msg)
                    response.pause(length=60)
                    response = str(response)
                    response = response[response.find('>') + 1:]
                    print(call.sid)
                    call = self.twilio_client.calls(str(call.sid)).update(twiml=response)

            sleep(2)
                    
                    
        

        sleep(60)
    


        
