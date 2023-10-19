class Player:
    def __init__(self, name):
        self.name = name
        #self.funds = funds
        self.hand = [] * 5
    
    def __str__(self):
        return f"Player: {self.name}"
    
    def show_hand(self):
        print(f"{self.name}'s hand:")
        for card in self.hand:
            print(card)