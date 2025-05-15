# analyzer/__init__.py
from .hs import HeadAndShoulders
from .trendline import TrendlineAnalyzer
from .dtb import DoubleTopBottom

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
