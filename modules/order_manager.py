from modules.broker_interface import BrokerInterface


class OrderManager:
    def __init__(self, broker: BrokerInterface | None = None):
        self.broker = broker or BrokerInterface()

    def connect(self):
        return self.broker.connect()

    def disconnect(self):
        self.broker.disconnect()

    def status(self):
        return self.broker.status()

    def account_info(self):
        return self.broker.account_info()

    def risk_per_lot(self, symbol, direction, entry, stop_loss):
        return self.broker.risk_per_lot(
            symbol, direction, entry, stop_loss
        )

    def execute_trade(
        self,
        symbol,
        direction,
        volume,
        stop_loss,
        take_profit,
    ):
        return self.broker.open_order(
            symbol=symbol,
            direction=direction,
            volume=volume,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )

    def close_trade(self, order_id):
        return self.broker.close_order(order_id)

    def get_open_positions(self):
        return self.broker.get_positions()
