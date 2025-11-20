# pattern_generator.py
import os, json, random
from tqdm import tqdm
import argparse

PATTERNS = [
    {
        "name": "Smurfing",
        "indicators": ["Multiple small transfers", "Linked accounts", "Rapid timing"],
        "risk_level": "High",
        "description": "Breaking large transactions into small ones to evade detection."
    },
    {
        "name": "Phishing",
        "indicators": ["Login from new IP", "Multiple failed attempts", "Device mismatch"],
        "risk_level": "Medium",
        "description": "User credentials compromised via fake login pages."
    },
    {
        "name": "Money Mule",
        "indicators": ["New account, large inbound transfers", "Immediate withdrawals"],
        "risk_level": "High",
        "description": "Account used to launder illicit funds."
    },
    {
        "name": "Card Testing",
        "indicators": ["Many small online purchases", "Declined transactions"],
        "risk_level": "Medium",
        "description": "Fraudsters testing stolen cards for validity."
    }
]

def main(n_records, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    data = [random.choice(PATTERNS) for _ in tqdm(range(n_records), desc="Generating fraud patterns")]
    path = os.path.join(output_dir, "fraud_patterns.json")
    json.dump(data, open(path, "w"), indent=2)
    print(f"✅ Generated {n_records} fraud patterns at {path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=50)
    parser.add_argument("--output_dir", default="outputs/patterns")
    args = parser.parse_args()
    main(args.n, args.output_dir)
