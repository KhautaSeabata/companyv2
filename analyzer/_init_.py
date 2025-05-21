from .hs import HeadShouldersAnalyzer
from .trendline import TrendlineAnalyzer
from .dtb import DoubleTopBottomAnalyzer
from .channel import ChannelAnalyzer

class Analyzer:
    def __init__(self):
        self.hs = HeadAndShoulders()
        self.trendline = TrendlineAnalyzer()
        self.dtb = DoubleTopBottom()

    def update(self, price, timestamp):
        signal = self.hs.update(price, timestamp)
        if signal:
            return {"type": "H&S", **signal}

        signal = self.trendline.update(price, timestamp)
        if signal:
            return {"type": "Trendline", **signal}

        signal = self.dtb.update(price, timestamp)
        if signal:
            return {"type": "DT/B", **signal}

        return None
