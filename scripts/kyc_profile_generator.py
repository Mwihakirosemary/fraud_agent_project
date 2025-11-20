# kyc_profile_generator.py

import os, json, random
from faker import Faker
from tqdm import tqdm
import pandas as pd
import argparse

fake = Faker()

RISK_LEVELS = ["Low", "Medium", "High"]
ACCOUNTS = ["Savings", "Checking", "Mobile Money", "Credit Card"]
EMPLOYMENTS = ["Engineer", "Teacher", "Doctor", "Trader", "Driver", "Unemployed", "Student"]
COUNTRIES = ["Kenya", "Uganda", "Tanzania", "Nigeria", "South Africa"]

def calculate_risk_score(age, transactions_per_month, device_count):
    """Basic scoring heuristic."""
    score = random.randint(30, 70)
    if age < 25 or age > 60:
        score += 10
    if transactions_per_month > 50:
        score += 10
    if device_count > 3:
        score += 15
    return min(score, 100)

def load_device_user_ids(device_file):
    """Read existing device-user mapping to get user_ids and device counts."""
    with open(device_file, "r") as f:
        data = json.load(f)
    user_device_map = {}
    for d in data:
        for uid in d["linked_users"]:
            user_device_map.setdefault(uid, []).append(d["device_id"])
    return user_device_map

def generate_kyc_profile(user_id, devices):
    """Generate a single user KYC profile."""
    name = fake.name()
    age = random.randint(18, 75)
    country = random.choice(COUNTRIES)
    transactions_per_month = random.randint(5, 200)
    device_count = len(devices)
    risk_score = calculate_risk_score(age, transactions_per_month, device_count)
    risk_level = (
        "High" if risk_score > 75 else
        "Medium" if risk_score > 50 else "Low"
    )

    return {
        "user_id": user_id,
        "full_name": name,
        "age": age,
        "country": country,
        "email": fake.email(),
        "phone_number": fake.phone_number(),
        "account_type": random.choice(ACCOUNTS),
        "employment": random.choice(EMPLOYMENTS),
        "avg_monthly_txn": transactions_per_month,
        "linked_devices": devices,
        "device_count": device_count,
        "risk_score": risk_score,
        "risk_level": risk_level
    }

def main(device_file, output_dir, output_format):
    os.makedirs(output_dir, exist_ok=True)
    user_device_map = load_device_user_ids(device_file)
    kyc_data = []

    for user_id, devices in tqdm(user_device_map.items(), desc="Generating KYC profiles"):
        kyc_data.append(generate_kyc_profile(user_id, devices))

    output_file = os.path.join(output_dir, f"kyc_profiles.{output_format}")

    if output_format == "json":
        with open(output_file, "w") as f:
            json.dump(kyc_data, f, indent=2)
    elif output_format == "csv":
        df = pd.DataFrame(kyc_data)
        df["linked_devices"] = df["linked_devices"].apply(lambda x: ",".join(x))
        df.to_csv(output_file, index=False)

    print(f"✅ Generated {len(kyc_data)} KYC profiles linked to device fingerprints.")
    print(f"📁 Saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic KYC profiles linked to device data.")
    parser.add_argument("--device_file", default="outputs/linked_devices/linked_devices.json")
    parser.add_argument("--output_dir", default="outputs/kyc_profiles")
    parser.add_argument("--format", choices=["json", "csv"], default="json")
    args = parser.parse_args()
    main(args.device_file, args.output_dir, args.format)
