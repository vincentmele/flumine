import unittest
from unittest import mock

from flumine.order.order import OrderStatus, OrderTypes

from betfairlightweight.resources.bettingresources import PriceSize

from flumine import config
from flumine.markets.market import Market
from flumine.markets.markets import Markets
from flumine.order.order import (
    BaseOrder,
    BetfairOrder,
)
from flumine.order import process
from flumine.strategy.strategy import Strategies
from flumine.utils import create_cheap_hash


class BaseOrderTest(unittest.TestCase):
    def setUp(self) -> None:
        mock_client = mock.Mock(paper_trade=False)
        self.mock_trade = mock.Mock(client=mock_client)
        self.mock_order_type = mock.Mock()
        self.order = BaseOrder(self.mock_trade, "BACK", self.mock_order_type, 1)
        config.simulated = True

    def tearDown(self) -> None:
        config.simulated = False

    def test_process_current_orders_with_default_sep(self):
        mock_log_control = mock.Mock()
        mock_add_market = mock.Mock()
        market_book = mock.Mock()
        markets = Markets()
        market = Market(
            flumine=mock.Mock(), market_id="market_id", market_book=market_book
        )
        markets.add_market("market_id", market)
        strategies = Strategies()
        cheap_hash = create_cheap_hash("strategy_name", 13)
        trade = mock.Mock(market_id="market_id")
        trade.strategy.name_hash = cheap_hash
        current_order = mock.Mock(
            customer_order_ref=f"{cheap_hash}I123", market_id="market_id", bet_id=None
        )
        betfair_order = BetfairOrder(trade=trade, side="BACK", order_type=mock.Mock())
        betfair_order.id = "123"
        market.blotter = {"123": betfair_order}
        event = mock.Mock(event=[mock.Mock(orders=[current_order])])

        process.process_current_orders(
            markets=markets,
            strategies=strategies,
            event=event,
            log_control=mock_log_control,
            add_market=mock_add_market,
        )
        self.assertEqual(current_order, betfair_order.responses.current_order)

    def test_process_current_order(self):
        mock_order = mock.Mock(status=OrderStatus.EXECUTABLE)
        mock_order.current_order.status = "EXECUTION_COMPLETE"
        mock_current_order = mock.Mock()
        mock_log_control = mock.Mock()
        process.process_current_order(mock_order, mock_current_order, mock_log_control)
        mock_order.update_current_order.assert_called_with(mock_current_order)
        mock_order.execution_complete.assert_called()

    def test_create_order_from_current(self):
        mock_add_market = mock.Mock()
        market_book = mock.Mock()
        markets = Markets()
        market = Market(
            flumine=mock.Mock(), market_id="market_id", market_book=market_book
        )
        markets.add_market("market_id", market)
        cheap_hash = create_cheap_hash("strategy_name", 13)
        strategy = mock.Mock(name_hash=cheap_hash)
        strategies = Strategies()
        strategies(strategy=strategy, client=mock.Mock())
        current_order = mock.Mock(
            customer_order_ref=f"{cheap_hash}I123",
            market_id="market_id",
            bet_id=None,
            selection_id="selection_id",
            handicap="handicap",
            order_type="LIMIT",
            price_size=PriceSize(price=10.0, size=2.0),
            persistence_type="LAPSE",
        )

        new_order = process.create_order_from_current(
            markets=markets,
            strategies=strategies,
            current_order=current_order,
            add_market=mock_add_market,
        )
        self.assertEqual(market.blotter["123"], new_order)
        self.assertEqual(new_order.market_id, "market_id")
        self.assertEqual(new_order.selection_id, "selection_id")
        self.assertEqual(new_order.handicap, "handicap")
        self.assertEqual(new_order.order_type.ORDER_TYPE, OrderTypes.LIMIT)
        self.assertEqual(new_order.order_type.size, 2.0)
        self.assertEqual(new_order.order_type.price, 10.0)
