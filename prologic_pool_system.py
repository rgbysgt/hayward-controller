#Copyright Jonathan Watkins (c) 2017
#All rights reserved

#prologic_pool_system
#RS485 Protocol Bridge

import serial
import threading
import time
import datetime
import re
from collections import deque

class ProLogicParser:
    def __init__(self):
        self.lastbyte = 0x00
        self.data = []
        self.DLE = b'\x10'
        self.STX = b'\x02'
        self.ETX = b'\x03'
        self.isStarted = False
      
    def parse(self, byte):
        #start = DLE-STX   end=DLE-ETX
        if(self.lastbyte == self.DLE and byte == self.STX):
            #start sequence
            self._startFrame()
            #reappend last byte to get full frame
            self.data.append(self.lastbyte)
            self.lastbyte = byte
            self.data.append(byte)
        elif(self.isStarted and self.lastbyte == self.DLE and byte == self.ETX):
            #end sequence
            self.lastbyte = byte
            self.data.append(byte)
            self._endFrame()

            #return full message payload
            r = ProLogicMessage()
            r.parseFrame(self.data)
            return r
        else:
            self.lastbyte = byte
            self.data.append(byte)

        #return incomplete message payload
        b = ProLogicMessage()
        return b

    def _startFrame(self):
        #purge any lingering data buffer
        self.data.clear()
        self.datalen = 0
        self.isStarted = True
        
    def _endFrame(self):
        self.isStarted = False
        

class ProLogicMessage:
    def __init__(self):
        self.data = []
        self.datalen = 0
        self.messageType = ""
        self.is_complete = False
        self.message = None

    def parseFrame(self, data):
        #min len = ??
        #first two bytes determine message type
        #  0x00 0x03 == Key Press Release
        #  0x01 0x01 == ClientQuery
        #  0x01 0x02 == Update LED
        #  0x01 0x03 == Update Display

        #need to strip out null 0x00 bytes
        #need to replace 0xDF with 0xB0 on Update Display messages (placeholder for degree character)
        self.data = data
        self.datalen = len(data)

        #min len is 2 frame start bytes + 2 message types bytes + x data + 2 checksum bytes + 2 end frame bytes
        #min length is 8 assuming null messages
        if(self.datalen < 8):
            return

        # get message type from bytes 3 & 4
        if(self.data[2] == b'\x00' and self.data[3] == b'\x03'):
            self.messageType = "KeyPressRelease"
        elif(self.data[2] == b'\x01' and self.data[3] == b'\x01'):
            self.messageType = "ClientQuery"
        elif(self.data[2] == b'\x01' and self.data[3] == b'\x02'):
            self.messageType = "UpdateLED"
            self.message = ProLogicLEDStatus(self.data)
        elif(self.data[2] == b'\x01' and self.data[3] == b'\x03'):
            self.messageType = "UpdateDisplay"
            self.message = ProLogicDisplayStatus(self.data)
        else:
            self.messageType = "Unknown"

        #todo parse and verify checksum

        self.is_complete=True
        

    def isComplete(self):
        return self.is_complete

    def getMessageType(self):
        return self.messageType

    def getMessage(self):
        return self.message

    def printSelf(self):
        print("[message] type=", self.messageType, end='')
        if(self.messageType == "UpdateLED"):
            print("") #force new line
            self.message.printSelf()
        elif(self.messageType == "UpdateDisplay"):
            print(" :: ", self.message.DisplayText)
        else:
            print(" data=", self.data)

