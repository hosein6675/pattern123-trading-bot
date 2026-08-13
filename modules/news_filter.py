from dataclasses import dataclass
from datetime import datetime


@dataclass
class NewsStatus:

    has_news: bool
    impact: str
    event: str
    currency: str
    allow_trade: bool
    message: str



class NewsFilter:


    def __init__(self):

        self.provider = "economic_calendar"



    def check_news(self, symbol):


        # نسخه اولیه دمو
        # در آینده به API خبری وصل می‌شود

        return NewsStatus(

            has_news=False,

            impact="none",

            event="",

            currency="",

            allow_trade=True,

            message="No high impact news"

        )



    def set_provider(self, provider):

        self.provider = provider
