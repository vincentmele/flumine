import time
import logging
import betfairlightweight
from pythonjsonlogger import jsonlogger

from dynaconf import settings, Validator

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

settings.validators.register(
    Validator('USERNAME', 'PASSWORD', 'APP_KEY', 'CERTS', 'EVENT_TYPE_IDS', 'MARKET_TYPES', must_exist = True),
    Validator('EVENT_TYPE_IDS', 'MARKET_TYPES', is_type_of=list)

)
settings.validators.validate()

trading = betfairlightweight.APIClient(settings.USERNAME, settings.PASSWORD,
                                       settings.APP_KEY, settings.CERTS)
client = clients.BetfairClient(trading)

framework = Flumine(client=client)

strategy = MarketRecorder(
    name="WIN",
    market_filter=betfairlightweight.filters.streaming_market_filter(
        event_type_ids=settings.EVENT_TYPE_IDS,
        country_codes=settings.get('COUNTRY_CODES', None),
        market_types=settings.MARKET_TYPES,
    ),
    stream_class=DataStream,
    context={"local_dir": settings.LOCAL_DIR,
             "force_update": settings.as_bool('FORCE_UPDATE'),
             "remove_file": settings.as_bool('REMOVE_FILE')},
)

framework.add_strategy(strategy)

framework.run()
