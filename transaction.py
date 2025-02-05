

class Transaction:
    transactionCounter = 1
    size = 8 ## 8 kilobits
    def __init__(self, senderId, receiverId, amount):
        self.txnID = Transaction.transactionCounter
        Transaction.transactionCounter += 1
        self.senID = senderId
        self.recID = receiverId
        self.amt = amount



