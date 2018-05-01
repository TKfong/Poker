# By Timothy Fong
# CMPE 209 Poker Project
#!/usr/bin/python
import socket
from Crypto.PublicKey import RSA
from Crypto import Random
import os
import sys
import threading
import mysql.connector
from Crypto.Cipher import AES
import MySQLdb

encrypt_str = "encrypted_message="
account_str = "make_account="
num_clients = 0
client_public_key = "public_key="
encrypt_log = "encrypted_login="
ID = 0
active = [0, 0, 0, 0, 0]

#Generate private and public keys
#Keys for making accounts
random_generator = Random.new().read
private_key0 = RSA.generate(1024, random_generator)
public_key0 = private_key0.publickey()
#Keys for getting session keys
random_generator = Random.new().read
private_key1 = RSA.generate(1024, random_generator)
public_key1 = private_key1.publickey()

# Thread class
class ClientThread(threading.Thread):
	def __init__ (self, c, addr):
		self.c = c
		self.addr = addr
		threading.Thread.__init__(self)
		print "Starting new thread"

	#might need to implement socket close at end of thread
	def run(self):
		#Wait until data is received.
		data = self.c.recv(1024)
		#remove new line character
		data = data.replace("\r\n", '') 

		#Create account on MySQL database
		make_account(self.c, data)
			
		#Poker Client 
		#Check account exists on MySQL database
		if data == "Poker: GO":
			#Get public key for making accounts
			global public_key1
			#Send out public key
			self.c.send("public_key=" + public_key1.exportKey() + "\n")
			print "Public key sent to account maker."
			#Update number of clients
			global num_clients 
			num_clients = num_clients + 1


			#print "poker go"


			#Limit number of clients server can handle to 5 
			if num_clients > 5:
				self.c.send("Too many clients")
				print "Fail: too many clients"
				num_clients = num_clients - 1
				print "Number of clients: " + str(num_clients)
				return
			#Otherwise prepare to receive account data
			else:
				#Request client public key
				#self.c.send("Start")
				print "Number of clients: " + str(num_clients)
				#Request client public key
				self.c.send("Request Public Key")
				#Receive client public key
				data = self.c.recv(1024)
				#Check client key
				if client_public_key in data:
					#Remove extra characters
					data = data.replace("\r\n", '') 
					data = data.replace(client_public_key, '')
					#Convert to key
					client_key = RSA.importKey(data)


					#print client_key.exportKey()


					# Open database connection
					db = MySQLdb.connect("localhost","root","root","poker" )
					# prepare a cursor object using cursor() method
					cursor = db.cursor()
				else:
					print "no public key"
					#return
					sys.exit()
				
				#Wait until username and password data is received.
				data = self.c.recv(1024)
				encrypted = eval(data)
				#Decrypt message
				decrypted = private_key1.decrypt(encrypted)
				
				#Receive encrypted message
				if encrypt_log in decrypted: 
					#Remove extra characters
					decrypted = decrypted.replace("\r\n", '') 
					decrypted = decrypted.replace(encrypt_log, '')


					#print "Received:\nEncrypted message = "+str(data)
					#print "Decrypted message = " + decrypted


					data = decrypted.split("~!@#$%^&*()")
					#Obtain username and password
					user = data[0]
					pw = data[1]
					#Check if username and password exist on database
					check_stmt = ("SELECT * FROM users WHERE username = %s and password = %s")
					cursor.execute(check_stmt, (user, pw, ))				
					#Check for a row on the database
					row_count = cursor.rowcount
					print("number of affected rows: {}".format(row_count))
					#If row_count > 0 then username/password on databse
					if row_count == 0:
						print "It Does Not Exist"
						#return
						sys.exit()
					#Only one copy of the account on the database
					elif row_count == 1:
						#Request for Session Key
						message = "Request Session Key"
						encrypted = client_key.encrypt(message, 32)
						self.c.send(str(encrypted))
						print "Getting session key"
						data = self.c.recv(1024)
						#remove new line character
						data = data.replace("\r\n", '') 
						data = data.replace(encrypt_str, '')
						encrypted = eval(data)
						decrypted = private_key1.decrypt(encrypted)
						data = decrypted.split("!@#$%^&*()")
						sess_key = data[0]
						IV = data[1]
						#self.c.send("Server: OK")
						print "key: " + sess_key
						print "IV: " + IV
						#Fill in Database
						#Add Session key to Database
						update_stmt = ("UPDATE users SET session_key = %s where username = %s and password = %s")
						cursor.execute(update_stmt, (sess_key, user, pw, ))
						db.commit()
						#Add IV to Database
						update_stmt = ("UPDATE users SET IV = %s where username = %s and password = %s")
						cursor.execute(update_stmt, (IV, user, pw, ))
						db.commit()
						#Add Player ID
						global ID
						ID = ID + 1
						global active
						if ID not in active:
							active[active.index(0)] = ID
						else:
							sys.exit()
						print "ID: " + str(ID)
						update_stmt = ("UPDATE users SET Player_ID = %s where username = %s and password = %s")
						cursor.execute(update_stmt, (ID, user, pw, ))
						db.commit()

						encryptor = AES.new(sess_key, AES.MODE_CBC, IV)
						text = 'loki dies'
						if len(text) % 16 != 0:
							text += '~' * (16 - len(text) % 16)
						ciphertext = encryptor.encrypt(text)
						self.c.send(ciphertext)

					#Beware if row_count != 1
					else:
						print "Multiple copies of account exist"
						#return
						sys.exit()
					db.close()
					#break
				#while True:
				#elif decrypted == "Quit": 
					self.c.send("Thread closed\n")
					print "Thread closed"
					num_clients = num_clients - 1
					print "Number of clients: "+str(num_clients)
					if num_clients <= 0: return

