from call.Call import *
import multiprocessing as mp 
import threading
from time import sleep, perf_counter


def main():
    mngr = mp.Manager()
    
    inboundLock = threading.Lock()
    inboundMsgs = mngr.list([])

    outboundLock = threading.Lock()
    outboundMsgs = mngr.list([])

    callThrd = threading.Thread(target=Call, args=["+15733032511", outboundMsgs, inboundMsgs, outboundLock, inboundLock])
    callThrd.start()

    maxThrdTime = 70
    initTime = perf_counter()

    msgCntr = 0

    while perf_counter() - initTime < maxThrdTime:
        while outboundLock.locked():
            sleep(0.001)
        with outboundLock:
            print(f"Main Thread Outbound Msgs:\n{outboundMsgs}")
            outboundMsgs.append(f"Message Number {msgCntr}")
            msgCntr += 1

        while inboundLock.locked():
            sleep(0.001)
        with inboundLock:
            rcvdMessage = ''.join([i for i in inboundMsgs])
            inboundMsgs[:] = []
        
        print(f"Main Thread Cur Inbound Msg:\n{rcvdMessage}")
            

        sleep(2)
    
if __name__ == "__main__":
    main()

