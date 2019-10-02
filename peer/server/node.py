import logging
from random import randint
import socket
import time
import threading


class Server:

    connections = list()
    peers = list()  # List of peers connected to the server. We broadcast this list out to sync our clients

    def __init__(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('127.0.0.1', 10001))
            s.listen(5)
            logging.info('Successfully started the server on port 10001.')

            while True:
                c, a = s.accept()
                logging.info('New client node joins pool.')
                t = threading.Thread(target=self.handler, args=(c, a), daemon=True).start()
                self.connections.append(c)
                self.peers.append(a[0])
                logging.info('New node connected: {}:{}'.format(str(a[0]), str(a[1])))
                self.send_peers()

    def handler(self, c, a):
        while True:
            data = c.recv(5120)

            logging.info('Broadcasting received data to all connected nodes: {}'.format(data.decode()))
            logging.info('Message: {}'.format(data.decode()))

            for connection in self.connections:
                connection.sendall(data)

            if not data:
                logging.info('Node disconnected: {}:{}'.format(str(a[0]), str(a[1])))
                self.connections.remove(c)
                self.peers.remove(a[0])
                c.close()
                self.send_peers()
                break

    def send_peers(self):
        """Sends the list of peers in the swarm to all connected peers.

        We prefix the message with '\x11' so the clients know it is a Routing Table refresh.
        """
        p = ''

        for peer in self.peers:
            p = p + peer + ','

        for connection in self.connections:
            connection.send(b'\x11' + p.encode())


class Client:
    def __init__(self, address):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.connect((address, 10001))

            t = threading.Thread(target=self.send_message, args=(s,), daemon=True).start()

            while True:
                data = s.recv(5120).decode()

                if not data:
                    break

                if data[0:1] == b'\x11':
                    # Message prefixed with \x11, so we know it is a new node message
                    self.update_peers(data[1:])
                else:
                    # Since the message received isn't prefixed with \x11, we know it is a message
                    logging.info('Received message: {}'.format(data))

    @staticmethod
    def send_message(s):
        """Sends a message to all connected nodes."""
        while True:
            s.sendall(input('Enter message: ').encode())

    @staticmethod
    def update_peers(peer_data):
        """Refreshes the local copy of all connected nodes."""
        Tracker.peers = peer_data.split(',')[:-1]


class Tracker:
    """Tracks the Peers connected within the swarm.

    This is a separate class due to data accessibility. We want to be able to access the peers list
    from outside the Client and Server classes.
    """
    peers = ['178.62.80.42']


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                        level=logging.INFO,
                        datefmt='%Y-%m-%d %H:%M:%S')

    while True:
        time.sleep(randint(1, 5))  # One node will become a server randomly
        for peer in Tracker.peers:
            #try:
            #    server = Server()
            #except:
            #    pass  # Server is already started. Becoming a client node

            client = Client(peer)
