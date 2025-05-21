import numpy as np
import pandas as pd
from scipy.signal import argrelextrema
import asyncio
import aiohttp
from datetime import datetime
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Firebase URLs
FIREBASE_TICKS_URL = "https://data-364f1-default-rtdb.firebaseio.com/ticks/R_25.json"
FIREBASE_1MIN_URL = "https://data-364f1-default-rtdb.firebaseio.com/1minVix25.json"
FIREBASE_SIGNALS_URL = "https://data-364f1-default-rtdb.firebaseio.com/signals.json"  # URL for storing signals

class PatternDetector:
    def __init__(self):
        self.data = pd.DataFrame()
        self.last_detected_pattern = None
        self.last_signal_time = None
        self.min_pattern_points = 5  # Minimum number of points to detect a pattern
        self.signal_cooldown = 300  # 5 minutes cooldown between signals

    async def fetch_data(self):
        """Fetch the latest tick data from Firebase."""
        async with aiohttp.ClientSession() as session:
            async with session.get(FIREBASE_TICKS_URL) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._process_ticks_data(data)
                else:
                    logger.error(f"Failed to fetch data: {response.status}")
                    return None

    async def fetch_1min_data(self):
        """Fetch the 1-minute candle data from Firebase."""
        async with aiohttp.ClientSession() as session:
            async with session.get(FIREBASE_1MIN_URL) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._process_1min_data(data)
                else:
                    logger.error(f"Failed to fetch 1-minute data: {response.status}")
                    return None

    def detect_patterns(tick_data):
    """
    Analyze tick data to detect patterns.
    Returns a list of dictionaries with keys: entry_price, stop_loss, take_profit, pattern
    """
    patterns = []
    # Your pattern detection logic here
    # For example:
    if len(tick_data) >= 3:
        last_tick = tick_data[-1]
        prev_tick = tick_data[-2]
        if last_tick["quote"] > prev_tick["quote"]:
            pattern = {
                "entry_price": last_tick["quote"],
                "stop_loss": last_tick["quote"] - 0.1,
                "take_profit": last_tick["quote"] + 0.2,
                "pattern": "Uptrend"
            }
            patterns.append(pattern)
    return patterns


    def _process_ticks_data(self, data):
        """Process raw tick data into usable DataFrame."""
        if not data:
            return None
            
        # Convert to DataFrame (adjust according to your actual data structure)
        df = pd.DataFrame(list(data.values()))
        
        # Assuming your data has 'timestamp' and 'price' columns
        # Adjust column names according to your actual data structure
        if 'time' in df.columns and 'quote' in df.columns:
            df = df[['time', 'quote']].rename(columns={'time': 'timestamp', 'quote': 'price'})
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df.sort_values('timestamp')
            return df
        else:
            logger.error("Expected columns not found in tick data")
            return None

    def _process_1min_data(self, data):
        """Process 1-minute candle data into usable DataFrame."""
        if not data:
            return None
            
        # Convert to DataFrame (adjust according to your actual data structure)
        df = pd.DataFrame(list(data.values()))
        
        # Adjust column names according to your actual data structure
        required_columns = ['time', 'open', 'high', 'low', 'close']
        if all(col in df.columns for col in required_columns):
            df['timestamp'] = pd.to_datetime(df['time'], unit='ms')
            df = df.sort_values('timestamp')
            return df
        else:
            logger.error("Expected columns not found in 1-minute data")
            return None

    def identify_peaks_and_troughs(self, df, window=5):
        """Identify peaks and troughs in the price data."""
        if df is None or df.empty:
            return None, None
            
        # Create a copy to avoid modifying the original
        data = df.copy()
        
        # Get indices of local maxima and minima
        max_idx = argrelextrema(data['price'].values, np.greater_equal, order=window)[0]
        min_idx = argrelextrema(data['price'].values, np.less_equal, order=window)[0]
        
        # Create Series for peaks and troughs
        peaks = pd.Series(data['price'].iloc[max_idx].values, index=data.iloc[max_idx].index)
        troughs = pd.Series(data['price'].iloc[min_idx].values, index=data.iloc[min_idx].index)
        
        return peaks, troughs

    def detect_head_and_shoulders(self, peaks, troughs):
        """Detect Head and Shoulders pattern."""
        if len(peaks) < 3 or len(troughs) < 2:
            return False, None
            
        # Get the last 3 peaks and 2 troughs
        last_peaks = peaks.iloc[-3:].values
        last_troughs = troughs.iloc[-2:].values
        
        # Head and Shoulders: middle peak higher than other two, troughs roughly equal
        if (last_peaks[1] > last_peaks[0] and 
            last_peaks[1] > last_peaks[2] and
            abs(last_troughs[0] - last_troughs[1]) / last_troughs[0] < 0.05):
            
            # Calculate entry, stop loss and take profit
            entry_price = last_troughs[1]
            stop_loss = last_peaks[2]
            take_profit = entry_price - (stop_loss - entry_price)
            
            return True, {
                "pattern": "Head and Shoulders",
                "entry_price": float(entry_price),
                "stop_loss": float(stop_loss),
                "take_profit": float(take_profit),
                "direction": "Bearish"
            }
        
        return False, None

    def detect_inverse_head_and_shoulders(self, peaks, troughs):
        """Detect Inverse Head and Shoulders pattern."""
        if len(troughs) < 3 or len(peaks) < 2:
            return False, None
            
        # Get the last 3 troughs and 2 peaks
        last_troughs = troughs.iloc[-3:].values
        last_peaks = peaks.iloc[-2:].values
        
        # Inverse Head and Shoulders: middle trough lower than other two, peaks roughly equal
        if (last_troughs[1] < last_troughs[0] and 
            last_troughs[1] < last_troughs[2] and
            abs(last_peaks[0] - last_peaks[1]) / last_peaks[0] < 0.05):
            
            # Calculate entry, stop loss and take profit
            entry_price = last_peaks[1]
            stop_loss = last_troughs[2]
            take_profit = entry_price + (entry_price - stop_loss)
            
            return True, {
                "pattern": "Inverse Head and Shoulders",
                "entry_price": float(entry_price),
                "stop_loss": float(stop_loss),
                "take_profit": float(take_profit),
                "direction": "Bullish"
            }
        
        return False, None

    def detect_double_top(self, peaks, troughs):
        """Detect Double Top pattern."""
        if len(peaks) < 2 or len(troughs) < 1:
            return False, None
            
        # Get the last 2 peaks and 1 trough
        last_peaks = peaks.iloc[-2:].values
        last_trough = troughs.iloc[-1]
        
        # Double Top: two peaks at similar levels with a trough in between
        if abs(last_peaks[0] - last_peaks[1]) / last_peaks[0] < 0.03:
            
            # Calculate entry, stop loss and take profit
            entry_price = last_trough
            stop_loss = max(last_peaks)
            take_profit = entry_price - (stop_loss - entry_price)
            
            return True, {
                "pattern": "Double Top",
                "entry_price": float(entry_price),
                "stop_loss": float(stop_loss),
                "take_profit": float(take_profit),
                "direction": "Bearish"
            }
        
        return False, None

    def detect_double_bottom(self, peaks, troughs):
        """Detect Double Bottom pattern."""
        if len(troughs) < 2 or len(peaks) < 1:
            return False, None
            
        # Get the last 2 troughs and 1 peak
        last_troughs = troughs.iloc[-2:].values
        last_peak = peaks.iloc[-1]
        
        # Double Bottom: two troughs at similar levels with a peak in between
        if abs(last_troughs[0] - last_troughs[1]) / last_troughs[0] < 0.03:
            
            # Calculate entry, stop loss and take profit
            entry_price = last_peak
            stop_loss = min(last_troughs)
            take_profit = entry_price + (entry_price - stop_loss)
            
            return True, {
                "pattern": "Double Bottom",
                "entry_price": float(entry_price),
                "stop_loss": float(stop_loss),
                "take_profit": float(take_profit),
                "direction": "Bullish"
            }
        
        return False, None

    def detect_triple_top(self, peaks, troughs):
        """Detect Triple Top pattern."""
        if len(peaks) < 3 or len(troughs) < 2:
            return False, None
            
        # Get the last 3 peaks and 2 troughs
        last_peaks = peaks.iloc[-3:].values
        last_troughs = troughs.iloc[-2:].values
        
        # Triple Top: three peaks at similar levels with troughs in between
        if (abs(last_peaks[0] - last_peaks[1]) / last_peaks[0] < 0.03 and
            abs(last_peaks[1] - last_peaks[2]) / last_peaks[1] < 0.03):
            
            # Calculate entry, stop loss and take profit
            entry_price = last_troughs[-1]
            stop_loss = max(last_peaks)
            take_profit = entry_price - (stop_loss - entry_price)
            
            return True, {
                "pattern": "Triple Top",
                "entry_price": float(entry_price),
                "stop_loss": float(stop_loss),
                "take_profit": float(take_profit),
                "direction": "Bearish"
            }
        
        return False, None

    def detect_triple_bottom(self, peaks, troughs):
        """Detect Triple Bottom pattern."""
        if len(troughs) < 3 or len(peaks) < 2:
            return False, None
            
        # Get the last 3 troughs and 2 peaks
        last_troughs = troughs.iloc[-3:].values
        last_peaks = peaks.iloc[-2:].values
        
        # Triple Bottom: three troughs at similar levels with peaks in between
        if (abs(last_troughs[0] - last_troughs[1]) / last_troughs[0] < 0.03 and
            abs(last_troughs[1] - last_troughs[2]) / last_troughs[1] < 0.03):
            
            # Calculate entry, stop loss and take profit
            entry_price = last_peaks[-1]
            stop_loss = min(last_troughs)
            take_profit = entry_price + (entry_price - stop_loss)
            
            return True, {
                "pattern": "Triple Bottom",
                "entry_price": float(entry_price),
                "stop_loss": float(stop_loss),
                "take_profit": float(take_profit),
                "direction": "Bullish"
            }
        
        return False, None

    def detect_falling_wedge(self, peaks, troughs, df):
        """Detect Falling Wedge pattern."""
        if len(peaks) < 3 or len(troughs) < 3:
            return False, None
            
        # Get the last 3 peaks and 3 troughs
        peak_indices = peaks.index[-3:]
        trough_indices = troughs.index[-3:]
        
        peak_values = peaks.iloc[-3:].values
        trough_values = troughs.iloc[-3:].values
        
        # Check if both support and resistance lines are downward sloping
        peak_slope = (peak_values[2] - peak_values[0]) / (peak_indices[2] - peak_indices[0])
        trough_slope = (trough_values[2] - trough_values[0]) / (trough_indices[2] - trough_indices[0])
        
        # Falling Wedge: both support and resistance trending down, but support has a gentler slope
        if peak_slope < 0 and trough_slope < 0 and peak_slope < trough_slope:
            
            # Calculate entry, stop loss and take profit
            entry_price = df['price'].iloc[-1]
            stop_loss = min(trough_values)
            take_profit = entry_price + 2 * (entry_price - stop_loss)
            
            return True, {
                "pattern": "Falling Wedge",
                "entry_price": float(entry_price),
                "stop_loss": float(stop_loss),
                "take_profit": float(take_profit),
                "direction": "Bullish"
            }
        
        return False, None

    def detect_rising_wedge(self, peaks, troughs, df):
        """Detect Rising Wedge pattern."""
        if len(peaks) < 3 or len(troughs) < 3:
            return False, None
            
        # Get the last 3 peaks and 3 troughs
        peak_indices = peaks.index[-3:]
        trough_indices = troughs.index[-3:]
        
        peak_values = peaks.iloc[-3:].values
        trough_values = troughs.iloc[-3:].values
        
        # Check if both support and resistance lines are upward sloping
        peak_slope = (peak_values[2] - peak_values[0]) / (peak_indices[2] - peak_indices[0])
        trough_slope = (trough_values[2] - trough_values[0]) / (trough_indices[2] - trough_indices[0])
        
        # Rising Wedge: both support and resistance trending up, but resistance has a gentler slope
        if peak_slope > 0 and trough_slope > 0 and peak_slope < trough_slope:
            
            # Calculate entry, stop loss and take profit
            entry_price = df['price'].iloc[-1]
            stop_loss = max(peak_values)
            take_profit = entry_price - 2 * (stop_loss - entry_price)
            
            return True, {
                "pattern": "Rising Wedge",
                "entry_price": float(entry_price),
                "stop_loss": float(stop_loss),
                "take_profit": float(take_profit),
                "direction": "Bearish"
            }
        
        return False, None

    def detect_flag(self, peaks, troughs, df):
        """Detect Flag pattern (bullish or bearish)."""
        if len(df) < 20:  # Need enough data to detect the flag pole
            return False, None
            
        # Calculate recent trend (last 20 candles)
        recent_trend = df['price'].iloc[-20:].values
        
        # Check if there was a strong move before consolidation
        price_change = recent_trend[-1] - recent_trend[0]
        price_range = np.max(recent_trend) - np.min(recent_trend)
        
        if len(peaks) < 2 or len(troughs) < 2:
            return False, None
            
        # Get the last 2 peaks and troughs
        peak_values = peaks.iloc[-2:].values
        trough_values = troughs.iloc[-2:].values
        
        # Flag characteristics: parallel consolidation after a strong move
        peak_slope = (peak_values[1] - peak_values[0])
        trough_slope = (trough_values[1] - trough_values[0])
        
        # Check if slopes are roughly parallel
        if abs(peak_slope - trough_slope) / abs(peak_slope) < 0.2:
            # Determine if bullish or bearish flag
            if price_change > 0:  # Bullish flag
                entry_price = df['price'].iloc[-1]
                stop_loss = min(trough_values)
                take_profit = entry_price + abs(price_change)
                
                return True, {
                    "pattern": "Bullish Flag",
                    "entry_price": float(entry_price),
                    "stop_loss": float(stop_loss),
                    "take_profit": float(take_profit),
                    "direction": "Bullish"
                }
            else:  # Bearish flag
                entry_price = df['price'].iloc[-1]
                stop_loss = max(peak_values)
                take_profit = entry_price - abs(price_change)
                
                return True, {
                    "pattern": "Bearish Flag",
                    "entry_price": float(entry_price),
                    "stop_loss": float(stop_loss),
                    "take_profit": float(take_profit),
                    "direction": "Bearish"
                }
        
        return False, None

    def detect_pennant(self, peaks, troughs, df):
        """Detect Pennant pattern (bullish or bearish)."""
        if len(df) < 20:  # Need enough data to detect the pennant pole
            return False, None
            
        # Calculate recent trend (last 20 candles)
        recent_trend = df['price'].iloc[-20:].values
        
        # Check if there was a strong move before consolidation
        price_change = recent_trend[-1] - recent_trend[0]
        
        if len(peaks) < 3 or len(troughs) < 3:
            return False, None
            
        # Get the last 3 peaks and troughs
        peak_indices = peaks.index[-3:]
        trough_indices = troughs.index[-3:]
        
        peak_values = peaks.iloc[-3:].values
        trough_values = troughs.iloc[-3:].values
        
        # Calculate slopes
        peak_slope = (peak_values[2] - peak_values[0]) / (peak_indices[2] - peak_indices[0])
        trough_slope = (trough_values[2] - trough_values[0]) / (trough_indices[2] - trough_indices[0])
        
        # Pennant characteristics: converging trendlines (peaks sloping down, troughs sloping up)
        if peak_slope < 0 and trough_slope > 0:
            # Determine if bullish or bearish pennant
            if price_change > 0:  # Bullish pennant
                entry_price = df['price'].iloc[-1]
                stop_loss = min(trough_values)
                take_profit = entry_price + abs(price_change)
                
                return True, {
                    "pattern": "Bullish Pennant",
                    "entry_price": float(entry_price),
                    "stop_loss": float(stop_loss),
                    "take_profit": float(take_profit),
                    "direction": "Bullish"
                }
            else:  # Bearish pennant
                entry_price = df['price'].iloc[-1]
                stop_loss = max(peak_values)
                take_profit = entry_price - abs(price_change)
                
                return True, {
                    "pattern": "Bearish Pennant",
                    "entry_price": float(entry_price),
                    "stop_loss": float(stop_loss),
                    "take_profit": float(take_profit),
                    "direction": "Bearish"
                }
        
        return False, None

    def detect_ascending_triangle(self, peaks, troughs, df):
        """Detect Ascending Triangle pattern."""
        if len(peaks) < 2 or len(troughs) < 3:
            return False, None
            
        # Get the last 2 peaks and 3 troughs
        peak_values = peaks.iloc[-2:].values
        trough_values = troughs.iloc[-3:].values
        
        # Ascending Triangle: flat resistance (peaks) and rising support (troughs)
        if (abs(peak_values[0] - peak_values[1]) / peak_values[0] < 0.03 and
            trough_values[0] < trough_values[1] < trough_values[2]):
            
            # Calculate entry, stop loss and take profit
            entry_price = peak_values[1]
            stop_loss = trough_values[2]
            take_profit = entry_price + (entry_price - stop_loss)
            
            return True, {
                "pattern": "Ascending Triangle",
                "entry_price": float(entry_price),
                "stop_loss": float(stop_loss),
                "take_profit": float(take_profit),
                "direction": "Bullish"
            }
        
        return False, None

    def detect_descending_triangle(self, peaks, troughs, df):
        """Detect Descending Triangle pattern."""
        if len(peaks) < 3 or len(troughs) < 2:
            return False, None
            
        # Get the last 3 peaks and 2 troughs
        peak_values = peaks.iloc[-3:].values
        trough_values = troughs.iloc[-2:].values
        
        # Descending Triangle: flat support (troughs) and declining resistance (peaks)
        if (abs(trough_values[0] - trough_values[1]) / trough_values[0] < 0.03 and
            peak_values[0] > peak_values[1] > peak_values[2]):
            
            # Calculate entry, stop loss and take profit
            entry_price = trough_values[1]
            stop_loss = peak_values[2]
            take_profit = entry_price - (stop_loss - entry_price)
            
            return True, {
                "pattern": "Descending Triangle",
                "entry_price": float(entry_price),
                "stop_loss": float(stop_loss),
                "take_profit": float(take_profit),
                "direction": "Bearish"
            }
        
        return False, None

    def detect_diamond(self, peaks, troughs, df):
        """Detect Diamond pattern."""
        if len(peaks) < 4 or len(troughs) < 4:
            return False, None
            
        # This is a complex pattern that's hard to detect algorithmically
        # A simplified approach: look for broadening followed by narrowing
        peak_values = peaks.iloc[-4:].values
        trough_values = troughs.iloc[-4:].values
        
        # Check for broadening followed by narrowing
        first_width = peak_values[1] - trough_values[1]
        middle_width = peak_values[2] - trough_values[2]
        last_width = peak_values[3] - trough_values[3]
        
        if first_width < middle_width and middle_width > last_width:
            # Determine direction based on breakout
            current_price = df['price'].iloc[-1]
            if current_price < trough_values[3]:  # Bearish breakout
                entry_price = current_price
                stop_loss = peak_values[3]
                take_profit = entry_price - (middle_width)
                
                return True, {
                    "pattern": "Diamond (Bearish)",
                    "entry_price": float(entry_price),
                    "stop_loss": float(stop_loss),
                    "take_profit": float(take_profit),
                    "direction": "Bearish"
                }
            elif current_price > peak_values[3]:  # Bullish breakout
                entry_price = current_price
                stop_loss = trough_values[3]
                take_profit = entry_price + (middle_width)
                
                return True, {
                    "pattern": "Diamond (Bullish)",
                    "entry_price": float(entry_price),
                    "stop_loss": float(stop_loss),
                    "take_profit": float(take_profit),
                    "direction": "Bullish"
                }
        
        return False, None

    def detect_cup_and_handle(self, peaks, troughs, df):
        """Detect Cup and Handle pattern."""
        if len(df) < 30 or len(peaks) < 3:
            return False, None
            
        # This pattern requires more data points and a specific shape
        # Using a simplified approach
        
        # Last 30 prices to detect the cup
        prices = df['price'].iloc[-30:].values
        
        # Cup characteristics (U-shaped curve)
        # Simplified detection - check if middle prices are lower than both ends
        mid_point = len(prices) // 2
        left_section = prices[:mid_point]
        right_section = prices[mid_point:]
        
        if (np.mean(left_section) > np.mean(prices[mid_point-3:mid_point+3]) and
            np.mean(right_section) > np.mean(prices[mid_point-3:mid_point+3])):
            
            # Handle: small pullback after the cup
            if len(peaks) >= 3 and peaks.iloc[-1] < peaks.iloc[-2]:
                entry_price = df['price'].iloc[-1]
                stop_loss = min(prices[-10:])
                take_profit = entry_price + (entry_price - stop_loss) * 2
                
                return True, {
                    "pattern": "Cup and Handle",
                    "entry_price": float(entry_price),
                    "stop_loss": float(stop_loss),
                    "take_profit": float(take_profit),
                    "direction": "Bullish"
                }
        
        return False, None

    def detect_rectangle(self, peaks, troughs, df, window=10):
        """Detect Rectangle pattern (consolidation)."""
        if len(peaks) < 2 or len(troughs) < 2:
            return False, None
            
        # Get recent peaks and troughs
        recent_peaks = peaks.iloc[-window:]
        recent_troughs = troughs.iloc[-window:]
        
        if len(recent_peaks) < 2 or len(recent_troughs) < 2:
            return False, None
            
        # Calculate standard deviation of peaks and troughs
        peak_std = np.std(recent_peaks.values)
        trough_std = np.std(recent_troughs.values)
        
        # Rectangle characteristics: consistent highs and lows
        peak_mean = np.mean(recent_peaks.values)
        trough_mean = np.mean(recent_troughs.values)
        
        # Check if peaks and troughs are relatively consistent
        if (peak_std / peak_mean < 0.03 and trough_std / trough_mean < 0.03):
            # Current price to determine breakout direction
            current_price = df['price'].iloc[-1]
            
            if current_price > peak_mean * 1.01:  # Bullish breakout
                entry_price = current_price
                stop_loss = trough_mean
                take_profit = entry_price + (peak_mean - trough_mean)
                
                return True, {
                    "pattern": "Rectangle (Bullish Breakout)",
                    "entry_price": float(entry_price),
                    "stop_loss": float(stop_loss),
                    "take_profit": float(take_profit),
                    "direction": "Bullish"
                }
            elif current_price < trough_mean * 0.99:  # Bearish breakout
                entry_price = current_price
                stop_loss = peak_mean
                take_profit = entry_price - (peak_mean - trough_mean)
                
                return True, {
                    "pattern": "Rectangle (Bearish Breakout)",
                    "entry_price": float(entry_price),
                    "stop_loss": float(stop_loss),
                    "take_profit": float(take_profit),
                    "direction": "Bearish"
                }
        
        return False, None

    def detect_broadening_triangle(self, peaks, troughs, df):
        """Detect Broadening Triangle pattern."""
        if len(peaks) < 3 or len(troughs) < 3:
            return False, None
            
        # Get the last 3 peaks and troughs
        peak_values = peaks.iloc[-3:].values
        trough_values = troughs.iloc[-3:].values
        
        # Broadening Triangle: expanding highs and lows
        if (peak_values[0] < peak_values[1] < peak_values[2] and
            trough_values[0] > trough_values[1] > trough_values[2]):
            
            # Calculate entry, stop loss and take profit based on current price and direction
            current_price = df['price'].iloc[-1]
            
            if current_price > peak_values[2]:  # Bullish breakout
                entry_price = current_price
                stop_loss = trough_values[2]
                take_profit = entry_price + (entry_price - stop_loss)
                
                return True, {
                    "pattern": "Broadening Triangle (Bullish)",
                    "entry_price": float(entry_price),
                    "stop_loss": float(stop_loss),
                    "take_profit": float(take_profit),
                    "direction": "Bullish"
                }
            elif current_price < trough_values[2]:  # Bearish breakout
                entry_price = current_price
                stop_loss = peak_values[2]
                take_profit = entry_price - (stop_loss - entry_price)
                
                return True, {
                    "pattern": "Broadening Triangle (Bearish)",
                    "entry_price": float(entry_price),
                    "stop_loss": float(stop_loss),
                    "take_profit": float(take_profit),
                    "direction": "Bearish"
                }
        
        return False, None

    def detect_symmetrical_triangle(self, peaks, troughs, df):
        """Detect Symmetrical Triangle pattern."""
        if len(peaks) < 3 or len(troughs) < 3:
            return False, None
            
        # Get the last 3 peaks and troughs
        peak_indices = peaks.index[-3:]
        trough_indices = troughs.index[-3:]
        
        peak_values = peaks.iloc[-3:].values
        trough_values = troughs.iloc[-3:].values
        
        # Calculate slopes
        peak_slope = (peak_values[2] - peak_values[0]) / (peak_indices[2] - peak_indices[0])
        trough_slope = (trough_values[2] - trough_values[0]) / (trough_indices[2] - trough_indices[0])
        
        # Symmetrical Triangle: higher lows and lower highs (converging)
        if peak_slope < 0 and trough_slope > 0:
            # Current price to determine breakout direction
            current_price = df['price'].iloc[-1]
            triangle_midpoint = (peak_values[2] + trough_values[2]) / 2
            
            if current_price > peak_values[2]:  # Bullish breakout
                entry_price = current_price
                stop_loss = triangle_midpoint
                take_profit = entry_price + (entry_price - stop_loss)
                
                return True, {
                    "pattern": "Symmetrical Triangle (Bullish)",
                    "entry_price": float(entry_price),
                    "stop_loss": float(stop_loss),
                    "take_profit": float(take_profit),
                    "direction": "Bullish"
                }
            elif current_price < trough_values[2]:  # Bearish breakout
                entry_price = current_price
                stop_loss = triangle_midpoint
                take_profit = entry_price - (stop_loss - entry_price)
                
                return True, {
                    "pattern": "Symmetrical Triangle (Bearish)",
                    "entry_price": float(entry_price),
                    "stop_loss": float(stop_loss),
                    "take_profit": float(take_profit),
                    "direction": "Bearish"
                }
        
        return False, None
        
    async def send_signal(self, signal_data):
        """Send detected pattern signal to Firebase."""
        # Add timestamp to signal data
        signal_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(FIREBASE_SIGNALS_URL, json=signal_data) as response:
                    if response.status == 200:
                        logger.info(f"Signal sent successfully: {signal_data['pattern']}")
                        return True
                    else:
                        logger.error(f"Failed to send signal: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Error sending signal: {str(e)}")
            return False
    
    def can_send_signal(self):
        """Check if we can send a signal (cooldown period)."""
        if self.last_signal_time is None:
            return True
            
        now = datetime.now()
        seconds_since_last_signal = (now - self.last_signal_time).total_seconds()
        
        return seconds_since_last_signal > self.signal_cooldown
    
    async def run_detection(self):
        """Main method to run pattern detection."""
        # Fetch latest data
        df = await self.fetch_data()
        if df is None or len(df) < self.min_pattern_points:
            logger.warning("Not enough data for pattern detection")
            return None
            
        # Identify peaks and troughs
        peaks, troughs = self.identify_peaks_and_troughs(df)
        if peaks is None or troughs is None:
            logger.warning("Could not identify peaks and troughs")
            return None
            
        # Dictionary to store detection methods and their results
        detection_methods = [
            self.detect_head_and_shoulders,
            self.detect_inverse_head_and_shoulders,
            self.detect_double_top,
            self.detect_double_bottom,
            self.detect_triple_top,
            self.detect_triple_bottom,
            lambda p, t: self.detect_falling_wedge(p, t, df),
            lambda p, t: self.detect_rising_wedge(p, t, df),
            lambda p, t: self.detect_flag(p, t, df),
            lambda p, t: self.detect_pennant(p, t, df),
            lambda p, t: self.detect_ascending_triangle(p, t, df),
            lambda p, t: self.detect_descending_triangle(p, t, df),
            lambda p, t: self.detect_diamond(p, t, df),
            lambda p, t: self.detect_cup_and_handle(p, t, df),
            lambda p, t: self.detect_rectangle(p, t, df),
            lambda p, t: self.detect_broadening_triangle(p, t, df),
            lambda p, t: self.detect_symmetrical_triangle(p, t, df)
        ]
        
        # Check if we can send a signal
        if not self.can_send_signal():
            logger.info("Signal cooldown period still active")
            return None
            
        # Run all detection methods
        for detect_method in detection_methods:
            detected, signal_data = detect_method(peaks, troughs)
            
            if detected:
                logger.info(f"Pattern detected: {signal_data['pattern']}")
                
                # Send signal to Firebase
                if await self.send_signal(signal_data):
                    self.last_detected_pattern = signal_data["pattern"]
                    self.last_signal_time = datetime.now()
                    return signal_data
                    
        return None

async def main():
    """Main function to run the pattern detector."""
    detector = PatternDetector()
    
    logger.info("Starting pattern detection service")
    
    while True:
        try:
            signal = await detector.run_detection()
            if signal:
                logger.info(f"Signal sent: {signal['pattern']} at price {signal['entry_price']}")
            
            # Sleep for a bit before checking again
            await asyncio.sleep(5)  # Check every 5 seconds
            
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
            await asyncio.sleep(10)  # Sleep a bit longer on error

if __name__ == "__main__":
    asyncio.run(main())
