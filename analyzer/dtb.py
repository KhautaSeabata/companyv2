import numpy as np
from collections import deque

class DoubleTopBottomAnalyzer:
    def __init__(self, window_size=100, tolerance=0.01, retest_window=10):
        self.prices = deque(maxlen=window_size)
        self.times = deque(maxlen=window_size)
        self.tolerance = tolerance
        self.retest_window = retest_window

        self.pending_retest = None  # Track if waiting for retest

    def update(self, price, timestamp):
        self.prices.append(price)
        self.times.append(timestamp)

        if len(self.prices) < 20:
            return None

        # First handle retest logic
        signal = self.check_retest(price)
        if signal:
            signal["time"] = timestamp
            return signal

        # Then scan for double top/bottom pattern
        signal = self.detect_pattern()
        if signal:
            return signal

        return None

    def detect_pattern(self):
        prices = np.array(self.prices)
        highs = self.find_local_highs(prices)
        lows = self.find_local_lows(prices)

        if len(highs) >= 2:
            h1, h2 = highs[-2], highs[-1]
            mid = prices[h1 + (h2 - h1) // 2]
            if abs(prices[h1] - prices[h2]) / prices[h1] < self.tolerance:
                if prices[-1] < mid:  # Broken below the midline
                    self.pending_retest = {
                        "type": "double_top",
                        "entry_zone": mid,
                        "top_level": max(prices[h1], prices[h2]),
                        "bottom_level": min(prices[h1], prices[h2], prices[-1]),
                        "countdown": self.retest_window
                    }

        if len(lows) >= 2:
            l1, l2 = lows[-2], lows[-1]
            mid = prices[l1 + (l2 - l1) // 2]
            if abs(prices[l1] - prices[l2]) / prices[l1] < self.tolerance:
                if prices[-1] > mid:  # Broken above midline
                    self.pending_retest = {
                        "type": "double_bottom",
                        "entry_zone": mid,
                        "bottom_level": min(prices[l1], prices[l2]),
                        "top_level": max(prices[l1], prices[l2], prices[-1]),
                        "countdown": self.retest_window
                    }

        return None

    def check_retest(self, price):
        if not self.pending_retest:
            return None

        self.pending_retest["countdown"] -= 1
        if self.pending_retest["countdown"] <= 0:
            self.pending_retest = None
            return None

        entry_zone = self.pending_retest["entry_zone"]
        dist = abs(price - entry_zone) / entry_zone

        if dist < self.tolerance:
            signal_type = self.pending_retest["type"]
            self.pending_retest = None

            if signal_type == "double_top":
                entry = price
                tp = entry - (self.pending_retest["top_level"] - entry)
                sl = self.pending_retest["top_level"] * 1.01
                return {
                    "pattern": "Double Top (Confirmed)",
                    "entry": round(entry, 4),
                    "tp": round(tp, 4),
                    "sl": round(sl, 4)
                }

            elif signal_type == "double_bottom":
                entry = price
                tp = entry + (entry - self.pending_retest["bottom_level"])
                sl = self.pending_retest["bottom_level"] * 0.99
                return {
                    "pattern": "Double Bottom (Confirmed)",
                    "entry": round(entry, 4),
                    "tp": round(tp, 4),
                    "sl": round(sl, 4)
                }

        return None

    def find_local_highs(self, prices, order=3):
        return [i for i in range(order, len(prices) - order)
                if prices[i] == max(prices[i - order:i + order + 1])]

    def find_local_lows(self, prices, order=3):
        return [i for i in range(order, len(prices) - order)
                if prices[i] == min(prices[i - order:i + order + 1])]
