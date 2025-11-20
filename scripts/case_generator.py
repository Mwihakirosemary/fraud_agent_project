# case_generator.py
import random, json, os
from tqdm import tqdm
from faker import Faker
import argparse

fake = Faker()

def generate_case():
    """Simulated fraud investigation summary."""
    fraud_types = ["Account Takeover", "Phishing", "Transaction Laundering", "Card Skimming", "Identity Theft"]
    fraud = random.choice(fraud_types)
    return {
        "case_id": f"CASE-{random.randint(1000,9999)}",
        "fraud_type": fraud,
        "description": f"Detected {fraud.lower()} involving unusual device behavior and location anomalies.",
        "investigator": fake.name(),
        "status": random.choice(["Open", "Under Review", "Closed"]),
        "actions_taken": random.choice(["Account frozen", "Customer contacted", "Escalated to compliance"]),
        "timestamp": str(fake.date_time_this_year())
    }

def main(n_records, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    cases = [generate_case() for _ in tqdm(range(n_records), desc="Generating investigation cases")]
    path = os.path.join(output_dir, "investigation_cases.json")
    json.dump(cases, open(path, "w"), indent=2)
    print(f"✅ Generated {n_records} cases at {path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=100)
    parser.add_argument("--output_dir", default="outputs/cases")
    args = parser.parse_args()
    main(args.n, args.output_dir)
