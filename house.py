import socket
from Crypto.PublicKey import RSA
from Crypto import Random
import os
import sys
import threading

encrypt_str = "encrypted_message="
num_clients = 0

# Thread class
class ClientThread(threading.Thread):
    def __init__ (self, c, addr):
        self.c = c
        self.addr = addr
        threading.Thread.__init__(self)

    def run(self):
        #Generate private and public keys
        random_generator = Random.new().read
        private_key = RSA.generate(1024, random_generator)
        public_key = private_key.publickey()

        while True:
            #Wait until data is received.
            data = self.c.recv(1024)
            data = data.replace("\r\n", '') #remove new line character

            if data == "Client: OK":
                self.c.send("public_key=" + public_key.exportKey() + "\n")
                print "Public key sent to client."
                #num_clients += 1
                #print "Number of clients: "+str(num_clients)

            elif encrypt_str in data: #Receive encrypted message and decrypt it.
                data = data.replace(encrypt_str, '')
                print "Received:\nEncrypted message = "+str(data)
                encrypted = eval(data)
                decrypted = private_key.decrypt(encrypted)
                self.c.send("Server: OK")
                print "Decrypted message = " + decrypted

                if decrypted == "number":
                    print str(num_clients)

            #elif data == "Quit":
                #num_clients -= 1
                #if num_clients <= 0: break

def Main():
    #Declartion
    mysocket = socket.socket()
    #host = socket.gethostbyname(socket.getfqdn())
    host = "localhost"
    port = 7777

    if host == "127.0.1.1":
        import commands
        host = commands.getoutput("hostname -I")
    print "host = " + host

    #Prevent socket.error: [Errno 98] Address already in use
    mysocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    mysocket.bind((host, port))

    mysocket.listen(5)

    while True:
        # establish connection with client
        c, addr = mysocket.accept()
        # start a new thread and return its identifier
        ClientThread(c, addr).start()

    #Server to stop
    c.send("Server stopped\n")
    print "Server stopped"
    c.close()

if __name__ == '__main__':
    Main()
