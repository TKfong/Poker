import socket
from Crypto.PublicKey import RSA
import getpass
import bcrypt

class Server():
    def __init__(self, server, server_string, server_pubkey):
        self.server = server
        self.server_string = server_string
        self.server_pubkey = server_pubkey

def connect():
    server = socket.socket()
    #host = "10.0.2.15"
    host = "localhost"
    port = 7777

    server.connect((host, port))

    #Tell server that connection is OK
    server.sendall("Client: OK")

    #Receive public key string from server
    server_string = server.recv(1024)

    #Remove extra characters
    server_string = server_string.replace("public_key=", '')
    server_string = server_string.replace("\r\n", '')

    #Convert string to key
    server_public_key = RSA.importKey(server_string)
    #demo()
    # TODO check if server/connection is valid
    return Server(server, server_string, server_public_key)

def message(msg, s):
    #msg = raw_input("Enter secret message: ")
    #type(msg)
    server = s.server
    server_pubkey = s.server_pubkey

    encrypted = server_pubkey.encrypt(msg, 32)
    server.sendall("encrypted_message="+str(encrypted))

    #TODO Tell server to finish connection
    if msg == "quit":
        return

    #Server's response
    rsp = server.recv(1024)
    rsp = rsp.replace("\r\n", '')
    if rsp != "Server: OK":
        print("SHIT")

def connect_demo():
    while True:
        #Encrypt message and send to server
        message = raw_input("Enter secret message: ")
        type(message)
        encrypted = server_public_key.encrypt(message, 32)
        server.sendall("encrypted_message="+str(encrypted))

        #Tell server to finish connection
        if message == "quit":
            break

        #Server's response
        server_response = server.recv(1024)
        server_response = server_response.replace("\r\n", '')
        if server_response == "Server: OK":
            print("Server decrypted message successfully")

    server.sendall("Quit")
    print(server.recv(1024)) #Quit server response
    server.close()

def login(server):
    message("shit", server)
    welcome = "Welcome to POTI (Poker on the Internet)."
    prompt = "Enter '0' to login or '1' to create a new account.\n"
    cmd = raw_input(welcome + ' ' + prompt)
    while True:
        if cmd == '0':
            user = raw_input("Username: ")
            passwd = bcrypt.hashpw(getpass.getpass("Password: "), bcrypt.gensalt())
            #tmp = getpass.getpass("Password: ")
            #passwd = bcrypt.hashpw(tmp, bcrypt.gensalt())
            #print(bcrypt.checkpw(tmp, passwd))
            msg = "login:" + "user:" + user + "password:" + passwd
            print(msg)
            # TODO username only allows alphanumberic + _, A
            # send over HTTPS in POST body with username:password (no hashing on client side)
            return
        elif cmd == '1':
            print("1")
            return
        else:
            print("Invalid command.")
            cmd = raw_input(prompt)

if __name__ == '__main__':
    s = connect()
    login(s)
