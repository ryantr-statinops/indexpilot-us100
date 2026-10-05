"""Ordered audit events; all values are measured at their event quote."""
from datetime import date
from .account import Account, Execution


def account_event(sequence: int, day: date, kind: str, account: Account, price: float, fee: float = 0., traded_notional: float = 0.) -> dict:
    return dict(sequence=sequence, date=day, kind=kind, price=price, cash=account.cash, holdings=account.holdings, equity=account.equity(price), exposure=account.exposure(price), fee=fee, traded_notional=traded_notional)


def order_record(sequence: int, day: date, execution: Execution, kind: str = 'rebalance') -> dict:
    return dict(sequence=sequence, date=day, kind=kind, price=execution.price, target=execution.target, delta_units=execution.delta_units, units_before=execution.before.holdings, units_after=execution.after.holdings, cash_before=execution.before.cash, cash_after=execution.after.cash, equity_before=execution.before.equity(execution.price), equity_after=execution.after.equity(execution.price), traded_notional=execution.traded_notional, fee=execution.fee)
