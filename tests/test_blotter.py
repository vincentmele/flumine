import unittest
from unittest import mock

from flumine.markets.blotter import Blotter
from flumine.order.order import OrderStatus
from flumine.order.ordertype import MarketOnCloseOrder, LimitOrder, LimitOnCloseOrder


class BlotterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.blotter = Blotter("1.23")

    def test_init(self):
        self.assertEqual(self.blotter.market_id, "1.23")
        self.assertEqual(self.blotter._orders, {})
        self.assertEqual(self.blotter._live_orders, [])
        self.assertEqual(self.blotter._trades, {})
        self.assertEqual(self.blotter._strategy_orders, {})
        self.assertEqual(self.blotter._strategy_selection_orders, {})

    def test_strategy_orders(self):
        mock_order = mock.Mock(lookup=(1, 2, 3))
        mock_order.trade.strategy = 69
        self.blotter["12345"] = mock_order
        self.assertEqual(self.blotter.strategy_orders(12), [])
        self.assertEqual(self.blotter.strategy_orders(69), [mock_order])

    def test_strategy_selection_orders(self):
        mock_order = mock.Mock(lookup=(1, 2, 3))
        mock_order.trade.strategy = 69
        self.blotter["12345"] = mock_order
        self.assertEqual(self.blotter.strategy_selection_orders(12, 2, 3), [])
        self.assertEqual(self.blotter.strategy_selection_orders(69, 2, 3), [mock_order])

    def test_live_orders(self):
        self.assertEqual(list(self.blotter.live_orders), [])
        mock_order = mock.Mock(complete=False)
        self.blotter._live_orders = [mock_order]
        self.assertEqual(list(self.blotter.live_orders), [mock_order])

    def test_has_live_orders(self):
        self.assertFalse(self.blotter.has_live_orders)
        self.blotter._live_orders = [mock.Mock()]
        self.assertTrue(self.blotter.has_live_orders)

    def test_process_closed_market(self):
        mock_market_book = mock.Mock(number_of_winners=1)
        mock_runner = mock.Mock(selection_id=123, handicap=0.0)
        mock_market_book.runners = [mock_runner]
        mock_order = mock.Mock(selection_id=123, handicap=0.0)
        self.blotter._orders = {"12345": mock_order}
        self.blotter.process_closed_market(mock_market_book)
        self.assertEqual(mock_order.runner_status, mock_runner.status)

    def test_process_cleared_orders(self):
        mock_cleared_orders = mock.Mock()
        mock_cleared_orders.orders = []
        self.assertEqual(self.blotter.process_cleared_orders(mock_cleared_orders), [])

    def test_selection_exposure(self):
        """
        Check that selection_exposure returns the absolute worse loss
        """

        def get_exposures(strategy, lookup):
            if strategy == "strategy" and lookup == (1, 2, 3):
                return {
                    "worst_possible_profit_on_win": -1.0,
                    "worst_possible_profit_on_lose": -2.0,
                }

        self.blotter.get_exposures = mock.Mock(side_effect=get_exposures)

        result = self.blotter.selection_exposure("strategy", (1, 2, 3))

        self.assertEqual(2.0, result)

    def test_selection_exposure2(self):
        """
        Check that selection_exposure returns zero if there is no risk of loss.
        """

        def get_exposures(strategy, lookup):
            if strategy == "strategy" and lookup == (1, 2, 3):
                return {
                    "worst_possible_profit_on_win": 0.0,
                    "worst_possible_profit_on_lose": 1.0,
                }

        self.blotter.get_exposures = mock.Mock(side_effect=get_exposures)

        result = self.blotter.selection_exposure("strategy", (1, 2, 3))

        self.assertEqual(0.0, result)

    def test_get_exposures(self):
        mock_strategy = mock.Mock()
        mock_trade = mock.Mock(strategy=mock_strategy)
        mock_order = mock.Mock(
            trade=mock_trade,
            lookup=(self.blotter.market_id, 123, 0),
            side="BACK",
            average_price_matched=5.6,
            size_matched=2.0,
            size_remaining=0.0,
            order_type=LimitOrder(price=5.6, size=2.0),
        )
        self.blotter["12345"] = mock_order
        self.assertEqual(
            self.blotter.get_exposures(mock_strategy, mock_order.lookup),
            {
                "matched_profit_if_lose": -2.0,
                "matched_profit_if_win": 9.2,
                "worst_possible_profit_on_lose": -2.0,
                "worst_possible_profit_on_win": 9.2,
                "worst_potential_unmatched_profit_if_lose": 0.0,
                "worst_potential_unmatched_profit_if_win": 0.0,
            },
        )

    def test_get_exposures_with_exclusion(self):
        mock_strategy = mock.Mock()
        mock_trade = mock.Mock(strategy=mock_strategy)
        mock_order = mock.Mock(
            trade=mock_trade,
            lookup=(self.blotter.market_id, 123, 0),
            side="BACK",
            average_price_matched=5.6,
            size_matched=2.0,
            size_remaining=0.0,
            order_type=LimitOrder(price=5.6, size=2.0),
        )
        mock_order_excluded = mock.Mock(
            trade=mock_trade,
            lookup=(self.blotter.market_id, 123, 0),
            side="BACK",
            average_price_matched=5.6,
            size_matched=2.0,
            size_remaining=0.0,
            order_type=LimitOrder(price=5.6, size=2.0),
        )
        self.blotter["12345"] = mock_order
        self.blotter["67890"] = mock_order_excluded
        self.assertEqual(
            self.blotter.get_exposures(
                mock_strategy, mock_order.lookup, exclusion=mock_order_excluded
            ),
            {
                "matched_profit_if_lose": -2.0,
                "matched_profit_if_win": 9.2,
                "worst_possible_profit_on_lose": -2.0,
                "worst_possible_profit_on_win": 9.2,
                "worst_potential_unmatched_profit_if_lose": 0.0,
                "worst_potential_unmatched_profit_if_win": 0.0,
            },
        )

    def test_get_exposures_value_error(self):
        mock_strategy = mock.Mock()
        mock_trade = mock.Mock(strategy=mock_strategy)
        mock_order = mock.Mock(
            trade=mock_trade,
            lookup=(self.blotter.market_id, 123, 0),
            side="BACK",
            average_price_matched=5.6,
            size_matched=2.0,
            size_remaining=0.0,
            order_type=mock.Mock(ORDER_TYPE="INVALID"),
        )
        self.blotter["12345"] = mock_order

        with self.assertRaises(ValueError) as e:
            self.blotter.get_exposures(mock_strategy, mock_order.lookup)

        self.assertEqual("Unexpected order type: INVALID", e.exception.args[0])

    def test_get_exposures_with_price_none(self):
        """
        Check that get_exposures works if order.order_type.price is None.
        If order.order_type.price is None, the controls will flag the order as a violation
        and it won't be set to the exchange, so there won't be any exposure and we can ignore it.
        """
        mock_strategy = mock.Mock()
        mock_trade = mock.Mock(strategy=mock_strategy)
        lookup = (self.blotter.market_id, 123, 0)
        mock_order1 = mock.Mock(
            trade=mock_trade,
            lookup=lookup,
            side="BACK",
            average_price_matched=5.6,
            size_matched=2.0,
            size_remaining=0.0,
            order_type=LimitOrder(price=5.6, size=2.0),
        )
        mock_order2 = mock.Mock(
            trade=mock_trade,
            lookup=lookup,
            side="LAY",
            average_price_matched=5.6,
            size_matched=0.0,
            size_remaining=2.0,
            order_type=LimitOrder(price=None, size=2.0),
        )
        self.blotter["12345"] = mock_order1
        self.blotter["23456"] = mock_order2
        self.assertEqual(
            self.blotter.get_exposures(mock_strategy, lookup),
            {
                "matched_profit_if_lose": -2.0,
                "matched_profit_if_win": 9.2,
                "worst_possible_profit_on_lose": -2.0,
                "worst_possible_profit_on_win": 9.2,
                "worst_potential_unmatched_profit_if_lose": 0.0,
                "worst_potential_unmatched_profit_if_win": 0.0,
            },
        )

    def test_get_exposures_no_match(self):
        mock_strategy = mock.Mock()
        mock_trade = mock.Mock(strategy=mock_strategy)
        mock_order = mock.Mock(
            trade=mock_trade,
            lookup=(self.blotter.market_id, 123, 0),
            side="BACK",
            average_price_matched=5.6,
            size_matched=0.0,
            size_remaining=0.0,
            order_type=LimitOrder(price=5.6, size=2.0),
        )
        self.blotter["12345"] = mock_order
        self.assertEqual(
            self.blotter.get_exposures(mock_strategy, mock_order.lookup),
            {
                "matched_profit_if_lose": 0.0,
                "matched_profit_if_win": 0.0,
                "worst_possible_profit_on_lose": 0.0,
                "worst_possible_profit_on_win": 0.0,
                "worst_potential_unmatched_profit_if_lose": 0.0,
                "worst_potential_unmatched_profit_if_win": 0.0,
            },
        )

    def test_get_exposures_from_unmatched_back(self):
        mock_strategy = mock.Mock()
        mock_trade = mock.Mock(strategy=mock_strategy)
        mock_order = mock.Mock(
            trade=mock_trade,
            lookup=(self.blotter.market_id, 123, 0),
            side="BACK",
            average_price_matched=5.6,
            size_matched=2.0,
            size_remaining=2.0,
            order_type=LimitOrder(price=6, size=4.0),
        )
        self.blotter["12345"] = mock_order
        # On the win side, we have 2.0 * (5.6-1.0) = 9.2
        # On the lose side, we have -2.0-2.0=-4.0
        self.assertEqual(
            self.blotter.get_exposures(mock_strategy, mock_order.lookup),
            {
                "matched_profit_if_lose": -2.0,
                "matched_profit_if_win": 9.2,
                "worst_possible_profit_on_lose": -4.0,
                "worst_possible_profit_on_win": 9.2,
                "worst_potential_unmatched_profit_if_lose": -2.0,
                "worst_potential_unmatched_profit_if_win": 0,
            },
        )

    def test_get_exposures_from_unmatched_lay(self):
        mock_strategy = mock.Mock()
        mock_trade = mock.Mock(strategy=mock_strategy)
        mock_order = mock.Mock(
            trade=mock_trade,
            lookup=(self.blotter.market_id, 123, 0),
            side="LAY",
            average_price_matched=5.6,
            size_matched=2.0,
            size_remaining=2.0,
            order_type=LimitOrder(price=6, size=4.0),
        )
        self.blotter["12345"] = mock_order
        # On the win side, we have -2.0 * (5.6-1.0) -2.0 * (6.0-1.0) = -19.2
        # On the lose side, we have 2.0 from size_matched
        self.assertEqual(
            self.blotter.get_exposures(mock_strategy, mock_order.lookup),
            {
                "matched_profit_if_lose": 2.0,
                "matched_profit_if_win": -9.2,
                "worst_possible_profit_on_lose": 2.0,
                "worst_possible_profit_on_win": -19.2,
                "worst_potential_unmatched_profit_if_lose": 0,
                "worst_potential_unmatched_profit_if_win": -10.0,
            },
        )

    def test_get_exposures_from_market_on_close_back(self):
        mock_strategy = mock.Mock()
        mock_trade = mock.Mock(strategy=mock_strategy)
        mock_order = mock.Mock(
            trade=mock_trade,
            lookup=(self.blotter.market_id, 123, 0),
            side="BACK",
            order_type=MarketOnCloseOrder(liability=10.0),
        )
        self.blotter["12345"] = mock_order
        self.assertEqual(
            self.blotter.get_exposures(mock_strategy, mock_order.lookup),
            {
                "matched_profit_if_lose": 0.0,
                "matched_profit_if_win": 0.0,
                "worst_possible_profit_on_lose": -10.0,
                "worst_possible_profit_on_win": 0.0,
                "worst_potential_unmatched_profit_if_lose": 0.0,
                "worst_potential_unmatched_profit_if_win": 0.0,
            },
        )

    def test_get_exposures_from_market_on_close_lay(self):
        mock_strategy = mock.Mock()
        mock_trade = mock.Mock(strategy=mock_strategy)
        mock_order = mock.Mock(
            trade=mock_trade,
            lookup=(self.blotter.market_id, 123, 0),
            side="LAY",
            order_type=MarketOnCloseOrder(liability=10.0),
        )
        self.blotter["12345"] = mock_order
        self.assertEqual(
            self.blotter.get_exposures(mock_strategy, mock_order.lookup),
            {
                "matched_profit_if_lose": 0.0,
                "matched_profit_if_win": 0.0,
                "worst_possible_profit_on_lose": 0.0,
                "worst_possible_profit_on_win": -10.0,
                "worst_potential_unmatched_profit_if_lose": 0.0,
                "worst_potential_unmatched_profit_if_win": 0.0,
            },
        )

    def test_get_exposures_from_limit_on_close_lay(self):
        mock_strategy = mock.Mock()
        mock_trade = mock.Mock(strategy=mock_strategy)
        mock_order = mock.Mock(
            trade=mock_trade,
            lookup=(self.blotter.market_id, 123, 0),
            side="LAY",
            order_type=LimitOnCloseOrder(price=1.01, liability=10.0),
        )
        self.blotter["12345"] = mock_order
        self.assertEqual(
            self.blotter.get_exposures(mock_strategy, mock_order.lookup),
            {
                "matched_profit_if_lose": 0.0,
                "matched_profit_if_win": 0.0,
                "worst_possible_profit_on_lose": 0.0,
                "worst_possible_profit_on_win": -10.0,
                "worst_potential_unmatched_profit_if_lose": 0.0,
                "worst_potential_unmatched_profit_if_win": 0.0,
            },
        )

    def test_get_exposures_voided(self):
        mock_strategy = mock.Mock()
        mock_trade = mock.Mock(strategy=mock_strategy)
        mock_order = mock.Mock(
            trade=mock_trade,
            lookup=(self.blotter.market_id, 123, 0),
            side="BACK",
            order_type=LimitOrder(price=5, size=10.0),
            status=OrderStatus.VIOLATION,
        )
        self.blotter["12345"] = mock_order
        self.assertEqual(
            self.blotter.get_exposures(mock_strategy, mock_order.lookup),
            {
                "matched_profit_if_lose": 0.0,
                "matched_profit_if_win": 0.0,
                "worst_possible_profit_on_lose": 0.0,
                "worst_possible_profit_on_win": 0.0,
                "worst_potential_unmatched_profit_if_lose": 0.0,
                "worst_potential_unmatched_profit_if_win": 0.0,
            },
        )

    def test_complete_order(self):
        self.blotter._live_orders = ["test"]
        self.blotter.complete_order("test")

    def test_has_trade(self):
        self.assertFalse(self.blotter.has_trade("123"))
        self.blotter._trades["123"].append(1)
        self.assertTrue(self.blotter.has_trade("123"))

    def test__contains(self):
        self.blotter._orders = {"123": "test"}
        self.assertIn("123", self.blotter)
        self.assertNotIn("321", self.blotter)

    def test__setitem(self):
        mock_order = mock.Mock(lookup=(1, 2, 3))
        self.blotter["123"] = mock_order
        self.assertEqual(self.blotter._orders, {"123": mock_order})
        self.assertEqual(self.blotter._live_orders, [mock_order])
        self.assertEqual(self.blotter._trades, {mock_order.trade.id: [mock_order]})
        self.assertEqual(
            self.blotter._strategy_orders, {mock_order.trade.strategy: [mock_order]}
        )
        self.assertEqual(
            self.blotter._strategy_selection_orders,
            {(mock_order.trade.strategy, 2, 3): [mock_order]},
        )

    def test__getitem(self):
        self.blotter._orders = {"12345": "test", "54321": "test2"}
        self.assertEqual(self.blotter["12345"], "test")
        self.assertEqual(self.blotter["54321"], "test2")

    def test__len(self):
        self.blotter._orders = {"12345": "test", "54321": "test"}
        self.assertEqual(len(self.blotter), 2)
