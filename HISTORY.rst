.. :changelog:

Release History
---------------

1.6.7 (2020-06-08)
+++++++++++++++++++

**Improvements**

- #185 cleared orders meta implemented
- Order.elapsed_seconds_executable added

1.6.6 (2020-06-08)
+++++++++++++++++++

**Improvements**

- Error handling added to logging control

**Bug Fixes**

- Incorrect event type passed to log_control

1.6.5 (2020-06-08)
+++++++++++++++++++

**Improvements**

- #205 MarketBook publishTime added to simulated.matched / order.execution_complete time added
- Controls error message added
- Info properties improved
- Order/Trade .complete refactored

**Bug Fixes**

- Log order moved to after execution (missing betId)

1.6.4 (2020-06-08)
+++++++++++++++++++

**Improvements**

- Client passed in AccountBalance event
- PublishTime added to order (MarketBook)
- GH Actions fixed

1.6.3 (2020-06-03)
+++++++++++++++++++

**Improvements**

- #178 Client order stream disable/enable
- #179 Info properties

**Bug Fixes**

- #191 missing git config

1.6.2 (2020-06-03)
+++++++++++++++++++

**Improvements**

- #191 Github actions added for testing and deployment

1.6.1 (2020-06-02)
+++++++++++++++++++

**Bug Fixes**

- #195 refactor to prevent RuntimeError

1.6.0 (2020-06-02)
+++++++++++++++++++

**Improvements**

- #175 Update/Replace simulated handling
- Trade context manager added

**Bug Fixes**

- #163 selection exposure improvement
- BetfairExecution replace bugfix

1.5.7 (2020-06-01)
+++++++++++++++++++

**Bug Fixes**

- Sentry uses name in extra so do not override.

1.5.6 (2020-06-01)
+++++++++++++++++++

**Improvements**

- #186 Error handling when calling strategy functions
- Start delay bumped on workers and name changed
- Minor typos / cleanups

1.5.5 (2020-05-29)
+++++++++++++++++++

**Improvements**

- Missing Middleware inheritance
- get_sp added

**Bug Fixes**

- MarketCatalogue missing from Market when logged

1.5.4 (2020-05-22)
+++++++++++++++++++

**Bug Fixes**

- Market close bug

1.5.3 (2020-05-22)
+++++++++++++++++++

**Improvements**

- Market properties added

**Bug Fixes**

- Memory leak in historical stream fixed (queue)
- process_closed_market bug fix in process logic

1.5.2 (2020-05-21)
+++++++++++++++++++

**Bug Fixes**

- pypi bug?

1.5.1 (2020-05-21)
+++++++++++++++++++

**Improvements**

- Worker refactor to make init simpler when adding custom workers

1.5.0 (2020-05-21)
+++++++++++++++++++

**Improvements**

- Logging control added and integrated
- PriceRecorder example added
- Balance polling added
- Cleared Orders/Market polling added
- Trade.notes added
- Middleware moved to flumine level
- SimulatedMiddleware refactored to handle all logic
- Context added to worker functionality

1.4.0 (2020-05-13)
+++++++++++++++++++

**Improvements**

- Simulated execution created (place/cancel only)
- Backtest simulation created and integrated
- patching added, major speed improvements

**Bug Fixes**

- Handicap missing from order
- Client update account details added
- Replace/Update `update_data` fix (now cleared)

**Libraries**

- betfairlightweight upgraded to 2.3.1

1.3.0 (2020-04-28)
+++++++++++++++++++

**Improvements**

- BetfairExecution now live (place/cancel/update/replace)
- Trading and Client controls now live
- Trade/Order logic created and integrated
- OrderPackage created for execution
- Market class created
- process.py created to handle order/trade logic and linking
- Market catalogue worker added
- Blotter created with some initial functions (selection_exposure)
- Strategy runner_context added to handle selection investment
- OrderStream created and integrated

**Bug Fixes**

- Error handling on keep_alive worker added

**Libraries**

- requests added as dependency

1.2.0 (2020-04-06)
+++++++++++++++++++

**Improvements**

- Backtest added and HistoricalStream refactor (single threaded)
- Flumine clients created and integrated
- MarketCatalogue polling worker added

**Libraries**

- betfairlightweight upgraded to 2.3.0

1.1.0 (2020-03-09)
+++++++++++++++++++

**Improvements**

- `context` added to strategy
- `.start` / `.add` refactored to make more sense
- HistoricalStream added and working but will change in the future to not use threads (example added)

**Libraries**

- betfairlightweight upgraded to 2.1.0

1.0.0 (2020-03-02)
+++++++++++++++++++

**Improvements**

- Refactor to trading framework / engine
- Remove recorder/storage engine and replace with 'strategies'
- Market and data streams added
- Background worker class added
- Add docs
- exampleone added

**Libraries**

- betfairlightweight upgraded to 2.0.1
- Add tenacity 5.0.3
- Add python-json-logger 0.1.11

0.9.0 (2020-01-06)
+++++++++++++++++++

**Improvements**

- py3.7/3.8 testing and Black fmt
- main.py update to remove flumine hardcoding
- Remove docker and change to 'main.py' example
- Refactor to local_dir so that it can be overwritten

**Bug Fixes**

- File only loaded if < than 1 line
- FLUMINE_DATA updated to /tmp to prevent permission issues

**Libraries**

- betfairlightweight upgraded to 1.10.4
- Add py3.8 support

0.8.1 (2019-09-30)
+++++++++++++++++++

**Improvements**

- logging improvements (exc_info)
- Python 3.4 removed and 3.7 support added

**Libraries**

- betfairlightweight upgraded to 1.10.3

0.8.0 (2019-09-09)
+++++++++++++++++++

**Improvements**

- black fmt
- _async renamed to async_ to match bflw
- py3.7 added to travis
- #28 readme update

**Libraries**

- betfairlightweight upgraded to 1.10.2
