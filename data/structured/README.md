# Data Files

This directory contains the transaction datasets used by the fraud detection agent.

## Required Files

Due to GitHub's file size limits, the actual data files are not included in this repository.

### To set up the data:

1. **Credit Card Fraud Dataset**
   - Download from: [Kaggle Credit Card Fraud Detection](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud)
   - Place as: `data/structured/creditcard.csv`

2. **IEEE Fraud Detection Dataset** (Optional)
   - Download from: [Kaggle IEEE-CIS Fraud Detection](https://www.kaggle.com/c/ieee-fraud-detection)
   - Place in: `data/structured/ieee-fraud-detection/`

### Alternative: Use Sample Data

The agent will work with smaller sample datasets for testing. You can generate sample data using:
```bash
python scripts/generate_sample_data.py
```

## File Structure
```
data/structured/
├── creditcard.csv          # Main transaction dataset (not in Git)
├── ieee-fraud-detection/   # Optional enhanced dataset (not in Git)
└── README.md               # This file
```