def Main():
	#Declaration of server attributes
	mysocket = socket.socket()
	host = socket.gethostbyname(socket.getfqdn())
	port = 7777
	#host check
	if host == "127.0.1.1":
		import commands
		host = commands.getoutput("hostname -I")
	print "host = " + host

	#Prevent socket.error: [Errno 98] Address already in use
	mysocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

	mysocket.bind((host, port))
	#Socket listening on port
	mysocket.listen(5)

	while True:
		#establish connection with client
		c, addr = mysocket.accept()
		#start a new thread and return its identifier
		ClientThread(c, addr).start()

	#Server to stop
	c.send("Server stopped\n")
	print "Server stopped"
	c.close()
	#cursor.close()
	#cnx.close()

def make_account(c, data):
	#Wait until data is received.
	#data = c.recv(1024)
	#data = data.replace("\r\n", '') #remove new line character
	
	#Create account on MySQL database
	if data == "Account: OK":
		#Get public key for making accounts
		global public_key0
		#Send out public key
		c.send("public_key=" + public_key0.exportKey() + "\n")
		print "Public key sent to account maker."
		#Update number of clients
		global num_clients 
		num_clients = num_clients + 1
		#Limit number of clients server can handle to 5
		if num_clients > 5:
			c.send("Too many clients")
			print "Fail: too many clients"
			num_clients = num_clients - 1
			print "Number of clients: " + str(num_clients)
			return
		#Otherwise prepare to receive data for new account
		else:
			c.send("Ready")
			print "Number of clients: " + str(num_clients)
			# Open database connection
			db = MySQLdb.connect("localhost","root","root","poker" )

			# prepare a cursor object using cursor() method
			cursor = db.cursor()
		while True:
			#Wait until username and password data is received
			data = c.recv(1024)
			#Encrypted data
			print "Received:\nEncrypted message = "+str(data)
			encrypted = eval(data)
			#Decrypt message data
			decrypted = private_key0.decrypt(encrypted)
			 
			#Confirm keyword in data received by account_maker
			#Otherwise loop
			if account_str in decrypted: 
				#Remove extra characters
				decrypted = decrypted.replace(account_str, '')
				decrypted = decrypted.replace("\r\n", '')
				#Send confirmation of reception (optional)
				c.send("Server: OK")
				print "Decrypted message = " + decrypted
				#separate username and password
				data = decrypted.split("~!@#$%^&*()")
				#Insert into Mysql database
				#cnx = mysql.connector.connect(user='root', password='root', host='127.0.0.1', database='poker')
				#cursor = cnx.cursor()
				insert_stmt = ("INSERT INTO users (username, password) VALUES (%s, %s)")
				cursor.execute(insert_stmt, (data[0], data[1], ))
				print data[0]
				print data[1]
				#End Mysql connection
				db.commit()
				#cursor.close()
				db.close()
			#End loop, end thread, and end connection
			elif decrypted == "Quit": 
				c.send("Thread closed\n")
				#Update number of clients connected
				num_clients = num_clients - 1
				print "Number of clients: "+str(num_clients)
				#if num_clients <= 0: break
				break

if __name__ == '__main__':
	Main()
# By Timothy Fong
# CMPE 209 Poker Project
