from modules.broker_interface import BrokerInterface


class OrderManager:


    def __init__(self):

        self.broker = BrokerInterface()



    def execute_trade(
        self,
        symbol,
        direction,
        volume,
        stop_loss,
        take_profit
    ):


        order = self.broker.open_order(

            symbol=symbol,

            direction=direction,

            volume=volume,

            stop_loss=stop_loss,

            take_profit=take_profit

        )


        return order



    def close_trade(self, order_id):


        result = self.broker.close_order(

            order_id

        )


        return result



    def get_open_positions(self):


        return self.broker.get_positions()
