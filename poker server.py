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
import string, math, random
import time

encrypt_str = "encrypted_message="
account_str = "make_account="
num_clients = 0
client_public_key = "public_key="
encrypt_log = "encrypted_login="
ID = 0
available = [True, True, True, True, True]
given = [1, 2, 3, 4, 5]
active = [0, 0, 0, 0, 0]
pot = 0
turn = 0
current_bet = 0

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
					print "Thread closed"
					num_clients = num_clients - 1
					print "Number of clients: "+str(num_clients)
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
						#Login FAIL
						message = "LOGIN FAIL"
						#Encrypt with client public key
						encrypted = client_key.encrypt(message, 32)
						#Send to client
						self.c.send(str(encrypted))
						print "It Does Not Exist"
						print "Thread closed"
						num_clients = num_clients - 1
						print "Number of clients: "+str(num_clients)
						#return
						sys.exit()
					
					#Only one copy of the account on the database
					elif row_count == 1:
						#Request for Session Key
						message = "Request Session Key"
						#Encrypt with client public key
						encrypted = client_key.encrypt(message, 32)
						#Send to client
						self.c.send(str(encrypted))
						print "Getting session key"
						#Receive Session key
						data = self.c.recv(1024)
						#remove extra characters
						data = data.replace("\r\n", '') 
						data = data.replace(encrypt_str, '')
						#Encrypted Session Key; encrypted with server public key
						encrypted = eval(data)
						#Decrypt Session key and IV
						decrypted = private_key1.decrypt(encrypted)
						data = decrypted.split("!@#$%^&*()")
						#Session Key and IV
						sess_key = data[0]
						IV = data[1]


						#print "key: " + sess_key
						#print "IV: " + IV


						#Fill in Database
						#Add Session key to Database
						#Note any changes to the Database have to finalized with a commit()
						update_stmt = ("UPDATE users SET session_key = %s where username = %s and password = %s")
						cursor.execute(update_stmt, (sess_key, user, pw, ))
						db.commit()
						#Add IV to Database
						update_stmt = ("UPDATE users SET IV = %s where username = %s and password = %s")
						cursor.execute(update_stmt, (IV, user, pw, ))
						db.commit()
						#AES Encryption (Symmetric Encryption)
						#Decryptor/Encryptor
						aes = AES.new(sess_key, AES.MODE_CBC, IV)

						#Obtain/Add Player ID
						playerID = 0
						#global ID
						global available
						global given
						#Check if poker room full or not
						if True in available:
							#If there is room then assign an ID
							if available[available.index(True)]:
								ID = given[available.index(True)]
								available[available.index(True)] = False
							playerID = ID

							#Send Player ID
							msg = str(playerID)
							if len(msg) % 16 != 0:
								msg += '~' * (16 - len(msg) % 16)
							ciphertext = aes.encrypt(msg)
							self.c.send(ciphertext)
						else:
							#If room is full of players (5 players)
							print "No room"
							msg = str(playerID)
							if len(msg) % 16 != 0:
								msg += '~' * (16 - len(msg) % 16)
							ciphertext = aes.encrypt(msg)
							self.c.send(ciphertext)
							print "Thread closed"
							num_clients = num_clients - 1
							print "Number of clients: "+str(num_clients)
							sys.exit()

						#Add IDs to active index
						global active
						if ID not in active:
							active[active.index(0)] = playerID
						else:
							sys.exit()
						print "ID: " + str(ID)
						print active
						#Update database with PlayerID
						update_stmt = ("UPDATE users SET Player_ID = %s where username = %s and password = %s")
						cursor.execute(update_stmt, (playerID, user, pw, ))
						db.commit()
						

						#Start Poker Game
#################################################################
						global game
						global pot
						while True:
							hand = ''
							
							pot = 0
#######################################################
							game = Poker(num_clients)
							#Wait for at least 2 players
#######################################################
							while (num_clients < 2):
								waiting = "WAITING"
								if len(waiting) % 16 != 0:
									waiting += '~' * (16 - len(waiting) % 16)
								ciphertext = aes.encrypt(waiting)
								self.c.send(ciphertext)
								time.sleep(5)
							
							#Minimum players ready
							print "READY"
							ready = "READY"
							if len(ready) % 16 != 0:
								ready += '~' * (16 - len(ready) % 16)
							ciphertext = aes.encrypt(ready)
							self.c.send(ciphertext)
							time.sleep(5)
							
							#Generate initial pot
							pot = pot + 10
							fetch_stmt = "SELECT * FROM users WHERE username = %s and password = %s"
							cursor.execute(fetch_stmt, (user, pw, ))
							results = cursor.fetchall()
							print "RESULTS: "
							for row in results:
								money = row[5]
							print "Initial: " + str(money)
							money = money - 10
							print "After buy-in: " + str(money)

							print "POT: " + str(pot)
							#Problem pot is not updating fast enough

							#Confirm from players
							#global reply
							reply = ''
							while ("READY" not in reply):
								data = self.c.recv(1024)
								reply = aes.decrypt(data)
								print reply
								time.sleep(1)
							print "GO"
						
							#Betting
							global current_bet
	#						bet = 0
	#						msg = ""
	#						if len(msg) % 16 != 0:
	#							msg += '~' * (16 - len(msg) % 16)
	#						ciphertext = aes.encrypt(msg)
	#						self.c.send(ciphertext)
						


							#Deal cards
