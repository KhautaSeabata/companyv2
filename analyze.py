# analyze.py

class Analyzer:
    def __init__(self):
        self.prices = []
        self.timestamps = []

    def analyze(self, price, timestamp):
        self.prices.append(price)
        self.timestamps.append(timestamp)

        # Example: return a signal every 20 ticks
        if len(self.prices) >= 20:
            entry = self.prices[-1]
            tp = entry + 20
            sl = entry - 20
            signal = {
                "signal": "buy" if entry % 2 == 0 else "sell",
                "entry": round(entry, 2),
                "tp": round(tp, 2),
                "sl": round(sl, 2),
                "timestamp": timestamp
            }
            self.prices = []
            self.timestamps = []
            return signal

        return None
