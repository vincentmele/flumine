# Design

### Main loop

Typical to most trading frameworks flumine uses an event driven design with the main thread handling these events through a FIFO [queue](https://docs.python.org/3/library/queue.html).

- handles all events in order one by one
- runs in __main__

### Events:

- `MARKET_CATALOGUE` Betfair MarketCatalogue object
- `MARKET_BOOK` Betfair MarketBook object
- `RAW_DATA` Raw streaming data
- *`CURRENT_ORDERS` Betfair CurrentOrders object*
- *`CLEARED_MARKETS` Betfair ClearedMarkets object*
- *`CLEARED_ORDERS` Betfair ClearedOrders object*

___

- `CLOSE_MARKET` flumine Close Market update
- *`STRATEGY_RESET` flumine Strategy Reset update*
- *`CUSTOM_EVENT` flumine Custom event update*
- `TERMINATOR` flumine End instance update

The above events are handled in the [flumine class]()

### MarketBook Cycle

### Backtesting

Backtesting is achieved by monkeypatching the datetime function utcnow(), this allows strategies to be simulated as if they were being executed in real time. Functions such as market.seconds_to_start and fillKill.seconds work as per a live execution.

### Streams
- Single stream (market)
- As above but 'data' (flumine listener)
- Order stream
- Future work:
    - Custom stream

### Strategy
- Class based
- Subscribe to streams
- Single strategy subscribes to a single market stream

### Handles
- Stream reconnect
- Trading client login/logout
- Trading client keep alive
- Future work:
    - Execution
        - place/cancel/replace/update
        - controls
        - fillKill
    - Market Catalogue
    - Polling (scores/raceCard etc)
    - CurrentOrders / ClearedOrders
    - database connection/logging



### notes
- market middleware (analytics/logging)
- order middleware (controls)
- paper trading
- back testing