class ProLogicDisplayStatus:
    DisplayText = ""
    def __init__(self, data):        
        #parse data
        self.data = data
        #expect at least 1 data bit
        if(len(data) < 9):
            return
        
        mdata = data[4:len(data)-4] #slice out message data
        #remove null bits
        while(True):
            try:
                mdata.remove(b'\x00')
            except:
                break
            
        #replace xDF with XB0 (degree character)
        while(mdata.count(b'\xDF')>0):
            mdata[mdata.index(b'\xDF')]=b'\xB0'

        #parse message bytes via UTF7 into DisplayText (however python can't take in a list of bytes, it needs a list of integers...)
        mlen = len(mdata)
        ba = bytearray(mlen)
        for i in range(mlen):
            ba[i] = int.from_bytes(mdata[i], byteorder='little')
        self.DisplayText = ba.decode("latin1")

class ProLogicLEDStatus:
    Aux1 = False
    Aux2 = False
    Aux3 = False
    Aux4 = False
    Aux5 = False
    Aux6 = False
    Aux7 = False
    Aux8 = False
    Aux9 = False
    Aux10 = False
    Aux11 = False
    Aux12 = False
    Aux13 = False
    Aux14 = False
    CheckSystem = False
    Filter = False
    Heater1 = False
    Lights = False
    Pool = False
    Service = False
    Spa = False
    Spillover = False
    SuperChlorinate = False
    SystemOff = False
    Valve3 = False
    Valve4_Heater2 = False
        
    def __init__(self, data):
        #parse data
        self.data = data

        #there are 4 data bytes expected; therefore min len should be 12 for a full frame (8 base bytes + 4 data)
        if(len(data)<12):
            return

        #read data byte 1 @ index 4
        b = int.from_bytes(data[4], byteorder='little')
        self.Heater1 = bool(b & 0x01)
        self.Valve3 = bool(b & 0x02)
        self.CheckSystem = bool(b & 0x04)
        self.Pool = bool(b & 0x08)
        self.Spa = bool(b & 0x10)
        self.Filter = bool(b & 0x20)
        self.Lights = bool(b & 0x40)
        self.Aux1 = bool(b & 0x80)

        #read data byte 2 @ index 5
        b = int.from_bytes(data[5], byteorder='little')
        self.Aux2 = bool(b & 0x01)
        self.Service = bool(b & 0x02)
        self.Aux3 = bool(b & 0x04)
        self.Aux4 = bool(b & 0x08)
        self.Aux5 = bool(b & 0x10)
        self.Aux6 = bool(b & 0x20)
        self.Valve4_Heater2 = bool(b & 0x40)
        self.Spillover = bool(b & 0x80)
        
        #read data byte 3 @ index 6
        b = int.from_bytes(data[6], byteorder='little')
        self.SystemOff = bool(b & 0x01)
        self.Aux7 = bool(b & 0x02)
        self.Aux8 = bool(b & 0x04)
        self.Aux9 = bool(b & 0x08)
        self.Aux10 = bool(b & 0x10)
        self.Aux11 = bool(b & 0x20)
        self.Aux12 = bool(b & 0x40)
        self.Aux13 = bool(b & 0x80)

        #read data byte 4 @ index 7
        b=int.from_bytes(data[7], byteorder='little')
        self.Aux14 = bool(b & 0x01)
        self.SuperChlorinate = bool(b & 0x02)

    def printSelf(self):
        print("SysOff  ChkSys  Pool   Filtr  Servc   Light")
        print(self.SystemOff, self.CheckSystem, self.Pool, self.Filter, self.Service, self.Lights, sep="   ")
        



