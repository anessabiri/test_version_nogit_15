import multiprocessing as mp
import ssl
import pathlib
import websockets
import traceback
import asyncio
import logging
import random
import queue
import time
import json
import copy
import certifi
import sys
import os

from queue import Queue

class WebSocketServer(mp.Process):

    def __init__(self, stop_event, event_message_queue, command_message_queue, local_ip_address, local_port):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.stop_event = stop_event
        self.event_message_queue = event_message_queue
        self.command_message_queue = command_message_queue
        self.local_ip_address = local_ip_address
        self.local_port = local_port
        self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.localhost_pem = "/workspace/.cert/cert.pem"
        self.key_pem = "/workspace/.cert/key.pem"
        self.password_cert = "r3l41cv4t"
        self.ssl_context.load_cert_chain(self.localhost_pem, keyfile=self.key_pem, password=self.password_cert)
        self.webSocketClientData = {}
        self.latest_export_state = {}
        self.ref_set = set()
        
    async def __msgLoop(self):
        while not self.stop_event.is_set():               
            try:
                msg = self.event_message_queue.get_nowait()                
            except queue.Empty:                
                await asyncio.sleep(.01)
            else:
                try:
                    if "ExportStateUpdate" in  msg:
                        if msg["ExportStateUpdate"]["category"] == "hide":
                            if msg['user'] in self.latest_export_state:
                                del self.latest_export_state[msg['user']]
                        else:
                            self.latest_export_state[msg['user']] = msg
                            if msg['user'] in self.webSocketClientData: #check if user is still connected
                                self.webSocketClientData[msg['user']]['msgQueue'].put(msg)
                    elif "SendLastState" in msg:
                        if msg['user'] in self.latest_export_state:
                            msg = self.latest_export_state[msg['user']]
                            if msg['user'] in self.webSocketClientData: #check if user is still connected
                                self.webSocketClientData[msg['user']]['msgQueue'].put(msg)           
                    else:            
                        if msg['user'] in self.webSocketClientData: #check if user is still connected
                            self.webSocketClientData[msg['user']]['msgQueue'].put(msg)

                except:
                    self.logger.error("Exception : ")
                    self.logger.error(traceback.format_exc())
                    #TODO: watchdog alert escalation !

        self.logger.warning('Exited msgloop')
        

    async def __recv(self, websocket):
        msg = await websocket.recv()
        msg = json.loads(msg)
        self.logger.warning("<<< " + str(msg["commandType"])[0:50])

        self.command_message_queue.put(msg)


    async def __handler(self, websocket, path):
        msg = await websocket.recv()
        if websocket.remote_address[0] in self.ref_set:
            self.logger.warning('WebSocketServer unwelcomed peer tried to reconnect %s', str(websocket.remote_address[0]))
            return
        if not "hello" in msg:
            self.ref_set.add(websocket.remote_address[0])
            return

        try:
            self.logger.debug(msg)
            msg = json.loads(msg)
        except Exception as e:
            self.ref_set.add(websocket.remote_address[0])
            return
        if type(msg) is not dict:
            self.ref_set.add(websocket.remote_address[0])
            return
        if "code" not in msg:
            self.ref_set.add(websocket.remote_address[0])
            return
        elif msg["code"] != "s3c7r3r3l414cc3ss":
            self.ref_set.add(websocket.remote_address[0])
            return
        if "user" not in msg:
            self.ref_set.add(websocket.remote_address[0])
            return
        client_user_cvat = msg["user"]
          
        self.webSocketClientData[client_user_cvat] = {'msgQueue': Queue()}
        self.command_message_queue.put({"clientConnected" : client_user_cvat})

        self.logger.warning('WebSocketServer hello %s', str(client_user_cvat))
        self.logger.warning('Connected to %s', str(websocket.remote_address))
        
        remote_address = websocket.remote_address #NOT working with nginx


        #Now that client session is registered, open our session for video call

        while not self.stop_event.is_set():

            #try to pump message queue and send message to clients
            try:
                msg = self.webSocketClientData[client_user_cvat]['msgQueue'].get_nowait()
                self.logger.warning(">>> " + str(msg)[0:50])
            except queue.Empty:
                pass #nothing to do
            else:                
                try:
                    self.logger.debug("---> ws send to %s > %s", str(client_user_cvat), json.dumps(msg)[0:200])
                    await websocket.send(json.dumps(msg))
                except websockets.exceptions.ConnectionClosed:
                    self.logger.warning('ConnectionClosed (1) for user %s', str(client_user_cvat))
                    break

            #try to receive command from client
            try:
                #https://www.programcreek.com/python/example/81576/asyncio.wait_for
               # if not peer_status is None:
               #     self.logger.warning(client_uuid + " status: "+peer_status)
                await asyncio.wait_for(self.__recv(websocket), timeout=0.010) 
            except asyncio.TimeoutError:
                pass #nothing to read               
            except: # #Alex: except all: key error or websockets.exceptions.ConnectionClosed
                self.logger.warning('ConnectionClosed (2) for user : %s', str(client_user_cvat))
                break
           
            try:
                await asyncio.sleep(.010)
            except:
                pass
        
        # self.command_message_queue.put({"clientDisconnected": [remote_address, client_user_cvat]})

        #remove uuid from dictionary
        self.webSocketClientData.pop(client_user_cvat, None)

        self.logger.warning('WebSocketServer goodbye %s', str(client_user_cvat))


    def run(self):
        
        #if need to select local ip cards :
        #ip addr show | awk '/inet 192.168/{print substr($2, 0, index($2, "/")-1)}'
        #for the moment wait on all available ethernet cards
        start_server = websockets.serve(
            self.__handler, self.local_ip_address, self.local_port, ssl=self.ssl_context, max_size=5*1048576, ping_interval=None
        )
        self.logger.warning('WebSocketServer READY')

        try:
            asyncio.get_event_loop().run_until_complete(asyncio.wait([   
            self.__msgLoop(),
            start_server
            ]))
        finally:
            self.logger.warning('Websocket event loop terminated')