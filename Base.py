import json
import threading
import socket
from abc import abstractmethod
# the format in which encoding and decoding will occur
FORMAT = "utf-8"
BUFFER_SIZE = 2048

class Base():
    def __init__(self, serverhost='localhost', serverport=10000, listen_num=100):
        # host and listening port of network peers/central server
        hostname = socket.gethostname()   
        self.serverhost = socket.gethostbyname(hostname)  
        self.serverport = int(serverport)
        
        # create server TCP socket (for listening)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # bind the socket to our local address
        self.socket.bind((self.serverhost, self.serverport))
        self.socket.listen(listen_num)
        
        # peerlist: dict with key is peer name and value is tuple (host,port) 
        # Child class CentralServer: connected peers of a network peer
        # Child class NetworkPeer: list of registered peers managed by central server
        self.peerlist = {}
        # used for mapping from MESSAGE TYPE to corresponding function
        self.handlers = {}

    def add_handler(self, msgtype, function): 
        self.handlers[msgtype] = function

    def function_mapper(self, message):
        type_ = message['msgtype']
        data_ = message['msgdata']
        self.handlers[type_](data_)

    def recv_input_stream(self, conn):
        # receive from client 
        buf = conn.recv(BUFFER_SIZE)
        message = buf.decode(FORMAT)  
        # deserialize (json type -> python type)
        message = json.loads(message)
        # map into function
        self.function_mapper(message)

    def input_recv(self):
        while True:
            # wait until receive a connection request -> return socket for connection from client
            conn, addr = self.socket.accept()
            input_stream = threading.Thread(target=self.recv_input_stream, args=(conn,))
            input_stream.daemon = True
            input_stream.start()

    @abstractmethod
    def run(self):
        pass

    @staticmethod
    def client_send(address, msgtype, msgdata):
        # msgtype for mapping into corresponding function
        # msgdata contains sent data
        message = {'msgtype': msgtype, 'msgdata': msgdata}
        
        # serialize into JSON for transmitting over the network
        message = json.dumps(message).encode(FORMAT)

        # create client TCP socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        try:
            # set a timeout to avoid indefinite blocking
            s.settimeout(10)  # 10 seconds timeout
            # request connection
            s.connect(address)
            # send the message to the server
            s.sendall(message)
            return True

        except (ConnectionRefusedError, socket.error) as e:
            print(f"Connection Error: {e}")
            raise
        finally:
            s.close()  # Ensure the socket is always closed