from .hs import HeadShouldersAnalyzer
from .trendline import TrendlineAnalyzer
from .dtb import DoubleTopBottomAnalyzer
from .channel import ChannelAnalyzer

class Analyzer:
    def __init__(self):
        self.hs_analyzer = HeadShouldersAnalyzer()
        self.trendline_analyzer = TrendlineAnalyzer()
        self.dtb_analyzer = DoubleTopBottomAnalyzer()
        self.channel_analyzer = ChannelAnalyzer()

    def update(self, price, timestamp):
        signals = []
        for analyzer in [
            self.hs_analyzer,
            self.trendline_analyzer,
            self.dtb_analyzer,
            self.channel_analyzer,
        ]:
            signal = analyzer.update(price, timestamp)
            if signal:
                signals.append(signal)
        return signals
