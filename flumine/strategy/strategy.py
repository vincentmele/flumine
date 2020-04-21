from typing import Type, Iterator
from betfairlightweight import filters
from betfairlightweight.resources import MarketBook, RaceCard

from ..streams.marketstream import BaseStream, MarketStream
from ..markets.market import Market
from .runnercontext import RunnerContext

DEFAULT_MARKET_DATA_FILTER = filters.streaming_market_data_filter(
    fields=[
        "EX_ALL_OFFERS",
        "EX_TRADED",
        "EX_TRADED_VOL",
        "EX_LTP",
        "EX_MARKET_DEF",
        "SP_TRADED",
        "SP_PROJECTED",
    ]
)


class BaseStrategy:
    def __init__(
        self,
        market_filter: dict,
        market_data_filter: dict = None,
        streaming_timeout: float = None,
        conflate_ms: int = None,
        stream_class: Type[BaseStream] = MarketStream,
        name: str = None,
        context: dict = None,
    ):
        """
        Processes data from streams.

        :param market_filter: Streaming market filter
        :param market_data_filter: Streaming market data filter
        :param streaming_timeout: Streaming timeout in seconds, will call snap() on cache
        :param conflate_ms: Streaming conflation
        :param stream_class: Can be Market or Data
        :param name: Strategy name
        :param context: Dictionary holding additional vars
        """
        self.market_filter = market_filter
        self.market_data_filter = market_data_filter or DEFAULT_MARKET_DATA_FILTER
        self.streaming_timeout = streaming_timeout
        self.conflate_ms = conflate_ms
        self.stream_class = stream_class
        self._name = name
        self.context = context

        self._invested = {}  # {marketId: {selectionId: RunnerContext}}
        self.streams = []  # list of streams strategy is subscribed

    def check_market(self, market: Market, market_book: MarketBook) -> bool:
        if market_book.streaming_unique_id not in self.stream_ids:
            return False  # strategy not subscribed to market stream
        elif self.check_market_book(market, market_book):
            return True
        else:
            return False

    def add(self) -> None:
        # called when strategy is added to framework
        return

    def start(self) -> None:
        # called when flumine starts but before streams start
        # e.g. subscribe to extra streams
        return

    def check_market_book(self, market: Market, market_book: MarketBook) -> bool:
        # process_market_book only executed if this returns True
        return False

    def process_market_book(self, market: Market, market_book: MarketBook) -> None:
        # process marketBook; place/cancel/replace orders
        return

    def process_raw_data(self, publish_time: int, datum: dict) -> None:
        return

    def process_race_card(self, race_card: RaceCard) -> None:
        # process raceCard object
        return

    def process_orders(self, market: Market, orders: list) -> None:
        # process list of Order objects for strategy and Market
        return

    def finish(self) -> None:
        # called before flumine ends
        return

    # order
    def place_order(self, market: Market, order) -> None:
        # get context
        market_context = self._invested.get(order.market_id)
        if market_context is None:
            self._invested[order.market_id] = market_context = {}
        runner_context = market_context.get(order.selection_id)
        if runner_context is None:
            market_context[order.selection_id] = runner_context = RunnerContext(
                order.selection_id
            )
        if self.validate_order(runner_context, order):
            runner_context.place()
            order.place()
            market.place_order(order)

    def cancel_order(self, market: Market, order, size_reduction: float = None) -> None:
        order.cancel(size_reduction)
        market.cancel_order(order)

    def update_order(self, market: Market, order, new_persistence_type: str) -> None:
        order.update(new_persistence_type)
        market.update_order(order)

    def replace_order(self, market: Market, order, new_price: float) -> None:
        order.replace(new_price)
        market.replace_order(order)

    def validate_order(self, runner_context: RunnerContext, order) -> bool:
        # todo multi/count
        if runner_context.invested:
            return False
        else:
            return True

    @property
    def stream_ids(self) -> list:
        return [stream.stream_id for stream in self.streams]

    @property
    def info(self) -> dict:
        return {
            "name": self.name,
            "market_filter": self.market_filter,
            "market_data_filter": self.market_data_filter,
            "streaming_timeout": self.streaming_timeout,
            "conflate_ms": self.conflate_ms,
            "stream_ids": self.stream_ids,
            "context": self.context,
        }

    @property
    def name(self) -> str:
        return self._name or self.__class__.__name__

    def __str__(self):
        return "{0}".format(self.name)


class Strategies:
    def __init__(self):
        self._strategies = []

    def __call__(self, strategy: BaseStrategy) -> None:
        self._strategies.append(strategy)
        strategy.add()

    def start(self) -> None:
        for s in self:
            s.start()

    def __iter__(self) -> Iterator[BaseStrategy]:
        return iter(self._strategies)

    def __len__(self) -> int:
        return len(self._strategies)