########################################################
							Hand = game.hands[playerID - 1]
							#for i in range(len(Hand)):
							sortedHand = sorted(Hand, reverse = True)
							for card in sortedHand:
								hand = hand + str(card) + ' '
							print (hand)
							text = game.isRoyal(Hand)

							#Check hands
#							hand1 = ''
#							Hand1 = game.hands[0]
#							sortedHand1 = sorted(Hand1, reverse = True)
#							for card in sortedHand1:
#								hand1 = hand1 + str(card) + ' '
#							print "hand1:"
#							print (hand1)
#							text = game.isRoyal(Hand1)
#						
#							hand2 = ''
#							Hand2 = game.hands[1]
#							sortedHand2 = sorted(Hand2, reverse = True)
#							for card in sortedHand2:
#								hand2 = hand2 + str(card) + ' '
#							print "hand2:"
#							print (hand2)
#							text = game.isRoyal(Hand2)

							maxpoint = max(game.tlist)
							maxindex = game.tlist.index(maxpoint)
							maxindex = maxindex + 1
							print('\nHand %d wins' % (maxindex))
							if maxindex == playerID:
								#Send result back to client
								msg = "YOU WIN"
								if len(msg) % 16 != 0:
									msg += '~' * (16 - len(msg) % 16)
								ciphertext = aes.encrypt(msg)
								self.c.send(ciphertext)
								#Update Money in database
								money = money + pot
								print "Winnings: " + str(money)
								update_stmt = ("UPDATE users SET Money = %s where username = %s and password = %s")
								cursor.execute(update_stmt, (str(money), user, pw, ))
								db.commit()
							else:
								#Send result back to client
								msg = "YOU LOSE"
								if len(msg) % 16 != 0:
									msg += '~' * (16 - len(msg) % 16)
								ciphertext = aes.encrypt(msg)
								self.c.send(ciphertext)
								#Update Money in database
								update_stmt = ("UPDATE users SET Money = %s where username = %s and password = %s")
								cursor.execute(update_stmt, (str(money), user, pw, ))
								db.commit()

							print "poker hand: "
							#print text
							#Text send using AES has to be a multiple to 16 so fill extra space with junk character ~
							if len(hand) % 16 != 0:
								hand += '~' * (16 - len(hand) % 16)
							ciphertext = aes.encrypt(hand)
							self.c.send(ciphertext)
###############################################################################

					#Beware if row_count != 1
					else:
						print "Multiple copies of account exist"
						#return
						sys.exit()

					#Delete session key and IV from database
					update_stmt = ("UPDATE users SET session_key = 'NULL' where username = %s and password = %s")
					cursor.execute(update_stmt, (user, pw, ))
					db.commit()
					update_stmt = ("UPDATE users SET IV = 'NULL' where username = %s and password = %s")
					cursor.execute(update_stmt, (user, pw, ))
					db.commit()
					db.close()
					#break
				#while True:
				#elif decrypted == "Quit": 
					#self.c.send("Thread closed\n")
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

	global game
	game = Poker(num_clients)

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
	
	#Create account on MySQL database
	if data == "Account: OK":
		#Get public key for making accounts
		global public_key0
		#Send out public key
		c.send("public_key=" + public_key0.exportKey() + "\n")
		print "Public key sent to account maker."

#		#Update number of clients
#		global num_clients 
#		num_clients = num_clients + 1
#		#Limit number of clients server can handle to 5
#		if num_clients > 5:
#			c.send("Too many clients")
#			print "Fail: too many clients"
#			num_clients = num_clients - 1
#			print "Number of clients: " + str(num_clients)
#			return
#		#Otherwise prepare to receive data for new account
#		else:
#			c.send("Ready")
#			print "Number of clients: " + str(num_clients)
#			# Open database connection
#			db = MySQLdb.connect("localhost","root","root","poker" )
#
#			# prepare a cursor object using cursor() method
#			cursor = db.cursor()

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
			#print "Received:\nEncrypted message = "+str(data)
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
				insert_stmt = ("INSERT INTO users (username, password, Money) VALUES (%s, %s, %s)")
				cursor.execute(insert_stmt, (data[0], data[1], '1000'))
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
				#num_clients = num_clients - 1
				print "Thread closed"
				print "Number of clients: "+str(num_clients)
				#if num_clients <= 0: break
				break

