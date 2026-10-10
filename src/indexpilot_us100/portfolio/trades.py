"""Aggregate each uninterrupted position direction into one net-P&L trade."""

from datetime import date

from .account import Execution


class TradeTracker:
    def __init__(self):
        self.active = None
        self.closed: list[dict] = []

    def _open(self, day: date, direction: int, fee: float):
        self.active = dict(
            trade_id=len(self.closed), entry_date=day, direction=direction, gross_pnl=0.0, fees=fee
        )

    def _close(self, day: date):
        trade = self.active
        if trade is None:
            raise ValueError("No active trade to close")
        self.closed.append(
            {**trade, "exit_date": day, "net_pnl": trade["gross_pnl"] - trade["fees"]}
        )
        self.active = None

    def execute(self, day: date, execution: Execution):
        old = execution.before.holdings
        new = execution.after.holdings
        if execution.traded_notional == 0:
            return
        if old == 0 and new != 0:
            self._open(day, 1 if new > 0 else -1, execution.fee)
        elif old * new < 0:
            closing_fee = execution.fee * abs(old) / (abs(old) + abs(new))
            self.active["fees"] += closing_fee
            self._close(day)
            self._open(day, 1 if new > 0 else -1, execution.fee - closing_fee)
        elif old != 0:
            self.active["fees"] += execution.fee
            if new == 0:
                self._close(day)

    def accrue(self, pnl: float):
        if self.active is not None:
            self.active["gross_pnl"] += pnl
        elif pnl != 0:
            raise ValueError("Position P&L without an active trade")
