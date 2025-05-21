import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import aiohttp
import asyncio
import json
from datetime import datetime, timedelta
import logging
from pattern_detector import PatternDetector

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Firebase URLs
FIREBASE_TICKS_URL = "https://data-364f1-default-rtdb.firebaseio.com/ticks/R_25.json"
FIREBASE_1MIN_URL = "https://data-364f1-default-rtdb.firebaseio.com/1minVix25.json"
FIREBASE_SIGNALS_URL = "https://data-364f1-default-rtdb.firebaseio.com/signals.json"

class PatternVisualizer:
    def __init__(self):
        self.detector = PatternDetector()
        self.signals = []
        self.chart_data = None
        self.tick_data = None
        
    async def fetch_signals(self):
        """Fetch signals from Firebase."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(FIREBASE_SIGNALS_URL) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data:
                            signals = []
                            for key, signal in data.items():
                                signal['id'] = key
                                signals.append(signal)
                            self.signals = signals
                            return signals
                        return []
                    else:
                        logger.error(f"Failed to fetch signals: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error fetching signals: {str(e)}")
            return []
    
    async def fetch_chart_data(self, timeframe='1min', limit=100):
        """Fetch candle data from Firebase."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(FIREBASE_1MIN_URL) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data:
                            df = pd.DataFrame(list(data.values()))
                            
                            # Process data according to your actual data structure
                            if all(col in df.columns for col in ['time', 'open', 'high', 'low', 'close']):
                                df['timestamp'] = pd.to_datetime(df['time'], unit='ms')
                                df = df.sort_values('timestamp')
                                df = df.tail(limit)
                                self.chart_data = df
                                return df
                            else:
                                logger.error("Expected columns not found in candle data")
                                return None
                    else:
                        logger.error(f"Failed to fetch chart data: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching chart data: {str(e)}")
            return None
    
    async def fetch_tick_data(self, limit=500):
        """Fetch tick data from Firebase."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(FIREBASE_TICKS_URL) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data:
                            df = pd.DataFrame(list(data.values()))
                            
                            # Process data according to your actual data structure
                            if 'time' in df.columns and 'quote' in df.columns:
                                df['timestamp'] = pd.to_datetime(df['time'], unit='ms')
                                df = df.sort_values('timestamp')
                                df = df.tail(limit)
                                self.tick_data = df
                                return df
                            else:
                                logger.error("Expected columns not found in tick data")
                                return None
                    else:
                        logger.error(f"Failed to fetch tick data: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching tick data: {str(e)}")
            return None
    
    def create_candlestick_chart(self):
        """Create a candlestick chart with detected patterns."""
        if self.chart_data is None:
            logger.error("No chart data available")
            return None
            
        # Create figure with secondary y-axis
        fig = make_subplots(rows=2, cols=1, 
                           shared_xaxes=True, 
                           vertical_spacing=0.02, 
                           row_heights=[0.7, 0.3])
        
        # Add candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=self.chart_data['timestamp'],
                open=self.chart_data['open'],
                high=self.chart_data['high'],
                low=self.chart_data['low'],
                close=self.chart_data['close'],
                name="Price"
            ),
            row=1, col=1
        )
        
        # Add volume bars
        if 'volume' in self.chart_data.columns:
            fig.add_trace(
                go.Bar(
                    x=self.chart_data['timestamp'],
                    y=self.chart_data['volume'],
                    name="Volume"
                ),
                row=2, col=1
            )
        
        # Add signals to the chart
        for signal in self.signals:
            if 'timestamp' in signal and 'entry_price' in signal:
                try:
                    signal_time = datetime.strptime(signal['timestamp'], "%Y-%m-%d %H:%M:%S")
                    
                    # Add signal marker
                    fig.add_trace(
                        go.Scatter(
                            x=[signal_time],
                            y=[signal['entry_price']],
                            mode='markers',
                            marker=dict(
                                symbol='star',
                                size=15,
                                color='red' if signal.get('direction') == 'Bearish' else 'green'
                            ),
                            name=signal['pattern'],
                            text=[f"Pattern: {signal['pattern']}<br>Entry: {signal['entry_price']}<br>SL: {signal['stop_loss']}<br>TP: {signal['take_profit']}"],
                            hoverinfo='text'
                        ),
                        row=1, col=1
                    )
                    
                    # Add horizontal lines for entry, stop loss, and take profit
                    colors = {'entry': 'blue', 'stop_loss': 'red', 'take_profit': 'green'}
                    for level_type in ['entry_price', 'stop_loss', 'take_profit']:
                        if level_type in signal:
                            # Find nearest timestamps for this signal
                            nearest_idx = self.chart_data['timestamp'].searchsorted(signal_time)
                            start_idx = max(0, nearest_idx - 5)
                            end_idx = min(len(self.chart_data), nearest_idx + 15)
                            
                            if start_idx < end_idx:
                                start_time = self.chart_data['timestamp'].iloc[start_idx]
                                end_time = self.chart_data['timestamp'].iloc[end_idx-1]
                                
                                fig.add_trace(
                                    go.Scatter(
                                        x=[start_time, end_time],
                                        y=[signal[level_type], signal[level_type]],
                                        mode='lines',
                                        line=dict(
                                            color=colors.get(level_type, 'gray'),
                                            width=1,
                                            dash='dash'
                                        ),
                                        name=f"{signal['pattern']} {level_type}",
                                        showlegend=False
                                    ),
                                    row=1, col=1
                                )
                except Exception as e:
                    logger.error(f"Error adding signal to chart: {str(e)}")
        
        # Update layout
        fig.update_layout(
            title='Price Chart with Detected Patterns',
            xaxis_title='Time',
            yaxis_title='Price',
            xaxis_rangeslider_visible=False,
            legend_orientation="h",
            legend=dict(y=1.02, x=0.5, xanchor='center'),
            height=800,
            margin=dict(l=50, r=50, t=100, b=50)
        )
        
        # Update y-axes labels
        fig.update_yaxes(title_text="Price", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        
        return fig
    
    def create_tick_chart_with_patterns(self):
        """Create a tick chart with patterns highlighted."""
        if self.tick_data is None:
            logger.error("No tick data available")
            return None
            
        fig = go.Figure()
        
        # Add tick data
        fig.add_trace(
            go.Scatter(
                x=self.tick_data['timestamp'],
                y=self.tick_data['quote'],
                mode='lines',
                name='Price',
                line=dict(color='blue', width=1)
            )
        )
        
        # Add signals to the chart
        for signal in self.signals:
            if 'timestamp' in signal and 'entry_price' in signal:
                try:
                    signal_time = datetime.strptime(signal['timestamp'], "%Y-%m-%d %H:%M:%S")
                    
                    # Add signal marker
                    fig.add_trace(
                        go.Scatter(
                            x=[signal_time],
                            y=[signal['entry_price']],
                            mode='markers+text',
                            marker=dict(
                                symbol='star',
                                size=12,
                                color='red' if signal.get('direction') == 'Bearish' else 'green'
                            ),
                            text=[signal['pattern']],
                            textposition="top center",
                            name=signal['pattern'],
                            hoverinfo='text',
                            hovertext=f"Pattern: {signal['pattern']}<br>Entry: {signal['entry_price']}<br>SL: {signal['stop_loss']}<br>TP: {signal['take_profit']}"
                        )
                    )
                    
                    # Draw pattern visualization
                    pattern_type = signal['pattern']
                    self._draw_pattern_visualization(fig, pattern_type, signal_time, signal['entry_price'])
                    
                except Exception as e:
                    logger.error(f"Error adding signal to tick chart: {str(e)}")
        
        # Update layout
        fig.update_layout(
            title='Tick Chart with Detected Patterns',
            xaxis_title='Time',
            yaxis_title='Price',
            height=600,
            margin=dict(l=50, r=50, t=100, b=50)
        )
        
        return fig
    
    def _draw_pattern_visualization(self, fig, pattern_type, signal_time, entry_price):
        """Draw a pattern visualization based on the pattern type."""
        # This is a simplified version - in production you would want to draw the actual pattern
        # based on the detected highs and lows
        
        # Get reference points before and after signal time
        if self.tick_data is not None:
            time_window = timedelta(minutes=5)
            pattern_start = signal_time - time_window
            pattern_end = signal_time + time_window
            
            # Filter data for this time range
            mask = (self.tick_data['timestamp'] >= pattern_start) & (self.tick_data['timestamp'] <= pattern_end)
            pattern_data = self.tick_data[mask]
            
            if not pattern_data.empty:
                if "Head and Shoulders" in pattern_type:
                    # Simplified head and shoulders visualization
                    fig.add_shape(
                        type="rect",
                        x0=pattern_start,
                        x1=pattern_end,
                        y0=min(pattern_data['quote']),
                        y1=max(pattern_data['quote']),
                        line=dict(color="rgba(255, 0, 0, 0.3)", width=1),
                        fillcolor="rgba(255, 0, 0, 0.1)"
                    )
                elif "Double" in pattern_type:
                    # Simplified double top/bottom visualization
                    fig.add_shape(
                        type="rect",
                        x0=pattern_start,
                        x1=pattern_end,
                        y0=min(pattern_data['quote']),
                        y1=max(pattern_data['quote']),
                        line=dict(color="rgba(0, 0, 255, 0.3)", width=1),
                        fillcolor="rgba(0, 0, 255, 0.1)"
                    )
                elif "Triangle" in pattern_type:
                    # Simplified triangle visualization
                    fig.add_shape(
                        type="rect",
                        x0=pattern_start,
                        x1=pattern_end,
                        y0=min(pattern_data['quote']),
                        y1=max(pattern_data['quote']),
                        line=dict(color="rgba(0, 255, 0, 0.3)", width=1),
                        fillcolor="rgba(0, 255, 0, 0.1)"
                    )
                else:
                    # Generic pattern highlight
                    fig.add_shape(
                        type="rect",
                        x0=pattern_start,
                        x1=pattern_end,
                        y0=min(pattern_data['quote']),
                        y1=max(pattern_data['quote']),
                        line=dict(color="rgba(128, 128, 128, 0.3)", width=1),
                        fillcolor="rgba(128, 128, 128, 0.1)"
                    )
    
    def create_signal_table(self):
        """Create a table of recent signals."""
        if not self.signals:
            return "No signals detected yet."
        
        # Sort signals by timestamp (newest first)
        sorted_signals = sorted(
            self.signals, 
            key=lambda x: datetime.strptime(x['timestamp'], "%Y-%m-%d %H:%M:%S") if 'timestamp' in x else datetime.min,
            reverse=True
        )
        
        # Create a DataFrame for display
        signal_df = pd.DataFrame(sorted_signals)
        
        # Select and rename columns for display
        display_columns = {
            'pattern': 'Pattern',
            'direction': 'Direction',
            'entry_price': 'Entry Price',
            'stop_loss': 'Stop Loss',
            'take_profit': 'Take Profit',
            'timestamp': 'Signal Time'
        }
        
        # Select only columns that exist in the DataFrame
        available_columns = [col for col in display_columns.keys() if col in signal_df.columns]
        
        if not available_columns:
            return "Signal data is missing expected columns."
        
        display_df = signal_df[available_columns].rename(columns=display_columns)
        
        # Format the table as HTML
        table_html = display_df.head(10).to_html(index=False, classes="table table-striped table-bordered")
        
        return table_html
    
    async def run_visualization(self):
        """Main method to run visualization."""
        # Fetch data
        await self.fetch_chart_data()
        await self.fetch_tick_data()
        await self.fetch_signals()
        
        # Create visualizations
        candlestick_chart = self.create_candlestick_chart()
        tick_chart = self.create_tick_chart_with_patterns()
        signal_table = self.create_signal_table()
        
        return {
            'candlestick_chart': candlestick_chart,
            'tick_chart': tick_chart,
            'signal_table': signal_table
        }

async def main():
    """Main function to run the visualizer."""
    visualizer = PatternVisualizer()
    
    logger.info("Starting pattern visualization service")
    
    while True:
        try:
            visualizations = await visualizer.run_visualization()
            
            # In a real application, you would save these visualizations or serve them
            # Here we just log that they were created
            if visualizations:
                logger.info("Visualizations updated")
                
                # Save the figures to HTML files
                if visualizations['candlestick_chart']:
                    visualizations['candlestick_chart'].write_html("static/candlestick_chart.html")
                    
                if visualizations['tick_chart']:
                    visualizations['tick_chart'].write_html("static/tick_chart.html")
                
                # Save the signal table
                with open("static/signal_table.html", "w") as f:
                    f.write(visualizations['signal_table'])
            
            # Sleep for a bit before updating again
            await asyncio.sleep(30)  # Update every 30 seconds
            
        except Exception as e:
            logger.error(f"Error in visualization loop: {str(e)}")
            await asyncio.sleep(60)  # Sleep longer on error

if __name__ == "__main__":
    asyncio.run(main())
