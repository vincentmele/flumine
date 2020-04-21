from typing import Iterator

from .market import Market


class Markets:
    def __init__(self):
        self._markets = {}  # marketId: <Market>

    def add_market(self, market_id: str, live_market: Market) -> None:
        if market_id in self._markets:
            self._markets[market_id].open_market()
        else:
            self._markets[market_id] = live_market

    def close_market(self, market_id: str) -> Market:
        live_market = self._markets[market_id]
        live_market.close_market()
        return live_market

    def get_order(self, market_id: str, customer_order_ref: str):
        try:
            return self.markets[market_id].blotter[customer_order_ref]
        except KeyError:
            return

    @property
    def markets(self) -> dict:
        return {
            key: value for key, value in self._markets.items() if value.closed is False
        }

    @property
    def open_market_ids(self) -> list:
        return list(self.markets.keys())

    @property
    def live_orders(self) -> bool:
        for market in self:
            if market.closed is False and market.blotter.live_orders is True:
                return True
        return False

    def __iter__(self) -> Iterator[Market]:
        return iter(self.markets.values())

    def __len__(self) -> int:
        return len(self.markets)