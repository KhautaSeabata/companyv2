from .head_shoulders import HeadShouldersAnalyzer
from .trendline import TrendlineAnalyzer
from .double_top_bottom import DoubleTopBottomAnalyzer
from .channel import ChannelAnalyzer  # If you've added this

class Analyzer:
    def __init__(self):
        self.hs_analyzer = HeadShouldersAnalyzer()
        self.trendline_analyzer = TrendlineAnalyzer()
        self.dtb_analyzer = DoubleTopBottomAnalyzer()
        self.channel_analyzer = ChannelAnalyzer()  # Optional, if used

    def analyze(self, candles):
        signals = []

        signal = self.hs_analyzer.detect(candles)
        if signal: signals.append(signal)

        signal = self.trendline_analyzer.detect(candles)
        if signal: signals.append(signal)

        signal = self.dtb_analyzer.detect(candles)
        if signal: signals.append(signal)

        signal = self.channel_analyzer.detect(candles)
        if signal: signals.append(signal)

        return signals
