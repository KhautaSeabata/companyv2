import asyncio
from datetime import datetime, timezone, timedelta
import firebase_admin
from firebase_admin import credentials, db
from analyzer import Analyzer  # Your unified analyzer class

# Firebase initialization (adjust path to your service account JSON)
cred = credentials.Certificate("path/to/firebase-adminsdk.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://data-364f1-default-rtdb.firebaseio.com/'
})

analyzer = Analyzer()

ticks_ref = db.reference('/ticks/R_25')       # Your live ticks node
signals_ref = db.reference('/signals')         # Where signals are stored

# Convert UTC epoch to Johannesburg time string
def utc_to_johannesburg(utc_ts):
    dt_utc = datetime.fromtimestamp(utc_ts, timezone.utc)
    dt_jhb = dt_utc + timedelta(hours=2)  # UTC+2 for Johannesburg
    return dt_jhb.strftime('%Y-%m-%d %H:%M:%S')

async def process_tick(price, timestamp):
    signal = analyzer.update(price, timestamp)
    if signal:
        # Prepare signal data
        signal_data = {
            "type": signal.get("type", ""),
            "pattern": signal.get("pattern", ""),
            "entry": signal.get("entry"),
            "tp": signal.get("tp"),
            "sl": signal.get("sl"),
            "timestamp": utc_to_johannesburg(timestamp),
            "status": "open"
        }
        # Push signal to Firebase and get its unique key
        signal_key = signals_ref.push(signal_data).key
        print(f"New signal stored: {signal_data}")

async def monitor_signals_live():
    """
    Monitor live ticks and update signal status if TP or SL hit
    """
    last_processed = 0
    active_signals = {}  # key -> signal_data

    while True:
        ticks_snapshot = ticks_ref.order_by_child('epoch').start_at(last_processed + 1).get()
        if ticks_snapshot:
            for key, val in ticks_snapshot.items():
                price = val['quote']
                timestamp = val['epoch']
                last_processed = max(last_processed, timestamp)

                # Process analyzer to detect new signals
                await process_tick(price, timestamp)

                # Check active signals for TP or SL hits
                signals_snapshot = signals_ref.get()
                if signals_snapshot:
                    for s_key, s_val in signals_snapshot.items():
                        # Only check signals that are still open
                        if s_val.get("status") == "open":
                            entry = s_val.get("entry")
                            tp = s_val.get("tp")
                            sl = s_val.get("sl")

                            # Check if TP hit
                            if tp is not None and price >= tp:
                                signals_ref.child(s_key).update({"status": "tp_hit"})
                                print(f"Signal {s_key} TP hit at price {price}")

                            # Check if SL hit
                            elif sl is not None and price <= sl:
                                signals_ref.child(s_key).update({"status": "sl_hit"})
                                print(f"Signal {s_key} SL hit at price {price}")

        await asyncio.sleep(1)  # poll every second

if __name__ == "__main__":
    print("Starting live analyzer...")
    asyncio.run(monitor_signals_live())
