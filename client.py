import quickfix as fix
import random
import time
import datetime

class FixClient(fix.Application):
    def __init__(self):
        super().__init__()  # Initialize the parent class
        self.order_count = 0
        self.max_orders = 100
        self.max_duration = 5 * 60  # 5 minutes in seconds
        self.orders_sent = []  # Track sent orders
        self.executions = []  # Track executed orders
        
    def onCreate(self, sessionID):
        self.sessionID = sessionID

    def onLogon(self, sessionID):
        print(f"Logon - {sessionID}")
        self.sessionID = sessionID
        self.send_orders()

    def onLogout(self, sessionID):
        print(f"Logout - {sessionID}")

    def toAdmin(self, message, sessionID):
        msg_type = fix.MsgType()
        message.getHeader().getField(msg_type)

        # Log the outgoing admin message
        if msg_type.getValue() == fix.MsgType_Logon:
            print(f"Sending Logon message to {sessionID}")
            # Example of modifying the logon message if needed:
            # message.setField(fix.Username("my_username"))
            # message.setField(fix.Password("my_password"))
        elif msg_type.getValue() == fix.MsgType_Logout:
            print(f"Sending Logout message to {sessionID}")
        else:
            print(f"Sending Admin message: {message}")


    def fromAdmin(self, message, sessionID):
        msg_type = fix.MsgType()
        message.getHeader().getField(msg_type)
        # print(f"{message}")
        # Log the incoming admin message
        if msg_type.getValue() == fix.MsgType_Logon:
            print(f"Received Logon response from {sessionID}")
        elif msg_type.getValue() == fix.MsgType_Logout:
            print(f"Received Logout response from {sessionID}")
        elif msg_type.getValue() == fix.MsgType_Heartbeat:
            print(f"Received Heartbeat from {sessionID}")
        elif msg_type.getValue() == "3":
            # Handle Reject (35=3)
            print(f"Received Admin Reject: {message}")
            self.handle_reject(message)
        elif msg_type.getValue() == "8":
            # Handle Execution Report (35=8)
            self.handle_execution_report(message)     
        elif msg_type.getValue() == "9":
            # Handle Order Cancel Reject (35=9)
            self.handle_order_cancel_reject(message)
        elif msg_type.getValue() == "2":
            # Handle Resend Request (35=2)
            print(f"Received Resend Request")
        elif msg_type.getValue() == "4":
            # Handle Sequence Reset (35=4)
            print(f"Received Sequence Reset Request")
        elif msg_type.getValue() == "1":
            # Handle Sequence Reset (35=1)
            print(f"Received Test Request")
        else:
            print(f"Unknown Message Type:{msg_type.getValue()}" )
            print(f"Received Admin message: {message}")


    def toApp(self, message, sessionID):
        print(f"Sent: {message}")
    
    def fromApp(self, message, sessionID):
        price = fix.Price()
        print(f"Received: {message}")

    def send_orders(self):
        for i in range(self.max_orders):
            ticker = random.choice(["MSFT","AAPL","BAC"])
            side = random.choice([fix.Side_BUY, fix.Side_SELL])  # Random side: BUY or SELL
            price = random.uniform(100.0, 150.0) if random.choice([True, False]) else None  # Random price for limit orders
            self.send_order(ticker, side, price)
            time.sleep(random.uniform(0.1, 0.3))  # Wait for 0.1-0.3 seconds between orders
        
            if random.random() < 0.2:  # 20% chance to cancel an order
                    if self.orders_sent:
                        order_to_cancel = random.choice(self.orders_sent)
                        self.cancel_order(order_to_cancel['cl_ord_id'])
                
    def send_order(self, symbol, side, price=None):
        order = fix.Message()
        order.getHeader().setField(fix.MsgType(fix.MsgType_NewOrderSingle))  # Set order type to "New Order"
        cl_ord_id = f"order-{self.order_count}"
        order.setField(fix.ClOrdID(cl_ord_id))  # Set client order ID
        order.setField(fix.Symbol(symbol))  # Set symbol (e.g., MSFT)
        order.setField(fix.Side(side))  # Set side (BUY/SELL)
        order.setField(fix.OrderQty(100))  # Set order quantity
        order.setField(fix.HandlInst(1))
        
        # Create the current UTC datetime object
        order.setField(fix.StringField(60,(datetime.datetime.utcnow().strftime("%Y%m%d-%H:%M:%S.%f"))[:-3]))
       
        # fix.H
        if price:
            order.setField(fix.OrdType(fix.OrdType_LIMIT))  # Set as Limit order
            order.setField(fix.Price(price))  # Set price for Limit order
        else:
            order.setField(fix.OrdType(fix.OrdType_MARKET))  # Set as Market order
        fix.Session.sendToTarget(order, self.sessionID)  # Send order to server
        
         # Record order details
        self.orders_sent.append({
            'cl_ord_id': cl_ord_id,
            'symbol': symbol,
            'side': side,
        })
        self.order_count += 1

    def cancel_order(self, cl_ord_id):
        # Find the order to cancel
        order = next((o for o in self.orders_sent if o['cl_ord_id'] == cl_ord_id), None)
        if not order:
            print(f"Order ID {cl_ord_id} not found in orders_sent.")
            return

        cancel_request = fix.Message()
        cancel_request.getHeader().setField(fix.MsgType(fix.MsgType_OrderCancelRequest))  # Set message type to Order Cancel Request
        cancel_request.setField(fix.ClOrdID(f"cancel-{cl_ord_id}"))  # Unique ID for the cancel request
        cancel_request.setField(fix.OrigClOrdID(cl_ord_id))  # Original order ID to be canceled
        cancel_request.setField(fix.Symbol(order['symbol']))  # Set symbol (e.g., MSFT)
        cancel_request.setField(fix.Side(order['side']))  # Set side (BUY/SELL)
        # cancel_request.setField(fix.OrderQty(100))  # Optional: specify if needed
        cancel_request.setField(fix.StringField(60,(datetime.datetime.utcnow().strftime("%Y%m%d-%H:%M:%S.%f"))[:-3]))
        fix.Session.sendToTarget(cancel_request, self.sessionID)  # Send cancel request to server
        print(f"Sent Order Cancel Request for Order ID {cl_ord_id}")
        
        # Optional: remove the canceled order from the list
        self.orders_sent = [o for o in self.orders_sent if o['cl_ord_id'] != cl_ord_id]

    # Handle Reject (35=3)
    def handle_reject(self, message):
        reason = message.getField(fix.Text())  # Get the reject reason
        cl_ord_id = message.getField(fix.ClOrdID())  # Get the order ID that was rejected
        print(f"Order rejected. ClOrdID: {cl_ord_id}, Reason: {reason}")

    # Handle Execution Report (35=8)
    def handle_execution_report(self, message):
        cl_ord_id = message.getField(fix.ClOrdID())  # Get the order ID
        exec_type = message.getField(fix.ExecType())  # Get the execution type
        symbol = message.getField(fix.Symbol())  # Get the symbol of the trade
        exec_qty = message.getField(fix.LastShares())  # Get the executed quantity
        exec_price = message.getField(fix.LastPx())  # Get the execution price
        side = message.getField(fix.Side())  # Get the side (BUY/SELL)

        # Store the execution data for PNL, VWAP, and volume calculations
        execution_data = {
            'symbol': symbol,
            'cl_ord_id': cl_ord_id,
            'qty': exec_qty,
            'price': exec_price,
            'side': side
        }
        self.executions.append(execution_data)

        print(f"Execution Report for ClOrdID: {cl_ord_id} - {exec_qty} shares at {exec_price} for {symbol}")
        
        super().handle_execution_report(message)
    
        # Periodically calculate metrics
        total_volume = self.calculate_total_trading_volume()
        pnl = self.calculate_pnl()
        vwap = self.calculate_vwap(symbol)
        
        print(f"Total Trading Volume: {total_volume}")
        print(f"PNL: {pnl}")
        print(f"VWAP ({symbol}): {vwap}")

    # Handle Order Cancel Reject (35=9)
    def handle_order_cancel_reject(self, message):
        cl_ord_id = message.getField(fix.ClOrdID())  # Get the ClOrdID
        orig_cl_ord_id = message.getField(fix.OrigClOrdID())  # Get the original ClOrdID of the cancel request
        reason = message.getField(fix.Text())  # Get the rejection reason

        print(f"Order Cancel Request rejected. OrigClOrdID: {orig_cl_ord_id}, ClOrdID: {cl_ord_id}, Reason: {reason}")

    def calculate_total_trading_volume(self):
        total_volume = 0
        for execution in self.executions:
            total_volume += execution['qty']
        return total_volume
    
    def calculate_pnl(self):
        pnl = 0
        buy_orders = {}   # Tracks long positions
        sell_orders = {}  # Tracks short positions
        
        for execution in self.executions:
            symbol = execution['symbol']
            side = execution['side']
            qty = execution['qty']
            price = execution['price']
            
            if side == fix.Side_BUY:
                # Check if there are any short (sell) orders to match
                if symbol in sell_orders and sell_orders[symbol]:
                    sell_order = sell_orders[symbol].pop(0)  # Match with the first sell order (short)
                    pnl += (sell_order['price'] - price) * min(qty, sell_order['qty'])  # Short PnL: (sell price - buy price)
                    
                    # If sell order qty exceeds the buy qty, adjust and reinsert the remaining sell order
                    if sell_order['qty'] > qty:
                        sell_order['qty'] -= qty
                        sell_orders[symbol].insert(0, sell_order)
                    qty -= min(qty, sell_order['qty'])
                
                # Track remaining buy qty (or if no short positions) as a long position
                if qty > 0:
                    if symbol not in buy_orders:
                        buy_orders[symbol] = []
                    buy_orders[symbol].append({'price': price, 'qty': qty})
                    
            elif side == fix.Side_SELL:
                # Check if there are any long (buy) orders to match
                if symbol in buy_orders and buy_orders[symbol]:
                    buy_order = buy_orders[symbol].pop(0)  # Match with the first buy order
                    pnl += (price - buy_order['price']) * min(qty, buy_order['qty'])  # Long PnL: (sell price - buy price)
                    
                    # If buy order qty exceeds the sell qty, adjust and reinsert the remaining buy order
                    if buy_order['qty'] > qty:
                        buy_order['qty'] -= qty
                        buy_orders[symbol].insert(0, buy_order)
                    qty -= min(qty, buy_order['qty'])
                
                # Track remaining sell qty (or if no long positions) as a short position
                if qty > 0:
                    if symbol not in sell_orders:
                        sell_orders[symbol] = []
                    sell_orders[symbol].append({'price': price, 'qty': qty})
        
        return pnl



    def calculate_vwap(self, symbol):
        total_qty = 0
        total_value = 0
        
        for execution in self.executions:
            if execution['symbol'] == symbol:
                total_qty += execution['qty']
                total_value += execution['price'] * execution['qty']
        
        return total_value / total_qty if total_qty > 0 else 0

def main():
    settings = fix.SessionSettings("client.cfg")
    app = FixClient()
    storeFactory = fix.FileStoreFactory(settings)
    logFactory = fix.FileLogFactory(settings)
    initiator = fix.SocketInitiator(app, storeFactory, settings, logFactory)
    initiator.start()

    time.sleep(300)  # Run for 5 minutes
    # time.sleep(60)
    initiator.stop()

    

if __name__ == "__main__":
    main()
