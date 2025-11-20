# siem_log_generator.py

import os, json, random
from faker import Faker
from tqdm import tqdm
import pandas as pd
import argparse
from datetime import datetime, timedelta

fake = Faker()

EVENT_TYPES = [
    "login_success",
    "login_failure",
    "transaction_initiated",
    "transaction_blocked",
    "device_blacklisted",
    "anomaly_detected",
    "account_locked"
]

def load_devices(device_file):
    with open(device_file, "r") as f:
        return json.load(f)

def generate_log(device, user_id):
    event_type = random.choice(EVENT_TYPES)
    timestamp = datetime.utcnow() - timedelta(minutes=random.randint(0, 10000))
    details = {}

    if event_type == "login_failure":
        details = {"reason": random.choice(["wrong_password", "unknown_device", "geo_mismatch"])}
    elif event_type == "transaction_initiated":
        details = {"amount": round(random.uniform(10, 5000), 2), "currency": "KES"}
    elif event_type == "transaction_blocked":
        details = {"amount": round(random.uniform(10, 3000), 2), "reason": "high_risk_pattern"}
    elif event_type == "anomaly_detected":
        details = {"metric": random.choice(["device_reuse", "ip_velocity", "geo_mismatch"]), "confidence": random.randint(60, 99)}

    return {
        "event_id": f"evt_{random.randint(100000, 999999)}",
        "timestamp": timestamp.isoformat() + "Z",
        "device_id": device["device_id"],
        "user_id": user_id,
        "ip_address": device["ip_address"],
        "geo_country": device["geo_location"]["country"],
        "geo_city": device["geo_location"]["city"],
        "event_type": event_type,
        "details": details
    }

def main(device_file, output_dir, n_events, output_format):
    os.makedirs(output_dir, exist_ok=True)
    devices = load_devices(device_file)
    logs = []

    for _ in tqdm(range(n_events), desc="Generating SIEM events"):
        device = random.choice(devices)
        user_id = random.choice(device["linked_users"])
        logs.append(generate_log(device, user_id))

    output_file = os.path.join(output_dir, f"siem_logs.{output_format}")

    if output_format == "json":
        with open(output_file, "w") as f:
            json.dump(logs, f, indent=2)
    elif output_format == "csv":
        df = pd.DataFrame(logs)
        df["details"] = df["details"].apply(json.dumps)
        df.to_csv(output_file, index=False)

    print(f"✅ Generated {len(logs)} SIEM logs linked to devices and users.")
    print(f"📁 Saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate SIEM security logs.")
    parser.add_argument("--device_file", default="outputs/linked_devices/linked_devices.json")
    parser.add_argument("--output_dir", default="outputs/siem_logs")
    parser.add_argument("--n_events", type=int, default=1000)
    parser.add_argument("--format", choices=["json", "csv"], default="json")
    args = parser.parse_args()
    main(args.device_file, args.output_dir, args.n_events, args.format)
