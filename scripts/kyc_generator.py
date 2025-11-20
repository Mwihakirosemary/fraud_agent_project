# kyc_generator.py
import json, random, os, string
from faker import Faker
from tqdm import tqdm
import argparse

fake = Faker()

def validate_kyc(record):
    """Basic validation checks."""
    return all([
        record.get("customer_id"),
        record.get("email") and "@" in record["email"],
        record.get("risk_score") >= 0
    ])

def generate_kyc_record():
    """Generate one synthetic KYC profile."""
    risk_score = random.uniform(0, 1)
    return {
        "customer_id": fake.uuid4(),
        "full_name": fake.name(),
        "dob": str(fake.date_of_birth(minimum_age=18, maximum_age=80)),
        "country": fake.country(),
        "email": fake.email(),
        "phone": fake.phone_number(),
        "occupation": fake.job(),
        "account_age_years": random.randint(0, 10),
        "avg_monthly_txn": round(random.uniform(100, 10000), 2),
        "risk_score": round(risk_score, 3),
        "risk_tier": "High" if risk_score > 0.7 else "Medium" if risk_score > 0.4 else "Low"
    }

def main(n_records, output_dir, output_format):
    os.makedirs(output_dir, exist_ok=True)
    data = []

    for _ in tqdm(range(n_records), desc="Generating KYC profiles"):
        rec = generate_kyc_record()
        if validate_kyc(rec):
            data.append(rec)

    path = os.path.join(output_dir, f"kyc_profiles.{output_format}")
    if output_format == "json":
        json.dump(data, open(path, "w"), indent=2)
    elif output_format == "csv":
        import pandas as pd
        pd.DataFrame(data).to_csv(path, index=False)
    print(f"✅ Generated {len(data)} KYC records at {path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=100)
    parser.add_argument("--output_dir", default="outputs/kyc")
    parser.add_argument("--format", choices=["json", "csv"], default="json")
    args = parser.parse_args()
    main(args.n, args.output_dir, args.format)
