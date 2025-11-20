# device_user_linked_generator.py

import os, json, random, string
from faker import Faker
from tqdm import tqdm
import pandas as pd
import argparse
from datetime import datetime

fake = Faker()

DEVICE_TYPES = ["Android", "iPhone", "Windows", "Mac", "Linux"]
BROWSERS = [
    ("Chrome", ["uBlock", "LastPass", "AdBlock", "Honey"]),
    ("Firefox", ["Ghostery", "NoScript", "Grammarly"]),
    ("Safari", ["Grammarly", "1Password"]),
    ("Edge", ["AdBlock", "LastPass"])
]
NETWORKS = ["Safaricom", "Airtel", "Telkom", "Zuku", "JTL", "Vodacom"]
TIMEZONES = ["Africa/Nairobi", "Europe/London", "Asia/Dubai", "America/New_York"]
RISK_FLAGS = ["vpn_detected", "emulator_detected", "geo_mismatch", "multiple_accounts", "none"]

def generate_device_id():
    return "dev_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

def generate_user_id():
    return "user_" + str(random.randint(1000, 9999))

def generate_fingerprint(device_id, user_ids):
    """Generate one device fingerprint record linked to multiple users."""
    device_type = random.choice(DEVICE_TYPES)
    browser_name, plugins = random.choice(BROWSERS)
    plugin_sample = random.sample(plugins, k=random.randint(1, len(plugins)))
    ip_address = fake.ipv4_public()
    country = fake.country()
    city = fake.city()
    
    risk_sample = random.choices(RISK_FLAGS, k=random.randint(0, 2))
    if "none" in risk_sample:
        risk_sample = []

    return {
        "device_id": device_id,
        "linked_users": user_ids,
        "device_type": device_type,
        "os_version": f"{device_type} {random.randint(9, 15)}" if device_type in ["Android", "iPhone"] else f"{device_type} {random.randint(8, 12)}",
        "browser": f"{browser_name} {random.randint(90, 120)}.0.{random.randint(1000,9999)}.{random.randint(10,99)}",
        "browser_plugins": plugin_sample,
        "screen_resolution": random.choice(["1080x2400", "1440x2960", "1920x1080", "2560x1440"]),
        "timezone": random.choice(TIMEZONES),
        "ip_address": ip_address,
        "geo_location": {"country": country, "city": city},
        "network_carrier": random.choice(NETWORKS),
        "device_reuse_count": len(user_ids),
        "risk_flags": risk_sample,
        "last_seen": datetime.utcnow().isoformat() + "Z"
    }

def validate_record(record):
    required = ["device_id", "linked_users", "device_type", "ip_address", "browser"]
    return all(k in record and record[k] for k in required)

def main(n_users, avg_devices, output_dir, output_format):
    os.makedirs(output_dir, exist_ok=True)
    
    users = [generate_user_id() for _ in range(n_users)]
    device_records = []
    
    # 90% unique devices, 10% shared devices
    total_devices = int(n_users * avg_devices)
    shared_count = int(total_devices * 0.1)
    
    for user_id in tqdm(users, desc="Generating devices per user"):
        num_devices = random.randint(1, avg_devices * 2)
        for _ in range(num_devices):
            device_id = generate_device_id()
            record = generate_fingerprint(device_id, [user_id])
            if validate_record(record):
                device_records.append(record)

    # Inject shared (fraudulent) devices
    for _ in tqdm(range(shared_count), desc="Injecting shared devices"):
        shared_device_id = generate_device_id()
        shared_users = random.sample(users, k=random.randint(2, 4))
        record = generate_fingerprint(shared_device_id, shared_users)
        if validate_record(record):
            device_records.append(record)

    file_path = os.path.join(output_dir, f"linked_devices.{output_format}")
    if output_format == "json":
        with open(file_path, "w") as f:
            json.dump(device_records, f, indent=2)
    elif output_format == "csv":
        df = pd.DataFrame(device_records)
        df["geo_country"] = df["geo_location"].apply(lambda x: x["country"])
        df["geo_city"] = df["geo_location"].apply(lambda x: x["city"])
        df.drop(columns=["geo_location"], inplace=True)
        df["linked_users"] = df["linked_users"].apply(lambda x: ",".join(x))
        df.to_csv(file_path, index=False)

    print(f"✅ Generated {len(device_records)} device fingerprints linked to {n_users} users.")
    print(f"📁 Saved to {file_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate linked device-user fingerprints.")
    parser.add_argument("--n_users", type=int, default=100)
    parser.add_argument("--avg_devices", type=int, default=2)
    parser.add_argument("--output_dir", default="outputs/linked_devices")
    parser.add_argument("--format", choices=["json", "csv"], default="json")
    args = parser.parse_args()
    main(args.n_users, args.avg_devices, args.output_dir, args.format)
