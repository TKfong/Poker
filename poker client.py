# By Timothy Fong
# CMPE 209 Poker Project
import socket
from Crypto.PublicKey import RSA
from Crypto import Random
import hashlib
import os, random, struct, sys
import Crypto.Random
from Crypto.Cipher import AES
import time

#Declare server's attributes
server = socket.socket()
host = "10.0.2.15"
#host = "127.0.1.1"
port = 7777
#Connect to server
server.connect((host, port))

#Tell server that connection is OK for poker game
server.sendall("Poker: GO")

#Receive public key string from server
server_string = server.recv(1024)

#Remove extra characters
server_string = server_string.replace("public_key=", '')
server_string = server_string.replace("\r\n", '')

#Convert string to key
server_public_key = RSA.importKey(server_string)
#print server_public_key.exportKey()

#Generate Client public/private key pair
random_generator = Random.new().read
client_private_key = RSA.generate(1024, random_generator)
client_public_key = client_private_key.publickey()
#print client_public_key.exportKey()

#Server's response if too many clients
server_response = server.recv(1024)
server_response = server_response.replace("\r\n", '')
print "server: " + server_response
#If Server occupied
if server_response == "Too many clients":
	print "Fail: server is currently full"
	print "Now quiting"
	server.close()
	sys.exit()
	print "b"

#Otherwise, send client's public key for asymmetric encryption
elif server_response == "Request Public Key":
	print "c"
	server.sendall("public_key=" + client_public_key.exportKey() + "\n")

	#Login to obtain public key
	username = raw_input("Username: ")
	type(username)
	password = raw_input("Password: ")
	type(password)
	message = "encrypted_login=" + username + "~!@#$%^&*()" + password

	#hashing, maybe later
	#hash_user = hashlib.md5(username)
	#hash_pass = hashlib.md5(password)
	#message = hash_user.hexdigest() + "#" + hash_pass.hexdigest() + "#" + client_public_key


	#Encrypt message
	encrypted = server_public_key.encrypt(message, 32)
	#Send Login Info to server
	server.sendall(str(encrypted))
	#Receive server reply confirming reception of username and password
	#server_response = server.recv(1024)
	#server_response = server_response.replace("\r\n", '')
	
	#Receive request for session key
	server_response = server.recv(1024)
	encrypted = eval(server_response)
	#Decrypt message
	decrypted = client_private_key.decrypt(encrypted)
	print decrypted
	#Confirm request
	if "Request Session Key" in decrypted:
		#Generate AES key and information
		key = Crypto.Random.OSRNG.posix.new().read(AES.block_size)
		#print key
		#Generate initialization vector
		IV = ''.join(chr(random.randint(0, 0xFF)) for i in range(16))
		#print IV
		mode = AES.MODE_CBC
		#Encrypt AES key and IV
		encrypted = server_public_key.encrypt(key + "!@#$%^&*()" + IV, 32)
		#Send to server
		server.sendall("encrypted_message="+str(encrypted))
	else:
		print "nono"
		sys.exit()
	#Confirm reception of key and IV
	server_response = server.recv(1024)
	#Decrypt check message
	decryptor = AES.new(key, mode, IV=IV)
	plain = decryptor.decrypt(server_response)
	plain = plain.replace("~", '')
	print plain
		#break
	#Tell server to finish connection
	#if message == "quit": break

server.sendall("Quit")
print "d"
print(server.recv(1024)) 
#Quit server response
server.close()
# By Timothy Fong
# CMPE 209 Poker Project
