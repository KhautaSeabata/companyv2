import numpy as np
from collections import deque

class HeadShouldersAnalyzer:
    def __init__(self, window_size=100, tolerance=0.015, retest_window=10):
        self.prices = deque(maxlen=window_size)
        self.times = deque(maxlen=window_size)
        self.tolerance = tolerance
        self.retest_window = retest_window
        self.pending_retest = None  # Stores pattern after breakout for retest confirmation

    def update(self, price, timestamp):
        self.prices.append(price)
        self.times.append(timestamp)

        if len(self.prices) < 20:
            return None

        # 1. Handle breakout retest check
        signal = self.check_retest(price)
        if signal:
            signal["time"] = timestamp
            return signal

        # 2. Scan for new Head and Shoulders pattern
        return self.detect_pattern()

    def detect_pattern(self):
        prices = np.array(self.prices)
        highs = self.find_local_highs(prices)
        lows = self.find_local_lows(prices)

        if len(highs) >= 3:
            l, h, r = highs[-3], highs[-2], highs[-1]
            if h > prices[l] and h > prices[r] and abs(prices[l] - prices[r]) / prices[h] < self.tolerance:
                # Neckline
                neckline = (prices[l] + prices[r]) / 2
                if prices[-1] < neckline:  # Broke below neckline
                    self.pending_retest = {
                        "type": "head_and_shoulders",
                        "neckline": neckline,
                        "head": prices[h],
                        "direction": "down",
                        "countdown": self.retest_window
                    }

        elif len(lows) >= 3:
            l, h, r = lows[-3], lows[-2], lows[-1]
            if h < prices[l] and h < prices[r] and abs(prices[l] - prices[r]) / prices[h] < self.tolerance:
                neckline = (prices[l] + prices[r]) / 2
                if prices[-1] > neckline:  # Broke above neckline
                    self.pending_retest = {
                        "type": "inverse_head_and_shoulders",
                        "neckline": neckline,
                        "head": prices[h],
                        "direction": "up",
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

        neckline = self.pending_retest["neckline"]
        head = self.pending_retest["head"]
        direction = self.pending_retest["direction"]

        if abs(price - neckline) / neckline < self.tolerance:
            self.pending_retest = None
            entry = price

            if direction == "down":
                tp = entry - (head - neckline)
                sl = head * 1.01
                return {
                    "pattern": "Head and Shoulders",
                    "entry": round(entry, 4),
                    "tp": round(tp, 4),
                    "sl": round(sl, 4)
                }

            elif direction == "up":
                tp = entry + (neckline - head)
                sl = head * 0.99
                return {
                    "pattern": "Inverse Head and Shoulders",
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
