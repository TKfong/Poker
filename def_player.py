from __future__ import division
from constants import Constants

#Define a player

class Player:
    #creates playee
    def __init__(self, money):
        self.money = money;
        self.cards = [];
        self.amtIn = 0;


    #get player's previous move

    def getPreviousMove(self, move):
        return self.previousMove;

    #sets the previous move
    def setPreviousMove(self, move):
        self.previousMove = move;

    #adds money to the money count
    def addMoney(self, money):
        self.money+=money;

    #set the amount of money the player has
    def setMoney(self, money):
        self.money = money;

    #adds money to the players in tracker
    def addToMoneyIn(self, amt):
        if amt <= 0:
            return;
        self.moneyIn += amt;

    #subtracts money from money count
    def subMoney(self, amt):
        if self.money - amt < 0:
            self.money = 0;
        else:
            self.money -= amt;

        #empties the players
    def empty(self):
        del self.cards[:];
        self.moneyIn = 0;
        self.previousMove = None;

    #gets teh amt the player has in pot
    def getMoneyIn(self):
        return self.moneyIn;

    #gets the player's hand
    def getCards(self):
        return self.cards;

    #gets the players money
    def getMoney(self):
        return self.money;

    #get the players move
    def getMove(self, pot, prevMove):
        #add for cards on table
        print("You have ${0}, Pot is ${1}".format(self.money, pot));

        move = "";
        if prevMove == Constants.ALLIN or prevMove == Constants.RAISE:
            while move != "c" and move != "f":
                if prevMove == Constants.ALLIN:
                    move = input("The player before you went all in! Do you CALL [c], or FOLD [f]: ").lowewr();
                else:
                    move = input("The player before you raised! Do you CALL [c], or FOLD [f]: ").lower();
        else:
            while move != "a" and move != "c" and move != "f" and move != "r":
                move = input("Do you go ALL IN [a], CALL [c], FOLD [f], or RAISE [r]: ").lower();
        if move == "a":
            self.previousMove = Constants.ALLIN;
            return Constants.ALLIN;
        elif move == "c":
            self.previousMove = Constants.CALL;
            return Constants.CALL;
        elif move == "f":
            self.previousMove = Constants.FOLD;
            return Constants.FOLD;
        elif move == "r":
            self.previousMove = Constants.RAISE;
            return  Constants.RAISE;

    #gets bet from player
    def getBet(self, raiseAmt):
        amt = -1;
        while amt < raiseAmt or amt > self.getMoney():
            try:
                amt = int(input("Raise by: "));
            except ValueError:
                print("Must enter a valid amount");
        return amt;




