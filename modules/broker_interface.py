from dataclasses import dataclass



@dataclass
class OrderResult:

    success: bool

    order_id: str

    message: str



class BrokerInterface:


    def __init__(self):

        self.connection = "demo"



    def connect(self):

        return {

            "status": "connected",

            "mode": self.connection

        }



    def open_order(
        self,
        symbol,
        direction,
        volume,
        stop_loss,
        take_profit
    ):


        # نسخه دمو
        # در آینده به MT5/API وصل می‌شود


        return OrderResult(

            success=True,

            order_id="DEMO_ORDER",

            message="Order created in demo mode"

        )



    def close_order(self, order_id):


        return OrderResult(

            success=True,

            order_id=order_id,

            message="Order closed"

        )



    def get_positions(self):


        return []
