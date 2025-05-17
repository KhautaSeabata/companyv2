import numpy as np
from collections import deque

class TrendlineAnalyzer:
    def __init__(self, window_size=100, tolerance=0.01, min_points=3, retest_window=10):
        self.prices = deque(maxlen=window_size)
        self.times = deque(maxlen=window_size)
        self.tolerance = tolerance
        self.min_points = min_points
        self.retest_window = retest_window

        self.trend = "sideways"
        self.support_points = []
        self.resistance_points = []

        # Retest logic
        self.pending_retest = None  # Dict: {type, level, triggered}

    def update(self, price, timestamp):
        self.prices.append(price)
        self.times.append(timestamp)

        if len(self.prices) < self.min_points:
            return None

        self.identify_trend()
        self.find_trendlines()

        # Check if we are waiting for a retest
        signal = self.check_retest(price)
        if signal:
            signal["time"] = timestamp
            return signal

        # Check breakout or bounce (only if no retest is pending)
        if not self.pending_retest:
            signal = self.check_signals(price)
            if signal:
                signal["time"] = timestamp
                return signal
        return None

    def identify_trend(self):
        prices = np.array(self.prices)
        highs = self.find_local_highs(prices)
        lows = self.find_local_lows(prices)

        is_uptrend = all(prices[highs[i]] < prices[highs[i + 1]] for i in range(len(highs) - 1)) and \
                     all(prices[lows[i]] < prices[lows[i + 1]] for i in range(len(lows) - 1))

        is_downtrend = all(prices[highs[i]] > prices[highs[i + 1]] for i in range(len(highs) - 1)) and \
                       all(prices[lows[i]] > prices[lows[i + 1]] for i in range(len(lows) - 1))

        if is_uptrend:
            self.trend = "uptrend"
        elif is_downtrend:
            self.trend = "downtrend"
        else:
            self.trend = "sideways"

    def find_trendlines(self):
        prices = np.array(self.prices)
        times = np.arange(len(prices))

        if self.trend == "uptrend":
            lows_idx = self.find_local_lows(prices)
            if len(lows_idx) >= 2:
                self.support_points = [(times[i], prices[i]) for i in lows_idx]
                self.support_slope, self.support_intercept = self.linear_fit(lows_idx, prices)
            else:
                self.support_slope = self.support_intercept = None

        elif self.trend == "downtrend":
            highs_idx = self.find_local_highs(prices)
            if len(highs_idx) >= 2:
                self.resistance_points = [(times[i], prices[i]) for i in highs_idx]
                self.resistance_slope, self.resistance_intercept = self.linear_fit(highs_idx, prices)
            else:
                self.resistance_slope = self.resistance_intercept = None

    def check_signals(self, current_price):
        idx = len(self.prices) - 1

        # Check breakout from support
        if self.trend == "uptrend" and self.support_slope is not None:
            expected_support = self.support_slope * idx + self.support_intercept

            if current_price < expected_support * (1 - self.tolerance):
                # breakout down, wait for retest
                self.pending_retest = {
                    "type": "support_break",
                    "level": expected_support,
                    "countdown": self.retest_window
                }

        # Check breakout from resistance
        if self.trend == "downtrend" and self.resistance_slope is not None:
            expected_resistance = self.resistance_slope * idx + self.resistance_intercept

            if current_price > expected_resistance * (1 + self.tolerance):
                # breakout up, wait for retest
                self.pending_retest = {
                    "type": "resistance_break",
                    "level": expected_resistance,
                    "countdown": self.retest_window
                }

        return None

    def check_retest(self, price):
        """Wait for retest after breakout"""
        if not self.pending_retest:
            return None

        level = self.pending_retest["level"]
        self.pending_retest["countdown"] -= 1

        if self.pending_retest["countdown"] <= 0:
            self.pending_retest = None
            return None

        dist = abs(price - level) / level
        if dist < self.tolerance:
            # Retest confirmed
            signal_type = self.pending_retest["type"]
            self.pending_retest = None

            if signal_type == "support_break":
                tp = price - abs(price - level) * 2
                sl = level * 1.01
                return {
                    "pattern": "Retest after Support Break",
                    "entry": round(price, 4),
                    "tp": round(tp, 4),
                    "sl": round(sl, 4),
                    "trend": self.trend
                }

            elif signal_type == "resistance_break":
                tp = price + abs(price - level) * 2
                sl = level * 0.99
                return {
                    "pattern": "Retest after Resistance Break",
                    "entry": round(price, 4),
                    "tp": round(tp, 4),
                    "sl": round(sl, 4),
                    "trend": self.trend
                }

        return None

    def linear_fit(self, indices, prices):
        x = np.array(indices)
        y = prices[x]
        A = np.vstack([x, np.ones(len(x))]).T
        return np.linalg.lstsq(A, y, rcond=None)[0]

    def find_local_highs(self, prices, order=3):
        return [i for i in range(order, len(prices) - order)
                if prices[i] == max(prices[i - order:i + order + 1])]

    def find_local_lows(self, prices, order=3):
        return [i for i in range(order, len(prices) - order)
                if prices[i] == min(prices[i - order:i + order + 1])]
