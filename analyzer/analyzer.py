from .head_shoulders import HeadShouldersAnalyzer
from .trendline import TrendlineAnalyzer
from .double_top_bottom import DoubleTopBottomAnalyzer
from .channel import ChannelAnalyzer  # Only if you're using channel detection

class Analyzer:
    def __init__(self):
        self.hs_analyzer = HeadShouldersAnalyzer()
        self.trendline_analyzer = TrendlineAnalyzer()
        self.dtb_analyzer = DoubleTopBottomAnalyzer()
        self.channel_analyzer = ChannelAnalyzer()  # Comment this line out if you haven't created it yet

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
