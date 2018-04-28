def turn(playerBank,label):
    #playerBank is just the player's balance (whoever's turn it is) and label is just  tkinter text.
    win.getMouse()
    action = ent.getText()
    if action == 'check':
        pass
    elif action == 'call':
        playerBank = playerBank - cashMoney
        pool = pool + cashMoney
    elif action == 'raise':
        cashMoney = cash.getText()
        playerBank = playerBank - cashMoney
        pool = pool + cashMoney
    elif action == 'fold':
         break