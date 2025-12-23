"""Minimal orderbook watcher showing top 5 levels and live spread."""

from __future__ import annotations

import argparse
import sys
import threading
import time
from typing import Dict, Iterable, Optional, Tuple

from weex_sdk import WeexWebSocket


def _format_number(value: Optional[float]) -> str:
    if value is None:
        return ""
    text = f"{value:.8f}".rstrip("0").rstrip(".")
    return text if text else "0"


def _parse_level(entry: object) -> Optional[Tuple[float, float]]:
    if isinstance(entry, dict):
        price = entry.get("price")
        size = entry.get("size")
    elif isinstance(entry, (list, tuple)) and len(entry) >= 2:
        price, size = entry[0], entry[1]
    else:
        return None

    try:
        return float(price), float(size)
    except (TypeError, ValueError):
        return None


class OrderBook:
    def __init__(self, levels: int = 5) -> None:
        self.levels = levels
        self.asks: Dict[float, float] = {}
        self.bids: Dict[float, float] = {}
        self.ready = False
        self.last_render = 0.0

    def apply_snapshot(self, asks: Iterable[object], bids: Iterable[object]) -> None:
        self.asks = self._build_side(asks)
        self.bids = self._build_side(bids)
        self.ready = True

    def apply_changes(self, asks: Iterable[object], bids: Iterable[object]) -> None:
        self._update_side(self.asks, asks)
        self._update_side(self.bids, bids)

    def best_prices(self) -> Tuple[Optional[float], Optional[float]]:
        if not self.asks or not self.bids:
            return None, None
        return min(self.asks), max(self.bids)

    def top_asks(self) -> Iterable[Tuple[float, float]]:
        return sorted(self.asks.items())[: self.levels]

    def top_bids(self) -> Iterable[Tuple[float, float]]:
        return sorted(self.bids.items(), key=lambda item: item[0], reverse=True)[: self.levels]

    def render(self, symbol: str) -> None:
        if not self.ready:
            return
        now = time.monotonic()
        if now - self.last_render < 0.2:
            return
        self.last_render = now

        best_ask, best_bid = self.best_prices()
        spread_text = (
            _format_number(best_ask - best_bid) if best_ask is not None and best_bid is not None else "N/A"
        )

        asks = list(self.top_asks())
        bids = list(self.top_bids())

        lines = [
            f"Symbol: {symbol}  Spread: {spread_text}",
            f"{'ASK':>14} {'SIZE':>14} | {'BID':>14} {'SIZE':>14}",
        ]
        for idx in range(self.levels):
            ask = asks[idx] if idx < len(asks) else None
            bid = bids[idx] if idx < len(bids) else None
            ask_price = _format_number(ask[0]) if ask else ""
            ask_size = _format_number(ask[1]) if ask else ""
            bid_price = _format_number(bid[0]) if bid else ""
            bid_size = _format_number(bid[1]) if bid else ""
            lines.append(f"{ask_price:>14} {ask_size:>14} | {bid_price:>14} {bid_size:>14}")

        sys.stdout.write("\033[H\033[J" + "\n".join(lines) + "\n")
        sys.stdout.flush()

    def _build_side(self, levels: Iterable[object]) -> Dict[float, float]:
        side: Dict[float, float] = {}
        for entry in levels:
            parsed = _parse_level(entry)
            if not parsed:
                continue
            price, size = parsed
            if size > 0:
                side[price] = size
        return side

    def _update_side(self, side: Dict[float, float], updates: Iterable[object]) -> None:
        for entry in updates:
            parsed = _parse_level(entry)
            if not parsed:
                continue
            price, size = parsed
            if size <= 0:
                side.pop(price, None)
            else:
                side[price] = size


def _run_self_test() -> None:
    book = OrderBook(levels=5)
    book.apply_snapshot(
        asks=[{"price": "101", "size": "1"}, {"price": "102", "size": "2"}],
        bids=[{"price": "99", "size": "3"}, {"price": "98", "size": "4"}],
    )
    best_ask, best_bid = book.best_prices()
    assert best_ask == 101.0
    assert best_bid == 99.0

    book.apply_changes(
        asks=[{"price": "101", "size": "0"}, {"price": "103", "size": "5"}],
        bids=[{"price": "98", "size": "0"}, {"price": "100", "size": "6"}],
    )
    asks = dict(book.top_asks())
    bids = dict(book.top_bids())
    assert 101.0 not in asks
    assert asks[103.0] == 5.0
    assert 98.0 not in bids
    assert bids[100.0] == 6.0
    print("self-test ok")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Minimal orderbook watcher")
    parser.add_argument("--symbol", default="cmt_btcusdt", help="Trading pair symbol")
    parser.add_argument("--levels", type=int, default=5, help="Levels to display")
    parser.add_argument("--self-test", action="store_true", help="Run built-in checks and exit")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.self_test:
        _run_self_test()
        return

    book = OrderBook(levels=max(1, args.levels))
    ws = WeexWebSocket(is_private=False)

    def on_depth(message: Dict[str, object]) -> None:
        data_list = message.get("data") if isinstance(message, dict) else None
        if not data_list:
            return
        for payload in data_list:
            if not isinstance(payload, dict):
                continue
            depth_type = payload.get("depthType")
            asks = payload.get("asks", [])
            bids = payload.get("bids", [])
            if depth_type == "SNAPSHOT" or not book.ready:
                book.apply_snapshot(asks, bids)
            else:
                book.apply_changes(asks, bids)
        book.render(args.symbol)

    thread = threading.Thread(target=ws.connect, daemon=True)
    thread.start()

    start_time = time.monotonic()
    while not ws.connected:
        if time.monotonic() - start_time > 10:
            ws.close()
            raise RuntimeError("WebSocket connection timeout")
        time.sleep(0.1)

    ws.subscribe_depth(args.symbol, limit=15, callback=on_depth)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        ws.close()


if __name__ == "__main__":
    main()
