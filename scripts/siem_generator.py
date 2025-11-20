# siem_generator.py
import random, os, pandas as pd
from tqdm import tqdm
import argparse

def generate_log_entry():
    """Create a synthetic SIEM event."""
    events = ["LOGIN_SUCCESS", "LOGIN_FAIL", "TXN_ATTEMPT", "TXN_SUCCESS", "SUSPICIOUS_ACTIVITY", "ACCOUNT_LOCKED"]
    severity = {"LOGIN_SUCCESS": "Low", "LOGIN_FAIL": "Medium", "TXN_ATTEMPT": "Low",
                "TXN_SUCCESS": "Low", "SUSPICIOUS_ACTIVITY": "High", "ACCOUNT_LOCKED": "Critical"}

    event = random.choice(events)
    return {
        "timestamp": pd.Timestamp.now() - pd.Timedelta(minutes=random.randint(0, 10000)),
        "user_id": f"user_{random.randint(1000,9999)}",
        "event_type": event,
        "ip_address": f"192.168.{random.randint(0,255)}.{random.randint(0,255)}",
        "device": random.choice(["Android", "iPhone", "Windows", "Mac"]),
        "severity": severity[event],
        "correlation_id": random.randint(100000,999999)
    }

def main(n_records, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    data = [generate_log_entry() for _ in tqdm(range(n_records), desc="Generating SIEM logs")]
    df = pd.DataFrame(data)
    path = os.path.join(output_dir, "siem_logs.csv")
    df.to_csv(path, index=False)
    print(f"✅ {n_records} SIEM logs saved to {path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=500)
    parser.add_argument("--output_dir", default="outputs/siem")
    args = parser.parse_args()
    main(args.n, args.output_dir)
