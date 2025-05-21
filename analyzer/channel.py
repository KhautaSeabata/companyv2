# analyzer/channel.py

from datetime import datetime
import pytz

class ChannelAnalyzer:
    def __init__(self):
        self.last_signal_time = None
        self.min_distance = 0.0005  # acceptable proximity to boundaries for signal

    def is_parallel(self, slope1, slope2, tolerance=0.2):
        return abs(slope1 - slope2) < tolerance

    def detect_channel(self, candles):
        if len(candles) < 10:
            return None

        highs = [c['high'] for c in candles]
        lows = [c['low'] for c in candles]
        times = [c['time'] for c in candles]

        # Use the last 20 bars to try and find a channel
        recent_highs = highs[-20:]
        recent_lows = lows[-20:]

        max_high = max(recent_highs)
        min_low = min(recent_lows)

        # Identify slopes (for up/down) or flatness (sideways)
        high_slope = (recent_highs[-1] - recent_highs[0]) / max(1, (times[-1] - times[-20]) / 60)
        low_slope = (recent_lows[-1] - recent_lows[0]) / max(1, (times[-1] - times[-20]) / 60)

        if self.is_parallel(high_slope, low_slope):
            if abs(high_slope) < 0.01:
                return {'type': 'sideways', 'high': max_high, 'low': min_low}
            elif high_slope > 0:
                return {'type': 'up', 'high': max_high, 'low': min_low}
            else:
                return {'type': 'down', 'high': max_high, 'low': min_low}
        return None

    def generate_signal(self, candles):
        if not candles:
            return None

        channel = self.detect_channel(candles)
        if not channel:
            return None

        last_candle = candles[-1]
        current_price = last_candle['close']
        timestamp = last_candle['time']

        if self.last_signal_time == timestamp:
            return None  # avoid duplicate signal

        if abs(current_price - channel['high']) <= self.min_distance:
            direction = 'sell'
            entry = current_price
            tp = channel['low']
            sl = channel['high'] + (channel['high'] - channel['low']) * 0.2
        elif abs(current_price - channel['low']) <= self.min_distance:
            direction = 'buy'
            entry = current_price
            tp = channel['high']
            sl = channel['low'] - (channel['high'] - channel['low']) * 0.2
        else:
            return None

        self.last_signal_time = timestamp

        # Convert to Johannesburg time
        jhb_time = datetime.fromtimestamp(timestamp, pytz.timezone('Africa/Johannesburg')).strftime('%Y-%m-%d %H:%M:%S')

        return {
            'type': channel['type'],
            'direction': direction,
            'entry': round(entry, 5),
            'tp': round(tp, 5),
            'sl': round(sl, 5),
            'time': jhb_time
        }