class Card(object):
	RANKS = (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14)
	SUITS = ('S', 'D', 'C', 'H')

	def __init__(self, rank, suit):
		self.rank = rank
		self.suit = suit

	def __str__(self):
		if self.rank == 14:
			rank = 'A'
		elif self.rank == 13:
			rank = "K"
		elif self.rank == 12:
			rank = "Q"
		elif self.rank == 11:
			rank = "J"
		else:
			rank = self.rank
		return str(rank) + self.suit

	def __eq__(self, other):
		return (self.rank == other.rank)

	def __ne__(self, other):
		return (self.rank != other.rank)

	def __lt__(self, other):
		return (self.rank < other.rank)

	def __le__(self, other):
		return (self.rank <= other.rank)

	def __gt__(self, other):
		return (self.rank > other.rank)

	def __ge__(self, other):
		return (self.rank >= other.rank)


class Deck(object):
	def __init__(self):
		self.deck = []
		for suit in Card.SUITS:
	    		for rank in Card.RANKS:
				card = Card(rank, suit)
				self.deck.append(card)

	def shuffle(self):
		random.shuffle(self.deck)

	def __len__(self):
		return len(self.deck)

	def deal(self):
		if len(self) == 0:
	    		return None
		else:
			return self.deck.pop(0)

class Poker(object):
	def __init__(self, numHands):

		self.deck = Deck()
		self.deck.shuffle()
		self.hands = []
		self.tlist = []  # create a list to store total_point
		numCards_in_Hand = 5

		for i in range(numHands):
	    		hand = []
		    	for j in range(numCards_in_Hand):
		        	hand.append(self.deck.deal())
		    	self.hands.append(hand)

	def play(self):
		for i in range(len(self.hands)):
		    	sortedHand = sorted(self.hands[i], reverse=True)
		    	hand = ''
		    	for card in sortedHand:
		        	hand = hand + str(card) + ''
		    	print ('Hand ' + str(i+1) + ': ' + hand)

    	def point(self, hand):  # point()function to calculate partial score
		sortedHand = sorted(hand, reverse=True)
		c_sum = 0
		ranklist = []
		for card in sortedHand:
		    	ranklist.append(card.rank)
		c_sum = ranklist[0] * 13 ** 4 + ranklist[1] * 13 ** 3 + ranklist[2] * 13 ** 2 + ranklist[3] * 13 + ranklist[4]
		return c_sum

    	def isRoyal(self, hand):  # returns the total_point and prints out 'Royal Flush' if true, if false, pass down to isStraightFlush(hand)
		sortedHand = sorted(hand, reverse=True)
		flag = True
		h = 10
		Cursuit = sortedHand[0].suit
		Currank = 14
		total_point = h * 13 ** 5 + self.point(sortedHand)
		for card in sortedHand:
	    		if card.suit != Cursuit or card.rank != Currank:
		        	flag = False
		        	break
		    	else:
		        	Currank -= 1
		if flag:
		    	print('Royal Flush')
		    	self.tlist.append(total_point)
		else:
		    	self.isStraightFlush(sortedHand)

    	def isStraightFlush(self, hand):  # returns the total_point and prints out 'Straight Flush' if true, if false, pass down to isFour(hand)
		sortedHand = sorted(hand, reverse=True)
		flag = True
		h = 9
		Cursuit = sortedHand[0].suit
		Currank = sortedHand[0].rank
		total_point = h * 13 ** 5 + self.point(sortedHand)
		for card in sortedHand:
		    	if card.suit != Cursuit or card.rank != Currank:
		        	flag = False
		        	break
		    	else:
		        	Currank -= 1
		if flag:
		    	print('Straight Flush')
		    	self.tlist.append(total_point)
		else:
		    	self.isFour(sortedHand)

    	def isFour(self, hand):  # returns the total_point and prints out 'Four of a Kind' if true, if false, pass down to isFull()
		sortedHand = sorted(hand, reverse=True)
		flag = True
		h = 8
		Currank = sortedHand[1].rank  # since it has 4 identical ranks,the 2nd one in the sorted listmust be the identical rank
		count = 0
		total_point = h * 13 ** 5 + self.point(sortedHand)
		for card in sortedHand:
		    	if card.rank == Currank:
		        	count += 1
		if not count < 4:
		    	flag = True
		    	print('Four of a Kind')
		    	self.tlist.append(total_point)
		else:
		    	self.isFull(sortedHand)

    	def isFull(self, hand):  # returns the total_point and prints out 'Full House' if true, if false, pass down to isFlush()
		sortedHand = sorted(hand, reverse=True)
		flag = True
		h = 7
		total_point = h * 13 ** 5 + self.point(sortedHand)
		mylist = []  # create a list to store ranks
		for card in sortedHand:
		    	mylist.append(card.rank)
		rank1 = sortedHand[0].rank  # The 1st rank and the last rank should be different in a sorted list
		rank2 = sortedHand[-1].rank
		num_rank1 = mylist.count(rank1)
		num_rank2 = mylist.count(rank2)
		if (num_rank1 == 2 and num_rank2 == 3) or (num_rank1 == 3 and num_rank2 == 2):
		    	flag = True
		    	print('Full House')
		    	self.tlist.append(total_point)
		else:
			    flag = False
			    self.isFlush(sortedHand)

    	def isFlush(self, hand):  # returns the total_point and prints out 'Flush' if true, if false, pass down to isStraight()
		sortedHand = sorted(hand, reverse=True)
		flag = True
		h = 6
		total_point = h * 13 ** 5 + self.point(sortedHand)
		Cursuit = sortedHand[0].suit
		for card in sortedHand:
		    	if not (card.suit == Cursuit):
		        	flag = False
		        	break
		if flag:
		    	print('Flush')
		    	self.tlist.append(total_point)
		else:
		    	self.isStraight(sortedHand)

    	def isStraight(self, hand):
		sortedHand = sorted(hand, reverse=True)
		flag = True
		h = 5
		total_point = h * 13 ** 5 + self.point(sortedHand)
		Currank = sortedHand[0].rank  # this should be the highest rank
		for card in sortedHand:
		    	if card.rank != Currank:
		        	flag = False
		        	break
		    	else:
		        	Currank -= 1
		if flag:
		    	print('Straight')
		    	self.tlist.append(total_point)
		else:
		    	self.isThree(sortedHand)

    	def isThree(self, hand):
		sortedHand = sorted(hand, reverse=True)
		flag = True
		h = 4
		total_point = h * 13 ** 5 + self.point(sortedHand)
		Currank = sortedHand[2].rank  # In a sorted rank, the middle one should have 3 counts if flag=True
		mylist = []
		for card in sortedHand:
		    	mylist.append(card.rank)
		if mylist.count(Currank) == 3:
		    	flag = True
		    	print("Three of a Kind")
		    	self.tlist.append(total_point)
		else:
		    	flag = False
		    	self.isTwo(sortedHand)

    	def isTwo(self, hand):  # returns the total_point and prints out 'Two Pair' if true, if false, pass down to isOne()
		sortedHand = sorted(hand, reverse=True)
		flag = True
		h = 3
		total_point = h * 13 ** 5 + self.point(sortedHand)
		rank1 = sortedHand[1].rank  # in a five cards sorted group, if isTwo(), the 2nd and 4th card should have another identical rank
		rank2 = sortedHand[3].rank
		mylist = []
		for card in sortedHand:
		    	mylist.append(card.rank)
		if mylist.count(rank1) == 2 and mylist.count(rank2) == 2:
		    	flag = True
		    	print("Two Pair")
		    	self.tlist.append(total_point)
		else:
		    	flag = False
		    	self.isOne(sortedHand)

    	def isOne(self, hand):

		# returns the total_point and prints out 'One Pair' if true, if false, pass down to isHigh()
		sortedHand = sorted(hand, reverse=True)
		flag = True
		h = 2
		total_point = h * 13 ** 5 + self.point(sortedHand)
		mylist = []  # create an empty list to store ranks
		mycount = []  # create an empty list to store number of count of each rank
		for card in sortedHand:
		    	mylist.append(card.rank)
		for each in mylist:
		    	count = mylist.count(each)
		    	mycount.append(count)
		if mycount.count(2) == 2 and mycount.count(1) == 3:  # There should be only 2 identical numbers and the rest are all different
		    	flag = True
		    	print("One Pair")
		    	self.tlist.append(total_point)
		else:
		    	flag = False
		    	self.isHigh(sortedHand)

    	def isHigh(self, hand):
		# returns the total_point and prints out 'High Card'
		sortedHand = sorted(hand, reverse=True)
		flag = True
		h = 1
		total_point = h * 13 ** 5 + self.point(sortedHand)
		mylist = []  # create a list to store ranks
		for card in sortedHand:
		    	mylist.append(card.rank)
		print("High Card")
		self.tlist.append(total_point)

if __name__ == '__main__':
	Main()
# By Timothy Fong
# CMPE 209 Poker Project
