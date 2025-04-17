

class Transaction:
    transactionCounter = 1
    size = 8                # 8 Kilobits

    def __init__(self, senderId: int, receiverId: int, amount: int):
        """
        Args:
            senderId (int): Peer ID of Sender
            receiverId (int): Peer ID od Receiver
            amount (int): Amount of coins to be transferred
        """
        self.txnID = Transaction.transactionCounter
        Transaction.transactionCounter += 1

        self.senID = senderId
        self.recID = receiverId
        self.amt = amount



