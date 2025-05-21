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
        for analyzer in [
            self.hs_analyzer,
            self.trendline_analyzer,
            self.dtb_analyzer,
            self.channel_analyzer

    def analyze(self, candles):
        signals = []

        hs_signal = self.hs_analyzer.detect(candles)
        if hs_signal:
            signals.append(hs_signal)

        trendline_signal = self.trendline_analyzer.detect(candles)
        if trendline_signal:
            signals.append(trendline_signal)

        dtb_signal = self.dtb_analyzer.detect(candles)
        if dtb_signal:
            signals.append(dtb_signal)

        channel_signal = self.channel_analyzer.detect(candles)
        if channel_signal:
            signals.append(channel_signal)

        return signals
