import asyncio
import json
import os
import queue
import ssl
import pathlib

import websockets
import socket
import multiprocessing as mp
from queue import Queue
import logging


class WebSocketClient(mp.Process):
    def __init__(self, server_ip_address, server_port, event_msg_queue, command_msg_queue):
        super().__init__()
        self.logger = logging.getLogger(__name__)

        self.is_client_running = True
        self.event_msg_queue = event_msg_queue
        self.command_msg_queue = command_msg_queue
        self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        self.localhost_pem = "/workspace/.cert/cert.pem"
        self.ssl_context.load_verify_locations(self.localhost_pem)
        self.server_uri = "wss://"+server_ip_address+":"+str(server_port)
        self.server_ip_address = server_ip_address
        self.status = "disconnected"
        self.waiting_for_new_token = False
    
    def set_access_route(self, server_ip_address, server_port, username):
        self.server_ip_address = server_ip_address
        self.server_port = server_port
        self.server_username = username
        self.server_uri = "wss://"+server_ip_address+":"+str(server_port)

    async def __recv(self, websocket):
        msg = await websocket.recv()
        self.logger.warning("<<<<<<<< " + msg[0:50])
        msg = json.loads(msg)
        self.event_msg_queue.put(msg)

    async def hello(self):
    
        while self.is_client_running:

            try:

                #print("Connecting "+self.server_uri)
                self.logger.warning("Connecting "+self.server_uri)
                async with websockets.connect(self.server_uri, ssl=self.ssl_context, max_size= 5 ** 20, ping_interval=None) as websocket:

                    msg = json.dumps({"WebSocketClient" : "hello", "user" : self.server_username, "code" : "s3c7r3r3l414cc3ss"})
                    #print(">>>>>>>> " + msg)
                    self.logger.warning(">>>>>>>> " + msg)

                    await websocket.send(msg)

                    # greeting = await websocket.recv()

                    # #TODO go back to login only
                    # greeting_data = json.loads(greeting)

                    # print("<<<<<<<< " + greeting)
                    # self.event_msg_queue.put(json.dumps({"func":"connectionState", "connected":True}))
    
                    while True:
    
                        if not self.is_client_running:
                            self.logger.warning('Stopping WebSocketClient')
                            #print('Stopping WebSocketClient')
                            break 
                                               
                        if self.status == "disconnected":
                            self.status = "connected"
                        #try to receive event from server
                        try:                        #https://www.programcreek.com/python/example/81576/asyncio.wait_for
                            #print("await recv")
                            await asyncio.wait_for(self.__recv(websocket), timeout=0.010)
                        except websockets.exceptions.ConnectionClosed:
                            #print('WebSocketClient ConnectionClosed')
                            self.logger.warning("WebSocketClient ConnectionClosed")
                            self.event_msg_queue.put(json.dumps({"func":"_connectionState", "connected":False}))
                            break
                        except asyncio.TimeoutError:
                            pass #nothing to read
    
                        #try to send command
                        try:
                            #print("try get from queue")
                            msg = self.command_msg_queue.get_nowait()
                        except queue.Empty:
                            pass                         
                        else:
                            try:
                                msg['user'] = self.server_username
                                msg = json.dumps(msg)
                                self.logger.warning(">>>>>>>> " + msg)

                                #print(">>>>>>>> " + msg)
                                await websocket.send(msg)             
                            except websockets.exceptions.ConnectionClosed:
                                self.logger.warning("WebSocketClient ConnectionClosed")

                                #print('WebSocketClient ConnectionClosed')
                                self.event_msg_queue.put(json.dumps({"func":"_connectionState", "connected":False}))
                                break
                        #print("done")

            except Exception as e: # ConnectionRefusedError:
                if e == ConnectionRefusedError:
                    #print('WebSocketClient failed to connect ' + self.server_uri)
                    self.logger.warning('WebSocketClient failed to connect ' + self.server_uri)

                    if self.status == "connected":
                        self.status = "disconnected"
                    await asyncio.sleep(3) #retry after 3 secs
                else:
                    self.logger.warning(e)
                    #print(e)
                    #print("WebSocketClient connection closed")
                    self.logger.warning("WebSocketClient connection closed")

                    if self.status == "connected":
                        self.status = "disconnected"
                        self.event_msg_queue.put(json.dumps({"func":"_connectionState", "connected":False}))
                    await asyncio.sleep(5) #retry after 5 secs
        self.logger.warning('Websocket closed.')

    def run(self):    
        # asyncio.get_event_loop().run_until_complete(self.hello())
        loop = asyncio.new_event_loop().run_until_complete(self.hello())
        asyncio.set_event_loop(loop)
        self.logger.warning('Websocket async loop exited.')
        #print('Websocket async loop exited.')
