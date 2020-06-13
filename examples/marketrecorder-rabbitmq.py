import time
import logging
import betfairlightweight
from pythonjsonlogger import jsonlogger

from flumine import Flumine, clients
from flumine.streams.datastream import DataStream
from strategies.marketrecorder import MarketRecorder

logger = logging.getLogger()

custom_format = "%(asctime) %(levelname) %(message)"
log_handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(custom_format)
formatter.converter = time.gmtime
log_handler.setFormatter(formatter)
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)

trading = betfairlightweight.APIClient("Rn2xJaSX4kLgQYZn5yEL", "RXKwNGQvpD3w", app_key="P86bgTI8r2VVhuYM", certs="/root/certs")

client = clients.BetfairClient(trading)

framework = Flumine(client=client)

strategy = MarketRecorder(
    name="WIN",
    market_filter=betfairlightweight.filters.streaming_market_filter(
        event_type_ids=["4339"],
       # country_codes=["FR", "AU"],
        market_types=["WIN"],
        # market_ids=["1.169056942"],
        # event_ids=[29671376]
    ),
    stream_class=DataStream,
    context={
        "local_dir": "/root/",
        "force_update": True,
        "remove_file": True,
    },
)

framework.add_strategy(strategy)

framework.run()
