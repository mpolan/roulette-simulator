
class Player():
    def __init__(self, name:str="Gracz", balance:int=1000):
        if balance <= 0:
            raise ValueError("Balance must be greater than 0")
        self.name = name
        self.balance = balance

    def credit(self, amount:int) -> int:
        if amount <= 0:
            raise ValueError("Amount cannot be lower than 0")
        
        self.balance += amount
        
        return self.balance
    
    def debit(self, amount:int) -> int:
        if amount <= 0:
            raise ValueError("Amount cannot be lower than 0")
        
        if self.balance < amount:
            raise ValueError("Insufficient balance")   
      
        self.balance -= amount
        
        return self.balance