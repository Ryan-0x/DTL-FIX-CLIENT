import quickfix as fix
import random
import time

class FixClient(fix.Application):
    def onCreate(self, sessionID):
        self.sessionID = sessionID

    def onLogon(self, sessionID):
        print(f"Logon - {sessionID}")
        self.sessionID = sessionID
        self.send_orders()

    def onLogout(self, sessionID):
        print(f"Logout - {sessionID}")

    def toAdmin(self, message, sessionID):
        pass

    def fromAdmin(self, message, sessionID):
        pass

    def toApp(self, message, sessionID):
        print(f"Sent: {message}")
    
    def fromApp(self, message, sessionID):
        print(f"Received: {message}")
        msg_type = fix.MsgType()
        message.getHeader().getField(msg_type)
        if msg_type == "8":  # Execution Report
            self.handle_execution_report(message)

    def send_orders(self):
        for i in range(20):
            side = random.choice([fix.Side_BUY, fix.Side_SELL])  # Random side: BUY or SELL
            price = random.uniform(100.0, 150.0) if random.choice([True, False]) else None  # Random price for limit orders
            self.send_order("MSFT", side, price)
            time.sleep(random.uniform(0.1, 0.5))  # Wait for 0.1-0.5 seconds between orders

    def send_order(self, symbol, side, price=None):
        order = fix.Message()
        order.getHeader().setField(fix.MsgType(fix.MsgType_NewOrderSingle))  # Set order type to "New Order"
        order.setField(fix.Symbol(symbol))  # Set symbol (e.g., MSFT)
        order.setField(fix.Side(side))  # Set side (BUY/SELL)
        order.setField(fix.OrderQty(100))  # Set order quantity
        if price:
            order.setField(fix.OrdType(fix.OrdType_LIMIT))  # Set as Limit order
            order.setField(fix.Price(price))  # Set price for Limit order
        else:
            order.setField(fix.OrdType(fix.OrdType_MARKET))  # Set as Market order
        fix.Session.sendToTarget(order, self.sessionID)  # Send order to server


    def handle_execution_report(self, message):
        # Parse and track the execution report for statistics
        pass

def main():
    settings = fix.SessionSettings("client.cfg")
    app = FixClient()
    storeFactory = fix.FileStoreFactory(settings)
    logFactory = fix.FileLogFactory(settings)
    initiator = fix.SocketInitiator(app, storeFactory, settings, logFactory)
    initiator.start()

    # time.sleep(300)  # Run for 5 minutes
    time.sleep(60)
    initiator.stop()

if __name__ == "__main__":
    main()
