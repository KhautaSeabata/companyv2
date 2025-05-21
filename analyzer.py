from collections import deque
import numpy as np

class Analyzer:
    def __init__(self, maxlen=200, sma_window=10, tp_pct=0.01, sl_pct=0.005):
        self.prices = deque(maxlen=maxlen)
        self.timestamps = deque(maxlen=maxlen)
        self.last_signal = None  # 'buy' or 'sell' or None
        self.sma_window = sma_window
        self.tp_pct = tp_pct
        self.sl_pct = sl_pct

    def update(self, price, timestamp):
        self.prices.append(price)
        self.timestamps.append(timestamp)

        if len(self.prices) < self.sma_window:
            return None

        signal = self.detect_signal()
        if signal:
            entry = price
            tp = entry * (1 + self.tp_pct) if signal == 'buy' else entry * (1 - self.tp_pct)
            sl = entry * (1 - self.sl_pct) if signal == 'buy' else entry * (1 + self.sl_pct)
            return {
                'signal': signal,
                'entry': round(entry, 4),
                'tp': round(tp, 4),
                'sl': round(sl, 4),
                'timestamp': timestamp
            }
        return None

    def simple_moving_average(self):
        return np.mean(list(self.prices)[-self.sma_window:])

    def detect_signal(self):
        prices = list(self.prices)
        sma = self.simple_moving_average()
        current_price = prices[-1]
        prev_price = prices[-2]

        if prev_price < sma and current_price > sma and self.last_signal != 'buy':
            self.last_signal = 'buy'
            return 'buy'
        elif prev_price > sma and current_price < sma and self.last_signal != 'sell':
            self.last_signal = 'sell'
            return 'sell'
        return None