class ProLogicSystem:
    def __init__(self, port, message_callback, status_callback):
        self.port = port
        self.is_started=False
        self.message_callback = message_callback
        self.status_callback = status_callback
        self._bgthread = threading.Thread(target=self._listen, daemon=True)
        self._bgthreadendevent = threading.Event()
        self._parser = ProLogicParser()
        self._pool_status = { "messages": PoolStatusMessagesQueue() }
        self._listenLock = threading.Lock()
        self._kqLock = threading.Lock()
        self._kq = deque()

    def start(self):
        if(self.is_started):
            raise SystemAlreadyStarted

        self.is_started=True
        try:
            print("ProLogicPoolSystem - Starting - BG Worker Starting...")
            self._bgthreadendevent.clear()
            self._bgthread.start()            
        except:
            print("prologic: Error starting background thread ", sys.exc_info()[0])
        

    def end(self):
        if(not self.is_started):
            return
        try:            
            print("ProLogicPoolSystem - Ending...")

            self._bgthreadendevent.set() #trigger the bg thread to close
            print("ProLogicPoolSystem - Ending - BG Worker End Event Set")
            self._bgthread.join() #join the thread to wait for it to end
            print("ProLogicPoolSystem - Ending - BG Worker Ended")
        finally:
            self.is_started=False

    def restart(self):
        self.end()
        time.sleep(1)        
        self.start()

    def getStatus(self):
        if(self.is_started==False):
            return { "error": "Pool System is not started" }
        #print("Get Status=",self._pool_status)
        return self._pool_status

    def pressKey_Lights(self):
        print("ProLogicSystem - Send KeyPress: Lights")
        self._queueKey([0,1], [0,23])

    def pressKey_Filter(self):        
        print("ProLogicSystem - Send KeyPress: Filter")
        self._queueKey([128,0], [1, 15])

    def _queueKey(self, key, checksum):
        with self._kqLock:
            #format into byte array... 
            v = bytearray([16,2,0,3,key[0],key[1],key[0],key[1],checksum[0],checksum[1],16,3])
            self._kq.append(v);

    def _listen(self):
        tself = threading.local()
        tself._parser = ProLogicParser()
        print("ProLogicPoolSystem - Starting - BG Worker Started")
        with self._listenLock:

            try:
                print("ProLogicPoolSystem - BG Worker - Port Opening...")
                tself._serial = serial.Serial(self.port, baudrate=19200, timeout=None, exclusive=True)
                tself._serial.flushInput()
                print("ProLogicPoolSystem - BG Worker - Port Opened")
            except:
                print("prologic: Error opening port")
                self.is_started=False
                raise

            try:
                tself.cq_index = 0
                tself.cq_check = [b'\x10', b'\x02', b'\x01', b'\x01', b'\x00', b'\x14', b'\x10', b'\x03']                
                
                while not self._bgthreadendevent.is_set():
                    if(True): #tself._serial.inWaiting() > 0): #don't bother checking? how much of an issue is this? and does it speed this process up to not check?
                        tself.recb = tself._serial.read() #need to add faster checks for clientquery
                        
                        if(tself.recb == tself.cq_check[tself.cq_index]):
                            #print("cq-index=", tself.cq_index)
                            if(tself.cq_index == 7):
                                #we have a client query request!
                                #print("CQ!")
                                tself.cq_index = 0 #reset index
                                with self._kqLock:
                                    if(len(self._kq) > 0):
                                        try:
                                            k = self._kq.popleft()
                                            tself._serial.write(k)
                                            tself._serial.flush()
                                            print("DEBUG write to port: ", k)
                                        except Error as e:
                                            print("ProLogicSystem :: Error trying to write key to port {}".format(e))                                            

                            else:
                                tself.cq_index = tself.cq_index + 1
                        else:
                            tself.cq_index = 0
                            
                        tself.m = tself._parser.parse(tself.recb)
                        if(tself.m.isComplete()):
                            if(tself.m.getMessageType() == "ClientQuery"):
                                pass
                            
                            elif(tself.m.getMessageType() == "UpdateLED"):
                                self._parseLED(tself.m)
                                
                            elif(tself.m.getMessageType() == "UpdateDisplay"):
                                self._parseDisplay(tself.m)
            except:
                print("ProLogicPoolSystem - BG Worker - Error reading serial data")
                self.is_started=False
                raise
            finally:
                print("ProLogicPoolSystem - Ending - BG Worker - Loop Exit")
                tself._serial.close()
                print("ProLogicPoolSystem - Ending - BG Worker - Port Closed.")
                #reset parser to avoid any cache issues upon restart
                

    def _parseDisplay(self, msg):
        #  DDDD  HH:SS   (sometimes wo colon aka blinking)
        #  Air Temp  000\xDF[F/C]
        #  Pool Temp  000\xDF[F/C]
        #  Salt Level  0000PPM
        #  Lights On/Off???
        #  No Flow detected???
        #  Too cold???
        
        t = msg.message.DisplayText.strip()
        p = False
        #print("DEBUG: parsing display update ", t)
        
        if(t.startswith("Air Temp")):
           t = t[8:].strip() #now should just be 000\xDF[F/C]
           u = t[-1] #get just the unit character
           t = t[:len(t)-2] #now just the temp w/o the suffix
           self._pool_status["air_temp"] = { "value": int(t), "unit": u, "last_updated": datetime.datetime.now() }
           p = True

        if(t.startswith("Pool Temp")):
           t = t[9:].strip() #now should just be 000\xDF[F/C]
           u = t[-1] #get just the unit character
           t = t[:len(t)-2] #now just the temp w/o the suffix
           self._pool_status["pool_temp"] = { "value": int(t), "unit": u, "last_updated": datetime.datetime.now() }
           p = True

        if(t.startswith("Salt Level")):
           t = t[10:].strip() #now should just be 0000PPM
           self._pool_status["salt_level"] = { "value": t, "last_updated": datetime.datetime.now() }
           p = True

        if(t.startswith("Pool Chlorinator")):
           t = t[16:].strip() #now should just be xx%
           self._pool_status["pool_chlorinator"] = { "value": t, "last_updated": datetime.datetime.now() }
           p = True

        if(p == False):
           #check for date format and ignore those w/o the colon
           #example: Saturday              6:36P
           if(re.match("^[A-Za-z]{3,6}day", t)):
               #date/time message, ensure the colon is present to avoid duplicate time entries
               t= t[:-4] + ":" + t[-3:]
               self._pool_status["messages"].enqueue(t, 25)
           else:
               self._pool_status["messages"].enqueue(t)
           


    def _parseLED(self, msg):
        self._pool_status["led"] = msg.message

