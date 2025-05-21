class Analyzer:
    def __init__(self):
        self.hs_analyzer = HeadShouldersAnalyzer()
        self.trendline_analyzer = TrendlineAnalyzer()
        self.dtb_analyzer = DoubleTopBottomAnalyzer()
        self.channel_analyzer = ChannelAnalyzer()

    def analyze(self, candles):
        signals = []

        hs_signal = self.hs_analyzer.generate_signal(candles)
        if hs_signal:
            hs_signal['pattern'] = 'Head & Shoulders'
            signals.append(hs_signal)

        trendline_signal = self.trendline_analyzer.generate_signal(candles)
        if trendline_signal:
            trendline_signal['pattern'] = 'Trendline'
            signals.append(trendline_signal)

        dtb_signal = self.dtb_analyzer.generate_signal(candles)
        if dtb_signal:
            dtb_signal['pattern'] = 'Double Top/Bottom'
            signals.append(dtb_signal)

        channel_signal = self.channel_analyzer.generate_signal(candles)
        if channel_signal:
            channel_signal['pattern'] = f"{channel_signal['type'].capitalize()} Channel"
            signals.append(channel_signal)

        return signals