class PoolStatusMessagesQueue:
    def __init__(self):
        self._queue = []
        self._queueLock = threading.Lock()

    def indexOf(self, msg):
        for index in range(len(self._queue)):
            if(self._queue[index]["message"] == msg):
                return index
        return -1
    
    def enqueue(self, msg, expirySeconds=40):
        #need to check if there's a duplicate message and just extend the expiry vs reinsert
        with self._queueLock:
            expiry = (datetime.datetime.now() + datetime.timedelta(seconds=expirySeconds))
            i = self.indexOf(msg)
            if(i > -1):
                self._queue[i]["expiry"] = expiry
            else:
                self._queue.append( { "message": msg, "expiry": expiry } )
        self.flush()

    def flush(self):
        #clear out those messages that have expired
        with self._queueLock:
            expired = []
            for index in range(len(self._queue)-1, -1, -1):
                if(self._queue[index]["expiry"] < datetime.datetime.now()):
                    expired.append(index)

            for di in range(len(expired)):
                self._queue.pop(di)

    def to_array(self):
        #print("mq.to_array()[unflushed]: ", self._queue)
        self.flush()
        with self._queueLock:
            r = []
            for x in self._queue:
                r.append(x["message"])
            return r
        

class MessageThread(threading.Thread):
    def __init__(self, system, cancel_event):
        threading.Thread.__init__(self)
        self.pl_system = system
        self.cancel = cancel_event

    def run(self):
        while not self.cancel.wait(timeout=0.1):
            #listen for data from port and raise events when full frames are found
            if(self.pl_system.is_started):
                in_waiting = self.pl_system.serial.in_waiting
                if(in_waiting > 0):
                    port_data = self.pl_system.serial.read(in_waiting)



#exceptions
class SystemAlreadyStarted(Exception):
    pass
